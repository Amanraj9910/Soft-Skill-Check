"""
Main FastAPI application entry point.
"""
import os
import asyncio
import concurrent.futures
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import jwt

from app.config import settings
from app.routers import assessments, conversation, scoring, responses, users
from app.routers import health as health_router

from app.core.logging import configure_logging, api_logger, format_duration
from app.core.middleware import RequestLoggingMiddleware, GlobalRateLimitMiddleware
from app.core.error_handlers import register_exception_handlers
from app.core import log_messages

# --- Rate Limiting Setup ---
# Single shared limiter used by all routers (see app/core/rate_limiter.py)
from app.core.rate_limiter import limiter

# User-key limiter for authenticated routes (falls back to IP)
# Uses same Redis storage backend as global limiter
def _get_user_key(request: Request) -> str:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub", get_remote_address(request))
    except Exception:
        return get_remote_address(request)

# Reuse the same storage backend as the global limiter
auth_limiter = Limiter(key_func=_get_user_key, storage=limiter._storage)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered English speaking assessment platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# Attach limiters to app state so routers can access them
app.state.limiter = limiter
app.state.auth_limiter = auth_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging FIRST (before any other operations)
configure_logging(
    log_level=settings.LOG_LEVEL,
    enable_colors=settings.LOG_ENABLE_COLORS,
    enable_emojis=settings.LOG_ENABLE_EMOJIS
)

# --- OpenTelemetry Setup (opt-in via OTEL_ENABLED=True) ---
if settings.OTEL_ENABLED:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource(attributes={
            "service.name": "soft-skill-check-backend",
            "service.version": "1.0.0",
            "deployment.environment": settings.APP_ENV,
        })
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        # Auto-instrument outgoing HTTP calls and incoming FastAPI requests
        HTTPXClientInstrumentor().instrument()
        FastAPIInstrumentor.instrument_app(app)

        api_logger.info(f"✅ OpenTelemetry enabled → {settings.OTEL_ENDPOINT}")
    except Exception as e:
        api_logger.warning(f"⚠️ OpenTelemetry setup failed (non-fatal): {e}")
# ---------------------------------------------------------------

# Register error handlers
register_exception_handlers(app)

# Register request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    enable_body_logging=settings.DEBUG  # Only log bodies in debug mode
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global rate limit (applies to all requests, before heavy processing)
# Uses Redis if REDIS_URL configured, else in-memory (dev only)
app.add_middleware(
    GlobalRateLimitMiddleware,
    limit=100,   # Max 100 requests/minute per IP globally
    window=60
)

# Register request logging middleware (after rate limit to log only passed requests)
app.add_middleware(
    RequestLoggingMiddleware,
    enable_body_logging=settings.DEBUG  # Only log bodies in debug mode
)

# Register routers
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(conversation.router)
app.include_router(scoring.router)
app.include_router(responses.router)
app.include_router(health_router.router)



@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "docs": "/docs"
    }




@app.get("/status")
async def system_status():
    """
    Comprehensive system status endpoint.
    """
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "service": "backend",
        "timestamp": "now"
    }


@app.get("/api/v1/config/test")
async def test_config():
    """Test endpoint to verify configuration (remove in production)."""
    if not settings.DEBUG:
        return JSONResponse(
            status_code=403,
            content={"detail": "This endpoint is only available in debug mode"}
        )
    
    return {
        "supabase_configured": bool(settings.SUPABASE_URL),
        "azure_openai_configured": bool(settings.AZURE_OPENAI_ENDPOINT),
        "azure_speech_configured": bool(settings.AZURE_SPEECH_KEY),
        "azure_storage_configured": bool(settings.AZURE_STORAGE_CONNECTION_STRING),
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Run on application startup — logs once across all workers."""
    # Dedup guard: only the first worker to set this env var logs the banner
    if os.environ.get("_STARTUP_LOGGED") == "1":
        return
    os.environ["_STARTUP_LOGGED"] = "1"

    # Increase thread pool for high-concurrency workloads
    # With 4 Gunicorn workers, each gets its own thread pool.
    # Per-worker needs: up to 20 STT + 20 TTS + 20 DB/audio ops = ~60 threads
    # Use 60 per worker to avoid starvation, total 240 threads across all workers
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=60,  # Per worker - enough for STT/TTS/DB peaks
        thread_name_prefix="worker"
    )
    loop.set_default_executor(executor)
    api_logger.info(f"🔧 Thread pool increased to 60 workers per gunicorn worker (for high concurrency)")

    api_logger.info(
        log_messages.app_starting(
            app_name=settings.APP_NAME,
            environment=settings.APP_ENV,
            debug=settings.DEBUG,
            host=settings.HOST,
            port=settings.PORT
        )
    )
    api_logger.info(
        log_messages.config_loaded({
            "cors_origins": len(settings.get_cors_origins()),
            "log_level": settings.LOG_LEVEL,
            "colors_enabled": settings.LOG_ENABLE_COLORS
        })
    )
    api_logger.info(f"🌐 CORS origins: {settings.get_cors_origins()}")
    api_logger.info(log_messages.app_ready(settings.APP_NAME))


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    api_logger.info(log_messages.app_shutting_down(settings.APP_NAME))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

# Trigger reload for new dependencies
