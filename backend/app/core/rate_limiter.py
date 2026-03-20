"""
Shared rate limiter instance.

All routers MUST import `limiter` from here to ensure a single Limiter
is used across the entire application. The same instance is also attached
to `app.state.limiter` in main.py.

Using per-router limiter instances is a common pitfall — they create
INDEPENDENT counters that SlowAPI's middleware ignores.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Single global limiter (IP-based by default)
limiter = Limiter(key_func=get_remote_address)
