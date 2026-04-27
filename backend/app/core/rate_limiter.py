"""
Shared rate limiter instance.

All routers MUST import `limiter` from here to ensure a single Limiter
is used across the entire application. The same instance is also attached
to `app.state.limiter` in main.py.

Using per-router limiter instances is a common pitfall — they create
INDEPENDENT counters that SlowAPI's middleware ignores.

In production with multiple Gunicorn workers, uses Redis for shared state.
In development (no Redis), falls back to in-memory storage.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.storage import RedisStorage, InMemoryStorage

# Import settings for environment and Redis URL
from app.config import settings

# Determine storage backend
# In production with Redis URL configured -> use Redis (shared across workers)
# In development or without Redis -> use in-memory (not shared)
redis_url = settings.REDIS_URL or os.getenv("REDIS_URL")

if redis_url and settings.APP_ENV == "production":
    storage = RedisStorage(redis_url)
else:
    storage = InMemoryStorage()

# Single global limiter (IP-based by default)
limiter = Limiter(key_func=get_remote_address, storage=storage)
