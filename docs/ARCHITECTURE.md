# 🏗️ Architecture Documentation

## Face Recognition Attendance System v2.0

This document explains the complete architecture, folder structure, and how all components work together.

---

## 📁 Project Structure

```
face_recog/
├── 📂 app/                          # Main application package
│   ├── 📂 api/                      # API layer
│   │   ├── 📂 routes/              # API route handlers
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── recognition.py     # Face recognition endpoints
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── 📂 core/                    # Core functionality
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database models & session
│   │   ├── auth.py                # JWT authentication logic
│   │   ├── logger.py              # Logging configuration
│   │   └── __init__.py
│   │
│   ├── 📂 models/                  # Database models (references)
│   │   └── __init__.py
│   │
│   ├── 📂 schemas/                 # Pydantic schemas
│   │   ├── schemas.py             # Request/response models
│   │   └── __init__.py
│   │
│   ├── 📂 services/                # Business logic
│   │   ├── face_service.py        # Face detection & recognition
│   │   ├── cache.py               # Redis caching service
│   │   ├── liveness.py            # Liveness detection
│   │   └── __init__.py
│   │
│   ├── 📂 utils/                   # Utility functions
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── 📂 deployment/                   # Deployment configurations
│   ├── Dockerfile                  # Container definition
│   ├── docker-compose.yml          # Multi-container setup
│   ├── nginx.conf                  # NGINX configuration
│   ├── deploy.sh                   # Linux deployment script
│   └── deploy.ps1                  # Windows deployment script
│
├── 📂 docs/                        # Documentation
│   ├── README.md                   # Main documentation
│   ├── QUICKSTART.md              # Quick start guide
│   ├── UPGRADE_SUMMARY.md         # Upgrade details
│   └── CHANGELOG.md               # Version history
│
├── 📂 scripts/                     # Utility scripts
│   ├── init_db.py                 # Database initialization
│   ├── migrate.py                 # Migration tool
│   └── test_system.py             # System testing
│
├── 📂 static/                      # Frontend files
│   └── index.html                 # Web interface
│
├── 📂 models/                      # ML model files
│   ├── deploy.prototxt.txt        # Face detector config
│   └── res10_300x300_ssd_iter_140000.caffemodel  # Face detector weights
│
├── 📂 legacy/                      # Old v1.0 files
│   ├── app_v1.py                  # Original Flask app
│   ├── recognize_face.py          # CLI recognition
│   └── process_dataset.py         # Batch processing
│
├── 📂 logs/                        # Application logs (auto-created)
│   └── app_YYYYMMDD.log
│
├── 📂 tests/                       # Test files
│
├── 📂 Faces/                       # Processed faces (legacy)
├── 📂 Original Images/             # Training dataset (legacy)
│
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
└── Dataset.csv                    # Legacy dataset index

```

---

## 🔄 Request Flow

### 1. **Authentication Flow**

```
User Request
    ↓
[main.py] → FastAPI App
    ↓
[Middleware] → CORS + Logging
    ↓
[app/api/routes/auth.py] → Login/Register endpoint
    ↓
[app/core/auth.py] → Password verification + JWT creation
    ↓
[app/core/database.py] → User table query
    ↓
[PostgreSQL] → User data
    ↓
Return: JWT Token
```

### 2. **Face Recognition Flow**

```
Camera Capture (Frontend)
    ↓
Base64 Image → POST /api/recognition/checkin
    ↓
[app/api/routes/recognition.py] → Decode image
    ↓
[app/services/face_service.py] → Detect face
    ↓
[OpenCV DNN] → Face bounding box
    ↓
[FaceNet] → Generate embedding (512-dim vector)
    ↓
[app/services/cache.py] → Check Redis cache
    ↓
[If cached] → Compare embeddings
[If not] → Query database → Cache results
    ↓
[Cosine Similarity] → Find best match
    ↓
[app/core/database.py] → Save attendance record
    ↓
Return: Recognition result
```

### 3. **Add Person Flow**

```
Admin Login → JWT Token
    ↓
Camera captures 3 frames → Base64 images
    ↓
POST /api/recognition/add-person (with token)
    ↓
[Auth Middleware] → Verify admin role
    ↓
[app/api/routes/recognition.py] → Process frames
    ↓
[app/services/face_service.py] → Extract embeddings
    ↓
Average embeddings → Single 512-dim vector
    ↓
[app/core/database.py] → Insert into people table
    ↓
[app/services/cache.py] → Invalidate cache
    ↓
Return: Success message
```

---

## 🧩 Component Details

### **1. Main Application (main.py)**

**Purpose**: Application entry point and configuration

**Key Functions**:
- Initialize FastAPI app
- Configure middleware (CORS, logging)
- Mount static files
- Register API routes
- Handle startup/shutdown events

