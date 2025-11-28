import os
from pathlib import Path
from pydantic_settings import BaseSettings
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

@lru_cache()
def get_settings() -> Settings:
    return Settings()
