# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
```powershell
# Check Python version (need 3.10+)
python --version

# Check PostgreSQL (need 15+)
psql --version

# Check Redis
redis-cli --version
```

### Step 1: Install Dependencies
```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Setup Database
```powershell
# Start PostgreSQL (if not running)
# Start Redis (if not running)

# Create database
psql -U postgres
CREATE DATABASE attendance_db;
\q

# Initialize database and create admin user
python init_db.py init
```

This creates:
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

**⚠️ IMPORTANT: Change password after first login!**

### Step 3: Start the Application
```powershell
# Development mode
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Access the Application
Open your browser:
- **Web Interface**: http://localhost:8000/
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### Step 5: First Login & Registration

1. **Login as Admin**
   - Go to http://localhost:8000/
   - Click "Login" tab
   - Username: `admin`
   - Password: `admin123`

2. **Register Your First Person**
   - Click "Register" tab
   - Enter name
   - Click "Start Camera"
   - Click "Capture 3 Frames & Register"
   - Wait for processing

3. **Test Check-In**
   - Click "Check-In" tab
   - Click "Start Camera"
   - Click "Capture & Check-In"

## 🐳 Docker Quick Start

### Even Faster with Docker
```powershell
# Make sure Docker Desktop is running

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application
# Web Interface: http://localhost/
# API Docs: http://localhost/api/docs
```

### Create Admin User (Docker)
```powershell
# Enter the app container
docker-compose exec app python init_db.py admin
```

## 📱 Using the API

### 1. Login and Get Token
```powershell
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Add Person (with token)
```powershell
curl -X POST http://localhost:8000/api/recognition/add-person `
  -H "Authorization: Bearer YOUR_TOKEN_HERE" `
  -H "Content-Type: application/json" `
  -d '{"name":"John Doe","frames":["base64_image1","base64_image2","base64_image3"]}'
```

### 3. Check-In (no auth required)
```powershell
curl -X POST http://localhost:8000/api/recognition/checkin `
  -H "Content-Type: application/json" `
  -d '{"image":"base64_encoded_image"}'
```

### 4. Get Attendance Records
```powershell
curl -X GET http://localhost:8000/api/recognition/attendance?limit=50 `
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔧 Common Issues

### Database Connection Failed
```powershell
# Check PostgreSQL is running
# Windows: Check Services
# Or start manually
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# Update .env with correct credentials
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/attendance_db
```

### Redis Connection Failed
```powershell
# Start Redis
redis-server

# Or continue without Redis (caching disabled)
# App will work but slower
```

### Camera Not Working
- Check browser permissions (allow camera access)
- Use HTTPS in production (required for camera)
- Try different browser (Chrome/Edge recommended)

### Face Not Detected
- Ensure good lighting
- Face should be clearly visible
- Look directly at camera
- Remove glasses if detection fails

## 🎯 Next Steps

1. **Change admin password**
   - Use API: `PATCH /api/auth/me`

2. **Add more users**
   - Register team members via web interface

3. **Set up SSL for production**
   - Follow deployment guide in README.md

4. **Configure liveness detection**
   - Download shape predictor model
   - Update liveness.py settings

5. **Customize settings**
   - Edit .env file
   - Adjust similarity threshold
   - Configure CORS origins

## 📚 Additional Resources

- **Full Documentation**: README.md
- **API Reference**: http://localhost:8000/api/docs
- **Database Schema**: See database.py
- **Configuration**: See config.py and .env

## 💡 Pro Tips

- Use Docker for easiest setup
- Keep similarity threshold at 0.7 (good balance)
- Capture faces in good lighting
- Use 3+ frames for registration
- Monitor logs: `docker-compose logs -f app`
- Backup database regularly

## 🆘 Getting Help

1. Check logs: `logs/app_YYYYMMDD.log`
2. Check health: http://localhost:8000/health
3. Review API docs: http://localhost:8000/api/docs
4. Open GitHub issue for bugs

---

**Happy Face Recognition! 🎭**
