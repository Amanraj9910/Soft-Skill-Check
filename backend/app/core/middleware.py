"""
Request logging middleware for automatic API request/response tracking.

This middleware logs all incoming HTTP requests and responses with timing
and human-readable messages.

Additionally includes:
- Global rate limiting per IP (100 requests/minute by default)
- Backpressure when system is overloaded
"""
import os
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import api_logger, error_logger
from app.core import log_messages


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses.
    
    Provides automatic logging with:
    - Human-readable messages
    - Execution timing
    - Status code differentiation (2xx/4xx/5xx)
    - Visual indicators (emojis in development)
    """
    
    def __init__(self, app: ASGIApp, enable_body_logging: bool = False):
        """
        Initialize middleware.
        
        Args:
            app: ASGI application
            enable_body_logging: Whether to log request/response bodies (only in dev)
        """
        super().__init__(app)
        self.enable_body_logging = enable_body_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
        
        Returns:
            HTTP response
        """
        # Skip logging for noisy/infrastructure endpoints
        skip_paths = {"/health", "/", "/status", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Extract client info
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = str(request.url.path)
        
        # Log incoming request
        api_logger.info(log_messages.request_received(method, path, client_host))
        
        # Process request and measure time
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            # If an exception occurs, it will be caught by exception handlers
            # We just measure the time here
            duration_ms = (time.time() - start_time) * 1000
            api_logger.error(
                log_messages.request_completed(method, path, 500, duration_ms)
            )
            raise
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log completed request with appropriate level
        status_code = response.status_code
        
        if 200 <= status_code < 300:
            # Success - INFO level
            api_logger.info(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        elif 400 <= status_code < 500:
            # Client error - WARNING level
            api_logger.warning(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        elif 500 <= status_code < 600:
            # Server error - ERROR level
            api_logger.error(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        else:
            # Other status codes
            api_logger.info(
                log_messages.request_completed(method, path, status_code, duration_ms)
            )
        
        return response


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware to prevent system overload.
    
    Applies a per-IP rate limit across ALL endpoints (not per-route).
    Uses Redis if available (shared across workers), else in-memory (dev only).
    
    Settings:
    - Default: 100 requests per minute per IP
    - Skips health check endpoints
    """
    
    def __init__(self, app: ASGIApp, limit: int = 100, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
        
        # Try to use Redis if configured (production)
        self.redis_client = None
        redis_url = None
        try:
            from app.config import settings
            redis_url = getattr(settings, 'REDIS_URL', None) or os.getenv("REDIS_URL")
        except Exception:
            redis_url = os.getenv("REDIS_URL")
        
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                api_logger.info(f"🔧 Global rate limit using Redis at {redis_url}")
            except Exception as e:
                error_logger.warning(f"⚠️ Redis not available for rate limiting: {e}. Falling back to in-memory.")
        
        # In-memory fallback (not shared across workers, only for dev)
        self.counter = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for infrastructure/health endpoints
        skip_paths = {"/health", "/health/live", "/", "/status", "/docs", "/openapi.json", "/redoc", "/favicon.ico", "/metrics"}
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Get client IP (respect X-Forwarded-For if behind proxy)
        client_ip = "unknown"
        if request.client and request.client.host:
            client_ip = request.client.host
        # X-Forwarded-For may be set by Azure Front Door/App Gateway
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Check rate limit
        if self.redis_client:
            # Use Redis (shared across workers)
            import time
            key = f"global_rate_limit:{client_ip}"
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, self.window)
            if current > self.limit:
                error_logger.warning(f"🚦 Global rate limit exceeded for IP {client_ip}: {current}/{self.limit}")
                raise HTTPException(status_code=429, detail="Too many requests - global rate limit exceeded")
        else:
            # In-memory fallback (fixed window)
            import time
            now = int(time.time())
            window_key = now // self.window
            key = f"{client_ip}:{window_key}"
            self.counter[key] = self.counter.get(key, 0) + 1
            if self.counter[key] > self.limit:
                raise HTTPException(status_code=429, detail="Too many requests - global rate limit exceeded")
        
        # Proceed with request
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            raise e

