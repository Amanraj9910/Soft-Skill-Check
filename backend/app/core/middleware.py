"""
Request middleware: trace ID generation + selective request/response logging.

Design principles:
- Generate a trace_id (UUID) for every request; store in request.state + ContextVar.
- Log REQUEST_RECEIVED only for meaningful business endpoints.
- Log RESPONSE_SENT only when: status >= 400 OR latency > 500ms.
- Heartbeat, list-assessment, and OPTIONS calls are completely silent.
- Global per-IP rate limiting (in-memory dev / Redis production).
"""
import os
import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import api_logger, error_logger, set_trace_id, event_log, format_duration

# Paths that should never be logged (infrastructure noise)
_SILENT_PATHS = {
    "/health", "/health/live", "/health/ready",
    "/", "/status", "/docs", "/openapi.json", "/redoc",
    "/favicon.ico", "/metrics",
}

# Paths that are logged only on error / slowness (not on every call)
_QUIET_PATHS_SUFFIXES = (
    "/heartbeat",       # 30-second polling — completely silent unless error
)

_SLOW_THRESHOLD_MS = 500  # log RESPONSE_SENT if slower than this


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Per-request trace ID + selective logging middleware.

    Attaches request.state.trace_id to every request.
    Logs REQUEST_RECEIVED for important endpoints.
    Logs RESPONSE_SENT when status >= 400 or latency > 500ms.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # ── Always skip infrastructure paths ────────────────────────────────
        if path in _SILENT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # ── Generate + propagate trace ID ───────────────────────────────────
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id
        set_trace_id(trace_id)

        method = request.method
        is_quiet = path.endswith(_QUIET_PATHS_SUFFIXES)

        # ── Log incoming request (skip quiet paths) ──────────────────────────
        if not is_quiet:
            event_log(
                api_logger, logging.INFO, "REQUEST_RECEIVED",
                f"{method} {path}",
                metadata={"method": method, "path": path, "trace_id": trace_id},
            )

        # ── Process request ──────────────────────────────────────────────────
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            event_log(
                error_logger, logging.ERROR, "REQUEST_ERROR",
                f"{method} {path} → 500  {format_duration(latency_ms)}",
                metadata={"method": method, "path": path, "status": 500,
                          "latency_ms": round(latency_ms), "trace_id": trace_id,
                          "error": str(exc)},
            )
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        status = response.status_code
        is_slow = latency_ms > _SLOW_THRESHOLD_MS
        is_error = status >= 400

        # ── Log RESPONSE_SENT only when notable ──────────────────────────────
        if is_error or is_slow or not is_quiet:
            suffix = " ⚠ SLOW" if is_slow and not is_error else ""
            level = logging.ERROR if status >= 500 else (
                logging.WARNING if status >= 400 else logging.INFO
            )
            event_log(
                api_logger, level, "RESPONSE_SENT",
                f"{method} {path} → {status}  {format_duration(latency_ms)}{suffix}",
                metadata={"method": method, "path": path, "status": status,
                          "latency_ms": round(latency_ms), "trace_id": trace_id},
            )

        return response


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware — 100 req/min per IP.
    Uses Redis if configured (production), in-memory fixed-window otherwise (dev).
    """

    def __init__(self, app: ASGIApp, limit: int = 100, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.redis_client = None
        self._counter: dict = {}

        redis_url = None
        try:
            from app.config import settings
            redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL")
        except Exception:
            redis_url = os.getenv("REDIS_URL")

        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                api_logger.info(f"Global rate limit: Redis at {redis_url}")
            except Exception as e:
                api_logger.warning(f"Redis unavailable for rate limiting: {e} — using in-memory")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        skip = {"/health", "/health/live", "/", "/status",
                "/docs", "/openapi.json", "/redoc", "/favicon.ico", "/metrics"}
        if request.url.path in skip or request.method == "OPTIONS":
            return await call_next(request)

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        if self.redis_client:
            key = f"rl:global:{client_ip}"
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, self.window)
            if current > self.limit:
                event_log(
                    error_logger, logging.WARNING, "RATE_LIMIT_EXCEEDED",
                    f"IP {client_ip} exceeded {self.limit} req/{self.window}s",
                    metadata={"ip": client_ip, "count": current, "limit": self.limit},
                )
                raise HTTPException(status_code=429, detail="Too many requests")
        else:
            now = int(time.time())
            key = f"{client_ip}:{now // self.window}"
            self._counter[key] = self._counter.get(key, 0) + 1
            if self._counter[key] > self.limit:
                raise HTTPException(status_code=429, detail="Too many requests")

        return await call_next(request)
