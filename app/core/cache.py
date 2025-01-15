from redis import Redis
import json
from typing import Optional, Any
from functools import wraps
import hashlib

class RedisCache:
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0):
        self.redis_client = Redis(host=host, port=port, db=db, decode_responses=True)
        self.default_ttl = 3600  # 1 hour default TTL

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        data = self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        serialized_value = json.dumps(value)
        if ttl:
            self.redis_client.setex(key, ttl, serialized_value)
        else:
            self.redis_client.setex(key, self.default_ttl, serialized_value)

    def delete(self, key: str) -> None:
        """Delete value from cache"""
        self.redis_client.delete(key)

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key based on function arguments"""
        key_parts = [prefix]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

def cache_response(prefix: str, ttl: int = None):
    """Decorator to cache function responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = RedisCache()
            cache_key = cache.generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator