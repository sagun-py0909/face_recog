import os
import base64
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
from sqlalchemy import create_engine, Column, Integer, String, ARRAY, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.future import select
from sklearn.metrics.pairwise import cosine_similarity
from keras_facenet import FaceNet

# --- CONFIG ---
DB_URL = "postgresql://postgres:12345@localhost:5432/attendance_db"  # Update if needed
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_PATH = os.path.join(BASE_DIR, 'deploy.prototxt.txt')
MODEL_PATH = os.path.join(BASE_DIR, 'res10_300x300_ssd_iter_140000.caffemodel')
SIM_THRESHOLD = 0.7
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# --- APP SETUP ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --- DATABASE MODELS ---
class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    embedding = Column(ARRAY(Float))
    attendance = relationship('Attendance', back_populates='person', cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('people.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    person = relationship('Person', back_populates='attendance')

Base.metadata.create_all(engine)

# --- FACE TOOLS ---
detector = cv2.dnn.readNetFromCaffe(PROTO_PATH, MODEL_PATH)
embedder = FaceNet()

def detect_and_crop(img):
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)),
                                 1.0, (300, 300), (104.0, 177.0, 123.0))
    detector.setInput(blob)
    dets = detector.forward()
    for i in range(dets.shape[2]):
        conf = dets[0, 0, i, 2]
        if conf > 0.5:
            box = dets[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            face = img[y1:y2, x1:x2]
            if face.size:
                return cv2.resize(face, (160, 160))
    return None

def load_db():
    with Session() as session:
        rows = session.execute(select(Person.id, Person.name, Person.embedding)).all()
    ids, names, embs = [], [], []
    for pid, name, emb in rows:
        if emb:
            ids.append(pid)
            names.append(name)
            embs.append(np.array(emb, dtype=np.float32))
    return ids, names, embs

# --- ROUTES ---

@app.route('/add', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Name is required'}), 400

        session = Session()
        try:
            # Check if person already exists
            existing = session.query(Person).filter_by(name=name).first()
            if existing:
                return jsonify({'error': f'Person with name "{name}" already exists'}), 400

            embeddings = []
            for k in range(3):
                data = request.form.get(f'frame{k}')
                if not data:
                    print(f"No data for frame{k}")
                    continue
                try:
                    # Handle data URL format
                    if ',' in data:
                        _, encoded = data.split(',', 1)
                    else:
                        encoded = data
                    
                    img_bytes = base64.b64decode(encoded)
                    npimg = np.frombuffer(img_bytes, np.uint8)
                    bgr = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
                    
                    if bgr is None:
                        print(f"Failed to decode image for frame{k}")
                        continue
                        
                    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                    face = detect_and_crop(rgb)
                    
                    if face is not None:
                        print(f"Face detected in frame{k}")
                        face_embedding = embedder.embeddings([face])[0]
                        embeddings.append(face_embedding)
                    else:
                        print(f"No face detected in frame{k}")
                        
                except Exception as e:
                    print(f"Frame {k} decode failed: {e}")
                    continue

            print(f"Total embeddings captured: {len(embeddings)}")
            
            if len(embeddings) == 0:
                return jsonify({'error': 'No faces detected in any frame. Please try again with better lighting and clear face visibility.'}), 400
            
            # Average the embeddings
            avg_emb = np.mean(embeddings, axis=0).tolist()
            
            # Add new person
            new_person = Person(name=name, embedding=avg_emb)
            session.add(new_person)
            session.commit()
            
            print(f"Successfully added person: {name}")
            return jsonify({'success': f'Successfully added {name} with {len(embeddings)} face samples'})
            
        except Exception as e:
            session.rollback()
            print(f"Error adding person: {e}")
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        finally:
            session.close()

    # GET request - show the form
    session = Session()
    try:
        persons = session.query(Person).all()
        return render_template_string('''
        <h2>Add Person (Live Capture)</h2>
        <div id="status"></div>
        <label>Name:</label> <input id="name" placeholder="Enter person's name"/><br><br>
        <video id="video" width="320" height="240" autoplay muted></video><br><br>
        <button id="captureBtn" onclick="startCapture()">Capture 3 Frames & Submit</button>
        <div id="progress"></div>
        
        <h3>Existing Profiles ({{persons|length}} total)</h3>
        <ul>
          {% for p in persons %}
            <li>{{p.name}} (ID: {{p.id}}) 
                <form style="display:inline" onsubmit="deletePerson({{p.id}}); return false;">
                    <button type="submit" onclick="return confirm('Delete {{p.name}}?')">Delete</button>
                </form>
            </li>
          {% endfor %}
        </ul>
        
        <script>
        let count = 0;
        let frames = [];
        let capturing = false;
        const video = document.getElementById('video');
        const status = document.getElementById('status');
        const progress = document.getElementById('progress');
        const captureBtn = document.getElementById('captureBtn');
        
        // Initialize camera
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 }
            } 
        }).then(stream => {
            video.srcObject = stream;
            status.innerHTML = '<span style="color: green;">Camera ready!</span>';
        }).catch(err => {
            status.innerHTML = '<span style="color: red;">Camera access denied: ' + err.message + '</span>';
        });
        
        function startCapture() {
            const name = document.getElementById('name').value.trim();
            if (!name) {
                alert('Please enter a name');
                return;
            }
            
            if (capturing) return;
            
            capturing = true;
            count = 0;
            frames = [];
            captureBtn.disabled = true;
            captureFrame();
        }
        
        function captureFrame() {
            if (count < 3) {
                progress.innerHTML = `Capturing frame ${count + 1}/3...`;
                
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const dataURL = canvas.toDataURL('image/jpeg', 0.8);
                frames.push(dataURL);
                count++;
                
                if (count < 3) {
                    setTimeout(captureFrame, 1500); // Wait 1.5 seconds between captures
                } else {
                    submitFrames();
                }
            }
        }
        
        function submitFrames() {
            progress.innerHTML = 'Processing...';
            
            const formData = new FormData();
            formData.append('name', document.getElementById('name').value.trim());
            
            frames.forEach((frame, i) => {
                formData.append(`frame${i}`, frame);
            });
            
            fetch('/add', { 
                method: 'POST', 
                body: formData 
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    status.innerHTML = '<span style="color: green;">' + data.success + '</span>';
                    document.getElementById('name').value = '';
                    setTimeout(() => location.reload(), 2000);
                } else if (data.error) {
                    status.innerHTML = '<span style="color: red;">Error: ' + data.error + '</span>';
                }
                progress.innerHTML = '';
                captureBtn.disabled = false;
                capturing = false;
            })
            .catch(error => {
                status.innerHTML = '<span style="color: red;">Network error: ' + error.message + '</span>';
                progress.innerHTML = '';
                captureBtn.disabled = false;
                capturing = false;
            });
        }
        
        function deletePerson(pid) {
            fetch(`/delete/${pid}`, { method: 'POST' })
                .then(() => location.reload());
        }
        </script>
        ''', persons=persons)
    finally:
        session.close()

@app.route('/')
def dashboard():
    with Session() as session:
        attendance = session.query(Attendance).order_by(Attendance.timestamp.desc()).limit(50).all()
        total_people = session.query(Person).count()
        return render_template_string('''
        <h2>Face Recognition Attendance System</h2>
        <p><strong>Registered People:</strong> {{total_people}}</p>
        
        <button onclick="checkin()">Check In</button>
        <a href="/add"><button>Add New Person</button></a><br><br>
        
        <div id="checkin-status"></div>
        
        <h3>Recent Attendance (Last 50 entries)</h3>
        <ul id="log">
          {% for a in attendance %}
            <li><strong>{{a.person.name}}</strong> - {{a.timestamp.strftime('%Y-%m-%d %H:%M:%S')}}</li>
          {% endfor %}
        </ul>
        
        <script>
        function checkin() {
            const status = document.getElementById('checkin-status');
            status.innerHTML = 'Starting camera...';
            
            navigator.mediaDevices.getUserMedia({
                video: { 
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            }).then(stream => {
                status.innerHTML = 'Look at the camera... capturing in 3 seconds';
                const video = document.createElement('video');
                video.srcObject = stream;
                video.play();
                
                setTimeout(() => {
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    video.pause();
                    stream.getTracks().forEach(track => track.stop());
                    
                    status.innerHTML = 'Processing...';
                    
                    canvas.toBlob(blob => {
                        const formData = new FormData();
                        formData.append('frame', blob, 'frame.jpg');
                        
                        fetch('/checkin', { method: 'POST', body: formData })
                            .then(response => response.json())
                            .then(data => {
                                status.innerHTML = '<strong>' + data.message + '</strong>';
                                if (data.message.includes('Checked in')) {
                                    setTimeout(() => location.reload(), 2000);
                                }
                            })
                            .catch(error => {
                                status.innerHTML = 'Error: ' + error.message;
                            });
                    }, 'image/jpeg', 0.8);
                }, 3000);
            }).catch(err => {
                status.innerHTML = 'Camera error: ' + err.message;
            });
        }
        </script>
        ''', attendance=attendance, total_people=total_people)

@app.route('/checkin', methods=['POST'])
def checkin():
    file = request.files.get('frame')
    if not file:
        return jsonify({'message': 'No frame provided'}), 400

    try:
        npimg = np.frombuffer(file.read(), np.uint8)
        bgr = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        if bgr is None:
            return jsonify({'message': 'Invalid image format'}), 400
            
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        face = detect_and_crop(rgb)
        
        if face is None:
            return jsonify({'message': 'No face detected. Please try again with better lighting.'}), 200

        emb = embedder.embeddings([face])[0]
        ids, names, embs = load_db()
        
        if not embs:
            return jsonify({'message': 'No registered faces found. Please add people first.'}), 200

        sims = cosine_similarity([emb], embs)[0]
        idx = int(np.argmax(sims))
        score = sims[idx]
        
        print(f"Best match: {names[idx]} with similarity: {score:.3f}")
        
        if score < SIM_THRESHOLD:
            return jsonify({'message': f'No match found (best: {names[idx]} - {score:.2f}). Please register first.'}), 200

        with Session() as session:
            session.add(Attendance(person_id=ids[idx]))
            session.commit()
            
        return jsonify({'message': f'✓ Checked in: {names[idx]} (confidence: {score:.2f})'})
        
    except Exception as e:
        print(f"Checkin error: {e}")
        return jsonify({'message': f'Processing error: {str(e)}'}), 500

@app.route('/delete/<int:pid>', methods=['POST'])
def delete_person(pid):
    with Session() as session:
        person = session.get(Person, pid)
        if person:
            session.delete(person)
            session.commit()
            print(f"Deleted person: {person.name}")
    return redirect(url_for('add_person'))

if __name__ == '__main__':
    print("Starting Face Recognition Attendance System...")
    print(f"Database URL: {DB_URL}")
    print("Make sure your PostgreSQL database is running and accessible.")
    app.run(host='0.0.0.0', port=5000, debug=True)