**Code Flow**:
```python
main.py
├── Import settings and components
├── Create FastAPI instance
├── Add middleware (CORS, logging)
├── Include routers (auth, recognition)
├── Mount static files
└── Define startup/shutdown hooks
```

---

### **2. Core Layer (app/core/)**

#### **config.py**
- Loads environment variables from `.env`
- Uses Pydantic for type-safe settings
- Provides `get_settings()` function (cached)

```python
Settings:
├── database_url         # PostgreSQL connection
├── redis_url           # Redis connection
├── similarity_threshold # Face matching threshold (0.7)
├── secret_key          # JWT signing key
└── ... (other settings)
```

#### **database.py**
- SQLAlchemy ORM models
- Database session management
- Three main tables:
  - `Person`: Stores faces and embeddings
  - `Attendance`: Check-in records
  - `User`: Authentication data

```python
Models:
├── Person
│   ├── id, name, embedding
│   └── created_at, updated_at
├── Attendance
│   ├── id, person_id, timestamp
│   └── confidence_score
└── User
    ├── id, username, email
    ├── hashed_password
    └── is_active, is_admin
```

#### **auth.py**
- JWT token creation/validation
- Password hashing (bcrypt)
- User authentication
- Dependency injection for protected routes

```python
Functions:
├── create_access_token()      # Generate JWT
├── verify_password()          # Check password
├── get_current_user()         # Extract user from token
├── get_current_active_user()  # Ensure user is active
└── get_current_admin_user()   # Ensure admin role
```

#### **logger.py**
- Structured logging setup
- File rotation (10MB, 5 backups)
- Console + file output
- Request/response logging middleware

---

### **3. API Layer (app/api/routes/)**

#### **auth.py**
**Endpoints**:
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user info

**Auth Flow**:
```
POST /api/auth/login
├── Validate username/password
├── Check user exists and is active
├── Generate JWT token (30 min expiry)
└── Return token
```

#### **recognition.py**
**Endpoints**:
- `POST /api/recognition/add-person` (Admin) - Register face
- `POST /api/recognition/checkin` (Public) - Face check-in
- `GET /api/recognition/people` (Auth) - List people
- `GET /api/recognition/attendance` (Auth) - List records
- `DELETE /api/recognition/people/{id}` (Admin) - Delete person

**Recognition Flow**:
```
POST /api/recognition/checkin
├── Decode base64 image
├── Detect face (OpenCV DNN)
├── Generate embedding (FaceNet)
├── Load cached embeddings (Redis)
├── Calculate similarities (Cosine)
├── Find best match (threshold 0.7)
├── Save attendance record
└── Return result
```

---

### **4. Services Layer (app/services/)**

#### **face_service.py**
**Core Face Recognition Logic**

```python
FaceRecognitionService:
├── detector (OpenCV DNN)
│   ├── Load: deploy.prototxt + .caffemodel
│   └── Detect faces with 50% confidence
│
├── embedder (FaceNet)
│   └── Generate 512-dim face embeddings
│
└── Methods:
    ├── detect_and_crop()      # Find face in image
    ├── get_embedding()        # Generate embedding
    ├── process_image()        # Full pipeline
    ├── calculate_similarity() # Cosine similarity
    └── find_best_match()      # Match against database
```

**Technical Details**:
- Input: RGB image (any size)
- Face Detection: SSD ResNet (300x300)
- Face Extraction: Resized to 160x160
- Embedding: FaceNet (512 dimensions)
- Similarity: Cosine similarity (0-1 range)
- Threshold: 0.7 (configurable)

#### **cache.py**
**Redis Caching Service**

```python
RedisCache:
├── Connection pooling
├── Automatic serialization (JSON)
├── TTL: 1 hour (3600s)
│
└── Methods:
    ├── get_embeddings()        # Get all face embeddings
    ├── set_embeddings()        # Cache embeddings
    ├── invalidate_embeddings() # Clear on update
    ├── get_person_names()      # Get cached names
    └── set_person_names()      # Cache names
```

**Cache Strategy**:
- **What**: Face embeddings + person names
- **When**: First database query
- **TTL**: 1 hour
- **Invalidation**: On person add/delete
- **Fallback**: Works without Redis

#### **liveness.py**
**Anti-Spoofing Detection**

```python
LivenessDetector:
├── Motion Detection (default)
│   ├── Compares frame differences
│   └── Threshold: 5.0 pixels change
│
└── Blink Detection (optional)
    ├── Requires: dlib shape predictor
    ├── Eye Aspect Ratio (EAR) calculation
    └── Detects eye closure patterns
```

---

### **5. Schemas Layer (app/schemas/)**

