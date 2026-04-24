import os
from pathlib import Path
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # Face Recognition
    similarity_threshold: float = 0.7
    confidence_threshold: float = 0.5
    
    # Model Paths
    proto_path: str
    model_path: str
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    max_content_length: int = 16777216
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return url.replace("postgresql://", "postgresql+pg8000://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+pg8000://", 1)
    return url


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.database_url = _normalize_database_url(settings.database_url)
    return settings
