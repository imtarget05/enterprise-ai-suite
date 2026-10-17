"""
Redis Client for Project 1 (Enterprise Copilot) with In-Memory Mock Fallback.
"""

from typing import Optional
from apps.enterprise_copilot.backend.config import settings


class InMemoryCache:
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._store[key] = value
        return True

    def incrby(self, key: str, amount: int = 1) -> int:
        val = int(self._store.get(key, 0)) + amount
        self._store[key] = str(val)
        return val

    def expire(self, key: str, seconds: int) -> bool:
        return True

    def delete(self, key: str) -> bool:
        return bool(self._store.pop(key, None))


class RedisWrapper:
    def __init__(self):
        self._client = None
        self._fallback = InMemoryCache()
        if settings.REDIS_ENABLED:
            try:
                import redis
                self._client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def get(self, key: str) -> Optional[str]:
        if self._client:
            try:
                return self._client.get(key)
            except Exception:
                pass
        return self._fallback.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self._client:
            try:
                return bool(self._client.set(key, value, ex=ex))
            except Exception:
                pass
        return self._fallback.set(key, value, ex=ex)

    def incrby(self, key: str, amount: int = 1) -> int:
        if self._client:
            try:
                return self._client.incrby(key, amount)
            except Exception:
                pass
        return self._fallback.incrby(key, amount)

    def expire(self, key: str, seconds: int) -> bool:
        if self._client:
            try:
                return bool(self._client.expire(key, seconds))
            except Exception:
                pass
        return self._fallback.expire(key, seconds)


redis_client = RedisWrapper()
