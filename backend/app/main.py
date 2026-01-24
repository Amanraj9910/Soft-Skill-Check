"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import assessments, conversation, scoring, responses, users

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered English speaking assessment platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# --- Observability Setup ---
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

from app.logging_config import configure_logging

# Configure Structlog
configure_logging()

# Configure OpenTelemetry
resource = Resource(attributes={
    "service.name": "soft-skill-check-backend",
    "service.version": "1.0.0",
    "deployment.environment": settings.APP_ENV
})

# trace.set_tracer_provider(TracerProvider(resource=resource))
# otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
# spam_processor = BatchSpanProcessor(otlp_exporter)
# trace.get_tracer_provider().add_span_processor(spam_processor)

# Instrument libraries (Client-side)
# HTTPXClientInstrumentor().instrument()
# RequestsInstrumentor().instrument()
# OpenAIInstrumentor().instrument()

# Instrument FastAPI
# FastAPIInstrumentor.instrument_app(app)
# ---------------------------


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


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV
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
    print(f"🚀 {settings.APP_NAME} starting...")
    print(f"📊 Environment: {settings.APP_ENV}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print(f"🌐 CORS origins: {settings.CORS_ORIGINS}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 {settings.APP_NAME} shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
