"""
Main FastAPI application entry point.
"""
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

# Import new logging and error handling system
from app.core.logging import configure_logging, api_logger, format_duration
from app.core.middleware import RequestLoggingMiddleware
from app.core.error_handlers import register_exception_handlers
from app.core import log_messages

# --- Rate Limiting Setup ---
# IP-based limiter for anonymous/public routes
limiter = Limiter(key_func=get_remote_address)

# User-key limiter for authenticated routes (falls back to IP)
def _get_user_key(request: Request) -> str:
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub", get_remote_address(request))
    except Exception:
        return get_remote_address(request)

auth_limiter = Limiter(key_func=_get_user_key)

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
    """Run on application startup."""
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
    api_logger.info(f"🌐 CORS allowed origins: {settings.get_cors_origins()}")
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