**Pydantic Models for Validation**

```python
Request Schemas:
├── AddPersonRequest
│   ├── name: str
│   └── frames: List[str] (base64 images)
│
├── CheckinRequest
│   └── image: str (base64)
│
└── UserCreate
    ├── username: str (3-50 chars)
    ├── email: EmailStr
    └── password: str (min 6 chars)

Response Schemas:
├── PersonResponse
├── AttendanceResponse
├── UserResponse
└── Token
```

---

## 🔐 Security Architecture

### **1. Authentication**
```
JWT Token Structure:
{
  "sub": "username",
  "exp": 1732896000,  # Expiration timestamp
  "iat": 1732894200   # Issued at
}
```

**Security Features**:
- Tokens expire after 30 minutes
- Password hashing with bcrypt (10 rounds)
- Admin vs user role separation
- Protected routes with dependencies

### **2. API Security**
- CORS configuration (whitelisted origins)
- Rate limiting (NGINX)
  - API: 10 req/sec
  - Check-in: 2 req/sec
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)

### **3. Data Security**
- Environment variables for secrets
- No hardcoded credentials
- Database connection pooling
- HTTPS ready (SSL/TLS support)

---

## 💾 Database Schema

```sql
-- People table
CREATE TABLE people (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    embedding FLOAT[] NOT NULL,  -- 512-dim vector
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Attendance table
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    person_id INTEGER REFERENCES people(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    confidence_score FLOAT
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes**:
- `people.name` - Fast name lookup
- `attendance.person_id` - Join optimization
- `attendance.timestamp` - Time-range queries
- `users.username` - Login lookup

---

## 🚀 Deployment Architecture

### **Development**
```
localhost:8000
├── FastAPI (uvicorn)
├── PostgreSQL (localhost:5432)
└── Redis (localhost:6379)
```

### **Production (Docker)**
```
Internet → Port 80/443
    ↓
[NGINX Container]
├── Reverse proxy
├── SSL termination
├── Rate limiting
└── Static files
    ↓
[FastAPI Container]
├── Application logic
└── Port 8000 (internal)
    ↓
[PostgreSQL Container]
└── Port 5432 (internal)
    ↓
[Redis Container]
└── Port 6379 (internal)
```

**Docker Compose Services**:
1. **nginx** - Web server (80, 443)
2. **app** - FastAPI application (8000)
3. **postgres** - Database (5432)
4. **redis** - Cache (6379)

---

## 📊 Performance Optimization

### **1. Caching Strategy**
- **Redis**: 80% faster embedding lookup
- **TTL**: 1 hour (balance freshness/performance)
- **Cache Keys**:
  - `face_embeddings` - All person embeddings
  - `person_names` - ID → name mapping

### **2. Database Optimization**
- Connection pooling (SQLAlchemy)
- Indexes on frequently queried columns
- Batch operations where possible
- Prepared statements (SQL injection prevention)

### **3. API Optimization**
- Async endpoints (FastAPI)
- Non-blocking I/O
- Compressed responses
- Static file caching (NGINX)

---

## 📝 Configuration Management

### **.env File Structure**
```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://host:port/0

# Face Recognition
SIMILARITY_THRESHOLD=0.7        # Match threshold
CONFIDENCE_THRESHOLD=0.5        # Detection threshold

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

**Environment-Specific**:
- Development: `.env` (DEBUG=True)
- Production: `.env` (DEBUG=False, strong SECRET_KEY)

---

## 🧪 Testing

```powershell
# Run system tests
python scripts/test_system.py

# Check health
curl http://localhost:8000/health

# View logs
Get-Content logs/app_YYYYMMDD.log -Tail 50
```

---

## 📈 Monitoring

### **Logs**
- Location: `logs/app_YYYYMMDD.log`
- Rotation: 10MB, 5 backups
- Format: Timestamp - Level - Message

### **Health Check**
```
GET /health
Response:
{
  "status": "healthy",
  "version": "2.0.0",
  "service": "face-recognition-api"
}
```

### **Metrics to Monitor**
- Response times
- Cache hit rate
- Database connection pool
- Error rates
- Active users

---

## 🎯 Best Practices

### **Code Organization**
✅ Separation of concerns (layers)
✅ Dependency injection
✅ Type hints throughout
✅ Comprehensive docstrings
✅ Consistent naming conventions

### **Security**
✅ Environment variables for secrets
✅ Input validation
✅ Authentication on sensitive endpoints
✅ SQL injection prevention
✅ XSS protection

### **Performance**
✅ Caching frequently accessed data
✅ Async operations
✅ Connection pooling
✅ Proper indexing
✅ Lazy loading

---

This architecture provides a solid foundation for a production-ready face recognition system with room for scaling and enhancement.
