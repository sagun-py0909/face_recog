import os
import sys
import cv2
import numpy as np
import psycopg2
from sklearn.metrics.pairwise import cosine_similarity
from keras_facenet import FaceNet

# ——— CONFIG ———
DB_URL       = "postgresql://postgres:12345@localhost:5432/attendance_db"  # ← update password if needed
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
PROTO_PATH   = os.path.join(BASE_DIR, "deploy.prototxt.txt")
MODEL_PATH   = os.path.join(BASE_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
SIM_THRESHOLD = 0.7

# ——— Initialize models ———
detector = cv2.dnn.readNetFromCaffe(PROTO_PATH, MODEL_PATH)
embedder = FaceNet()

def detect_and_crop(img):
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)),
                                 1.0, (300, 300),
                                 (104.0, 177.0, 123.0))
    detector.setInput(blob)
    dets = detector.forward()
    for i in range(dets.shape[2]):
        conf = dets[0, 0, i, 2]
        if conf > 0.5:
            box = dets[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            face = img[y1:y2, x1:x2]
            if face.size == 0:
                continue
            return cv2.resize(face, (160, 160))
    return None

def load_db_embeddings():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, name, embedding FROM people")
    rows = cur.fetchall()
    conn.close()
    ids, names, embs = [], [], []
    for pid, name, emb in rows:
        ids.append(pid)
        names.append(name)
        embs.append(np.array(emb, dtype=np.float32))
    return ids, names, embs

def recognize(image_path):
    # 1) Load image (BGR), convert to RGB
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        print(f"❌ Could not read image: {image_path}")
        return
    # note: FaceNet embedder expects RGB
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # 2) Detect & crop face
    face = detect_and_crop(img_rgb)
    if face is None:
        print("❌ No face detected in the image.")
        return

    # 3) Get embedding
    emb = embedder.embeddings([face])[0]

    # 4) Load DB embeddings and compare
    ids, names, db_embs = load_db_embeddings()
    if not db_embs:
        print("❌ No embeddings in database.")
        return

    sims = cosine_similarity([emb], db_embs)[0]
    best_idx = int(np.argmax(sims))
    best_score = sims[best_idx]

    print(f"🔍 Best similarity: {best_score:.3f}")
    if best_score >= SIM_THRESHOLD:
        print(f"✅ Identified as: {names[best_idx]}")
    else:
        print("❌ No confident match (below threshold).")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python recognize_face.py <image_path>")
    else:
        recognize(sys.argv[1])
