# 📂 Folder Structure Guide

## Quick Reference: What Goes Where

---

## 🎯 Main Directories

### **app/** - Application Code
**Everything the application needs to run**

```
app/
├── api/           → API endpoints and routes
├── core/          → Essential components (config, database, auth)
├── services/      → Business logic (face recognition, caching)
├── schemas/       → Data validation models
├── models/        → Database model references
└── utils/         → Helper functions
```

**When to use**: All application code goes here

---

### **deployment/** - Deployment Files  
**Everything needed to deploy the application**

```
deployment/
├── Dockerfile              → Container definition
├── docker-compose.yml      → Multi-container setup
├── nginx.conf              → Web server config
├── deploy.sh               → Linux deployment script
└── deploy.ps1              → Windows deployment script
```

**When to use**: Production deployment, Docker setup

---

### **docs/** - Documentation
**All documentation files**

```
docs/
├── ARCHITECTURE.md         → System architecture explained
├── QUICKSTART.md          → 5-minute setup guide
├── README.md              → Full documentation
└── CHANGELOG.md           → Version history
```

**When to use**: Reading about the system, understanding how it works

---

### **scripts/** - Utility Scripts
**Standalone scripts for maintenance**

```
scripts/
├── init_db.py             → Database initialization
├── migrate.py             → v1→v2 migration
└── test_system.py         → System testing
```

**When to use**: Database setup, testing, migration

---

### **static/** - Frontend Files
**Web interface files**

```
static/
└── index.html             → Web UI
```

**When to use**: Frontend development

---

### **models/** - ML Models
**Machine learning model files**

```
models/
├── deploy.prototxt.txt                      → Face detector config
└── res10_300x300_ssd_iter_140000.caffemodel → Face detector weights
```

**When to use**: Face detection model files

---

### **legacy/** - Old Files
**Version 1.0 files (preserved for reference)**

```
legacy/
├── app_v1.py              → Original Flask app
├── recognize_face.py      → CLI recognition
└── process_dataset.py     → Batch processing
```

**When to use**: Reference only, not for active development

---

### **logs/** - Application Logs
**Auto-generated log files**

```
logs/
└── app_YYYYMMDD.log       → Daily log files
```

**When to use**: Debugging, monitoring

---

### **tests/** - Test Files
**Future test files**

```
tests/
└── (test files go here)
```

**When to use**: Unit tests, integration tests

---

## 📝 Root Files

### **Configuration**
- `.env` → Environment variables (DATABASE_URL, SECRET_KEY, etc.)
- `.env.example` → Template for .env file
- `.gitignore` → Git ignore rules
- `requirements.txt` → Python dependencies

### **Application**
- `main.py` → Application entry point (run this!)
- `Dataset.csv` → Legacy dataset index

### **Documentation**
- `README.md` → Main readme with quick links

---

## 🗺️ File Relationships

### **How Files Connect**

```
main.py
├── Imports from app.core (config, database, auth, logger)
├── Imports from app.api.routes (auth_router, recognition_router)
└── Uses app.services (via routes)

app/api/routes/auth.py
├── Uses app.core.database (User model)
├── Uses app.core.auth (JWT functions)
└── Uses app.schemas (validation)

app/api/routes/recognition.py
├── Uses app.core.database (Person, Attendance)
├── Uses app.services.face_service (face recognition)
├── Uses app.services.cache (Redis)
└── Uses app.schemas (validation)

app/services/face_service.py
├── Uses app.core.config (settings)
└── Uses models/ (ML model files)
```

---

## 🎯 Where Do I Put My Code?

### **Adding a new API endpoint?**
→ `app/api/routes/`

### **Adding business logic?**
→ `app/services/`

### **Adding data validation?**
→ `app/schemas/`

### **Changing configuration?**
→ `.env` file or `app/core/config.py`

### **Adding a database table?**
→ `app/core/database.py`

### **Adding a utility script?**
→ `scripts/`

### **Adding documentation?**
→ `docs/`

### **Changing deployment?**
→ `deployment/`

---

## 📦 Import Patterns

### **From root directory (main.py)**
```python
from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import auth_router, recognition_router
```

### **Within app/ directory**
```python
from app.core.database import get_db, Person
from app.core.auth import get_current_user
from app.services.face_service import face_service
from app.schemas.schemas import PersonResponse
```

---

## 🔄 Workflow Examples

### **Starting the Application**
```
1. Load .env → app/core/config.py
2. Initialize database → app/core/database.py
3. Start FastAPI → main.py
4. Register routes → app/api/routes/
5. Handle requests → app/services/
```

### **Adding a New Person**
```
1. POST /api/recognition/add-person
2. Route handler → app/api/routes/recognition.py
3. Validate data → app/schemas/schemas.py
4. Process face → app/services/face_service.py
5. Save to DB → app/core/database.py
6. Invalidate cache → app/services/cache.py
```

### **Deploying to Production**
```
1. Configure .env
2. Run deployment/deploy.sh (or .ps1)
3. Docker builds from deployment/Dockerfile
4. Docker Compose starts services (deployment/docker-compose.yml)
5. NGINX routes traffic (deployment/nginx.conf)
```

---

## 🎨 Design Principles

### **Separation of Concerns**
- **app/api/** → HTTP layer (routes, requests, responses)
- **app/services/** → Business logic
- **app/core/** → Infrastructure (DB, auth, config)
- **app/schemas/** → Data validation

### **Dependency Flow**
```
Routes → Services → Core
  ↓         ↓         ↓
Schemas ← ← ← ← ← ← ←
```

Routes depend on services  
Services depend on core  
Everything uses schemas for validation

---

## 📊 Directory Sizes (Typical)

```
app/                 ~50-100 KB (Python code)
deployment/          ~20 KB (Config files)
docs/                ~100 KB (Markdown)
models/              ~10 MB (ML models)
static/              ~10 KB (HTML/JS)
logs/                ~1-100 MB (Log files)
legacy/              ~30 KB (Old code)
scripts/             ~20 KB (Utilities)
```

---

## ✅ Best Practices

### **DO**
✅ Keep code in `app/` organized by layer
✅ Put new API routes in `app/api/routes/`
✅ Put business logic in `app/services/`
✅ Use `.env` for configuration
✅ Document in `docs/`

### **DON'T**
❌ Mix business logic with routes
❌ Hardcode configuration
❌ Put code in root directory
❌ Modify `legacy/` files
❌ Commit `.env` to git

---

## 🔍 Quick Find

**Need to find something?**

| Looking for... | Check... |
|---------------|----------|
| Configuration | `.env` or `app/core/config.py` |
| Database models | `app/core/database.py` |
| API endpoints | `app/api/routes/` |
| Face recognition | `app/services/face_service.py` |
| Authentication | `app/core/auth.py` |
| Caching | `app/services/cache.py` |
| Logging | `app/core/logger.py` or `logs/` |
| Deployment | `deployment/` |
| Documentation | `docs/` |
| Tests | `scripts/test_system.py` |

---

## 🎓 Learning Path

**New to the codebase?**

1. **Start**: Read `README.md` (root)
2. **Understand**: Read `docs/ARCHITECTURE.md`
3. **Setup**: Follow `docs/QUICKSTART.md`
4. **Explore**: Look at `app/api/routes/` to see endpoints
5. **Deep Dive**: Trace request flow through the layers

---

This organization keeps the code clean, maintainable, and easy to navigate!
