# Face Recognition Attendance System v2.0

Advanced face recognition attendance system built with FastAPI, PostgreSQL, Redis, and OpenCV.

## 🚀 Features

- **FastAPI Backend** - Modern async API with automatic documentation
- **Face Recognition** - Using FaceNet embeddings and OpenCV detection
- **Liveness Detection** - Motion-based anti-spoofing (optional blink detection)
- **JWT Authentication** - Secure API with role-based access control
- **Redis Caching** - Fast embedding retrieval and performance optimization
- **PostgreSQL Database** - Reliable data storage with SQLAlchemy ORM
- **Docker Support** - Complete containerized deployment
- **NGINX Reverse Proxy** - Load balancing and SSL termination
- **REST API** - Well-documented endpoints with Swagger UI

## 📋 Prerequisites

### For Local Development
- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- Webcam (for face capture)

### For Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

## 🛠️ Installation

### Option 1: Local Development

1. **Clone the repository**
```bash
git clone https://github.com/sagun-py0909/face_recog.git
cd face_recog
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL**
```bash
# Create database
createdb attendance_db

# Or using psql
psql -U postgres
CREATE DATABASE attendance_db;
```

5. **Set up Redis**
```bash
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# Linux/Mac:
sudo apt-get install redis-server  # Debian/Ubuntu
brew install redis                  # macOS

# Start Redis
redis-server
```

6. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

7. **Run the application**
```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

8. **Access the API**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

### Option 2: Docker Deployment

1. **Clone the repository**
```bash
git clone https://github.com/sagun-py0909/face_recog.git
cd face_recog
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with production settings
```

3. **Build and run with Docker Compose**
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

4. **Access the application**
- API: http://localhost:80
- Swagger UI: http://localhost:80/api/docs
- Direct API (dev): http://localhost:8000/api/docs

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "admin",
  "email": "admin@example.com",
  "password": "securepassword123"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=securepassword123
```

Returns JWT access token for authenticated requests.

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

### Face Recognition Endpoints

#### Add Person (Admin Only)
```http
POST /api/recognition/add-person
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "John Doe",
  "frames": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  ]
}
```

#### Check-In (Public)
```http
POST /api/recognition/checkin
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

#### Get All People
```http
GET /api/recognition/people
Authorization: Bearer <access_token>
```

#### Delete Person (Admin Only)
```http
DELETE /api/recognition/people/{person_id}
Authorization: Bearer <access_token>
```

#### Get Attendance Records
```http
GET /api/recognition/attendance?limit=50
Authorization: Bearer <access_token>
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://localhost:6379/0

# Face Recognition
SIMILARITY_THRESHOLD=0.7
CONFIDENCE_THRESHOLD=0.5

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 🔒 Security Features

1. **JWT Authentication** - Secure token-based authentication
2. **Password Hashing** - Bcrypt for secure password storage
3. **Role-Based Access** - Admin vs regular user permissions
4. **Rate Limiting** - NGINX-based request throttling
5. **CORS Configuration** - Controlled cross-origin access
6. **Input Validation** - Pydantic schemas for data validation

## 📊 Database Schema

### Tables

**people**
- id (Primary Key)
- name (Unique)
- embedding (Float Array)
- created_at
- updated_at

**attendance**
- id (Primary Key)
- person_id (Foreign Key)
- timestamp
- confidence_score

**users**
- id (Primary Key)
- username (Unique)
- email (Unique)
- hashed_password
- is_active
- is_admin
- created_at

## 🚀 Production Deployment

### 1. Prepare Server
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### 2. Clone and Configure
```bash
git clone https://github.com/sagun-py0909/face_recog.git
cd face_recog

# Set production environment
cp .env.example .env
nano .env  # Edit with production values
```

### 3. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/

# Update nginx.conf with SSL settings
```

### 4. Deploy
```bash
# Build and start
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 5. Set Up Systemd Service (Alternative to Docker)
```bash
# Create service file
sudo nano /etc/systemd/system/face-recog.service
```

```ini
[Unit]
Description=Face Recognition Attendance API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/face_recog
Environment="PATH=/var/www/face_recog/venv/bin"
ExecStart=/var/www/face_recog/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable face-recog
sudo systemctl start face-recog
sudo systemctl status face-recog
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

## 📈 Performance Optimization

1. **Redis Caching** - Embeddings cached for 1 hour
2. **Database Indexing** - Indexes on person_id, timestamp
3. **Connection Pooling** - SQLAlchemy pool management
4. **NGINX Load Balancing** - Distribute requests across instances
5. **Image Optimization** - Resize before processing

## 🔍 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Docker
docker-compose logs -f app

# System service
sudo journalctl -u face-recog -f
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# or
sudo systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d attendance_db
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis
# or
sudo systemctl status redis

# Test connection
redis-cli ping
```

### Face Detection Not Working
- Ensure model files are present: `deploy.prototxt.txt` and `res10_300x300_ssd_iter_140000.caffemodel`
- Check camera permissions
- Verify image quality (good lighting, clear face)

## 📝 Migration from v1.0 (Flask)

The old Flask app (`app.py`) is preserved for backward compatibility. To migrate:

1. **Export existing data**
```sql
COPY people TO '/tmp/people.csv' DELIMITER ',' CSV HEADER;
COPY attendance TO '/tmp/attendance.csv' DELIMITER ',' CSV HEADER;
```

2. **Run new FastAPI app** - Database schema is compatible
3. **Create admin user** via `/api/auth/register`
4. **Test endpoints** with API docs

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- sagun-py0909

## 🙏 Acknowledgments

- OpenCV for face detection
- FaceNet for face embeddings
- FastAPI framework
- PostgreSQL and Redis teams
