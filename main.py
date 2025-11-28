"""
Face Recognition Attendance System v2.0
Main application entry point

This is the entry point for the FastAPI application.
Run with: python main.py or uvicorn main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path

from app.core.config import get_settings
from app.core.database import init_db
from app.core.logger import log_requests, app_logger
from app.api.routes import auth_router, recognition_router

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Face Recognition Attendance System",
    description="Advanced face recognition system with FastAPI, PostgreSQL, and Redis",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
origins = settings.allowed_origins.split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.middleware("http")(log_requests)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )

# Include routers
app.include_router(auth_router)
app.include_router(recognition_router)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    app_logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "face-recognition-api"
    }

@app.get("/")
async def root():
    """Serve the main HTML interface or API info"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return {
        "message": "Face Recognition Attendance API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

@app.get("/docs")
async def redirect_docs():
    """Redirect /docs to /api/docs"""
    return RedirectResponse(url="/api/docs")

@app.get("/redoc")
async def redirect_redoc():
    """Redirect /redoc to /api/redoc"""
    return RedirectResponse(url="/api/redoc")

# Startup event
@app.on_event("startup")
async def startup_event():
    app_logger.info("=" * 60)
    app_logger.info("🚀 Starting Face Recognition Attendance System v2.0")
    app_logger.info("=" * 60)
    
    # Initialize database
    app_logger.info("📊 Initializing database...")
    init_db()
    app_logger.info("✓ Database initialized")
    
    # Test Redis connection
    from app.services.cache import cache
    if cache.is_available():
        app_logger.info("✓ Redis cache connected")
    else:
        app_logger.warning("⚠ Redis cache not available (running without cache)")
    
    app_logger.info("=" * 60)
    app_logger.info(f"📡 Web Interface: http://{settings.host}:{settings.port}/")
    app_logger.info(f"📡 API Documentation: http://{settings.host}:{settings.port}/api/docs")
    app_logger.info(f"🏥 Health Check: http://{settings.host}:{settings.port}/health")
    app_logger.info("=" * 60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    app_logger.info("👋 Shutting down Face Recognition Attendance System")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
