"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered English speaking assessment platform",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
