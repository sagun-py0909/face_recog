import os
import numpy as np
import cv2
from keras_facenet import FaceNet
from sqlalchemy import create_engine, Column, Integer, String, ARRAY, Float, MetaData, Table
from sqlalchemy.orm import sessionmaker

# --- CONFIG ---
THIS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(THIS_DIR, "Original Images")  # Corrected path
DB_URL = "postgresql://postgres:12345@localhost:5432/attendance_db"
PROTO_PATH = os.path.join(THIS_DIR, "deploy.prototxt.txt")
MODEL_PATH = os.path.join(THIS_DIR, "res10_300x300_ssd_iter_140000.caffemodel")

# --- Init ---
embedder = FaceNet()
detector = cv2.dnn.readNetFromCaffe(PROTO_PATH, MODEL_PATH)

# --- Database Setup ---
engine = create_engine(DB_URL)
metadata = MetaData()
people = Table(
    'people', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, unique=True),
    Column('embedding', ARRAY(Float), nullable=False)
)
metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- Helpers ---
def detect_and_crop(img):
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)),
                                 1.0, (300, 300),
                                 (104.0, 177.0, 123.0))
    detector.setInput(blob)
    detections = detector.forward()
    for i in range(detections.shape[2]):
        conf = detections[0, 0, i, 2]
        if conf > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            face = img[y1:y2, x1:x2]
            if face.size == 0:
                continue
            return cv2.resize(face, (160, 160))
    return None

# --- Process Dataset ---
for person in os.listdir(DATA_DIR):
    person_folder = os.path.join(DATA_DIR, person)
    if not os.path.isdir(person_folder):
        continue

    embs = []
    for img_name in os.listdir(person_folder):
        img_path = os.path.join(person_folder, img_name)
        img = cv2.imread(img_path)
        if img is None:
            print(f"[!] Could not read image: {img_path}")
            continue

        face = detect_and_crop(img)
        if face is None:
            print(f"[!] No face detected in {img_path}")
            continue

        emb = embedder.embeddings([face])[0]
        embs.append(emb)

    if not embs:
        print(f"[!] No embeddings found for {person}")
        continue

    avg_emb = np.mean(embs, axis=0).tolist()
    session.execute(
        people.insert().values(name=person.strip(), embedding=avg_emb)
    )
    print(f"[+] Stored {len(embs)} embeddings for '{person}'")

session.commit()
session.close()
print("✅ Dataset processing complete.")
