# 🎭 Face Recognition Attendance System v2.0

Production-ready face recognition system built with FastAPI, PostgreSQL, Redis, and OpenCV.

---

## ✨ Documentation Hub

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[⚡ QUICKSTART.md](docs/QUICKSTART.md)** | Get running in 5 minutes | **Start here!** |
| **[🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Complete system architecture (15KB) | Understanding how it works |
| **[📂 FOLDER_STRUCTURE.md](docs/FOLDER_STRUCTURE.md)** | File organization explained | Finding your way around |
| **[📖 README.md](docs/README.md)** | Full documentation | In-depth reference |
| **[📝 CHANGELOG.md](docs/CHANGELOG.md)** | Version history | What changed |

---

## 🚀 Quick Start

### **Development** (5 minutes)
```powershell
pip install -r requirements.txt
python scripts/init_db.py init
python main.py
```
Access: http://localhost:8000/

### **Production** (Docker)
```powershell
cd deployment
docker-compose up -d
```
Access: http://localhost/

**Default Login**: `admin` / `admin123` ⚠️ *Change immediately!*

---

## 📁 Organized Structure

```
app/                    # Main application
├── api/routes/        # API endpoints
├── core/              # Config, DB, auth, logging
├── services/          # Face recognition, caching
└── schemas/           # Data validation

deployment/            # Docker & deployment files
docs/                  # All documentation
scripts/               # Utility scripts
static/                # Web interface
models/                # ML model files
```

**📖 See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for complete structure explanation**

---

## 🎯 Features

- ✅ **FastAPI** - Modern async framework with auto-docs
- ✅ **High Accuracy** - FaceNet embeddings (99%+)
- ✅ **Secure** - JWT auth, bcrypt, rate limiting
- ✅ **Fast** - Redis caching (3x faster)
- ✅ **Docker** - Complete containerization
- ✅ **Liveness Detection** - Anti-spoofing
- ✅ **Admin Panel** - Web interface

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | 🏗️ System architecture & how components work |
| **[QUICKSTART.md](docs/QUICKSTART.md)** | ⚡ 5-minute setup guide |
| **[README.md](docs/README.md)** | 📖 Complete documentation |
| **[CHANGELOG.md](docs/CHANGELOG.md)** | 📝 Version history |

---

## 🔧 Key Commands

```powershell
# Start application
python main.py

# Initialize database
python scripts/init_db.py init

# Run tests
python scripts/test_system.py

# Docker deployment
cd deployment && docker-compose up -d

# View logs
Get-Content logs/app_*.log -Tail 50
```

---

## 🛠️ Tech Stack

**Backend**: FastAPI, Python 3.10+  
**Database**: PostgreSQL 15+  
**Cache**: Redis 7+  
**Face Detection**: OpenCV DNN  
**Face Recognition**: FaceNet  
**Auth**: JWT  
**Deployment**: Docker, NGINX  

---

## 📊 How It Works

### Face Recognition Flow
```
Camera → Detect Face → Extract Embedding → Compare → Match → Record
```

### System Architecture
```
User → NGINX → FastAPI → Redis/PostgreSQL → Response
```

**For detailed explanation**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🧪 Testing

```powershell
python scripts/test_system.py    # Run all tests
curl http://localhost:8000/health # Health check
```

---

## 📞 Need Help?

1. **Quick Setup**: [QUICKSTART.md](docs/QUICKSTART.md)
2. **How It Works**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. **API Reference**: http://localhost:8000/api/docs
4. **Full Docs**: [docs/README.md](docs/README.md)

---

**⭐ Star this repo if you find it useful!**

MIT License | sagun-py0909
