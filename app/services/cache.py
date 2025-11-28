import redis
import json
import numpy as np
from typing import Optional, List, Dict, Any
from app.core.config import get_settings

settings = get_settings()

class RedisCache:
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False,  # We'll handle encoding manually
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print("✓ Redis connected successfully")
        except Exception as e:
            print(f"⚠ Redis connection failed: {e}. Caching disabled.")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def get_embeddings(self) -> Optional[Dict[int, np.ndarray]]:
        """
        Get all face embeddings from cache
        
        Returns:
            Dict mapping person_id to embedding array, or None if not cached
        """
        if not self.is_available():
            return None
        
        try:
            data = self.redis_client.get('face_embeddings')
            if data:
                embeddings_dict = json.loads(data)
                # Convert lists back to numpy arrays
                return {
                    int(pid): np.array(emb, dtype=np.float32)
                    for pid, emb in embeddings_dict.items()
                }
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set_embeddings(self, embeddings: Dict[int, np.ndarray], ttl: int = 3600):
        """
        Cache face embeddings
        
        Args:
            embeddings: Dict mapping person_id to embedding array
            ttl: Time to live in seconds (default: 1 hour)
        """
        if not self.is_available():
            return
        
        try:
            # Convert numpy arrays to lists for JSON serialization
            embeddings_dict = {
                str(pid): emb.tolist()
                for pid, emb in embeddings.items()
            }
            self.redis_client.setex(
                'face_embeddings',
                ttl,
                json.dumps(embeddings_dict)
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def invalidate_embeddings(self):
        """Invalidate embeddings cache"""
        if not self.is_available():
            return
        
        try:
            self.redis_client.delete('face_embeddings')
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def get_person_names(self) -> Optional[Dict[int, str]]:
        """Get cached person names"""
        if not self.is_available():
            return None
        
        try:
            data = self.redis_client.get('person_names')
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set_person_names(self, names: Dict[int, str], ttl: int = 3600):
        """Cache person names"""
        if not self.is_available():
            return
        
        try:
            self.redis_client.setex(
                'person_names',
                ttl,
                json.dumps(names)
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def invalidate_person_names(self):
        """Invalidate person names cache"""
        if not self.is_available():
            return
        
        try:
            self.redis_client.delete('person_names')
        except Exception as e:
            print(f"Redis delete error: {e}")

# Singleton instance
cache = RedisCache()
