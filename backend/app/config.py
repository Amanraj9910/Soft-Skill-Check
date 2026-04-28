"""
Configuration management for the application.
Loads environment variables and provides validated settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file_path() -> str | None:
    """Use .env.backend only when present (e.g. local dev). Azure uses App Settings."""
    path = os.path.join(os.path.dirname(__file__), "..", ".env.backend")
    return path if os.path.isfile(path) else None


_model_config: dict = {
    "case_sensitive": True,
    "env_parse_none_str": "null",
    "extra": "ignore",
}
if _env_file_path():
    _model_config["env_file"] = _env_file_path()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Security
    SUPABASE_JWT_SECRET: str
    
    # Application
    APP_NAME: str = "AI English Assessment Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://english-assisment-frontend-dneudafhasbchsfv.centralindia-01.azurewebsites.net"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_DB_URL: str
    SUPABASE_JWT_SECRET: str
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_NAME_MINI: str = "gpt-4o-mini"
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    
    # Azure Speech
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    AZURE_SPEECH_LANGUAGE: str = "en-US"
    AZURE_TTS_VOICE_NAME: str = "en-US-JennyNeural"
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str = "assessment-audio"
    AZURE_BLOB_SAS_EXPIRY_HOURS: int = 24
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Audio Processing
    MAX_AUDIO_DURATION_SECONDS: int = 300
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_FORMAT: str = "wav"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_ENABLE_COLORS: bool = True
    LOG_ENABLE_EMOJIS: bool = True
    
    # Optional services
    SENTRY_DSN: str = ""
    
    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_ENDPOINT: str = "http://localhost:4317"
    
    # Redis (for rate limiting in production with multiple workers)
    REDIS_URL: str = ""
    
    # SENDGRID_API_KEY: str = ""
    
    # Site24x7 Monitoring
    SITE24X7_API_KEY: str = ""
    SITE24X7_ENABLED: bool = False
    
    def get_cors_origins(self) -> List[str]:
        """Parse and return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def openai_base_url(self) -> str:
        """
        Derive the OpenAI-compatible base_url from the Azure endpoint.

        Azure AI Foundry project URLs contain '/v1' and MUST NOT have
        an api-version query parameter.  We use the standard OpenAI
        client (AsyncOpenAI) with this base_url instead of AsyncAzureOpenAI.
        """
        ep = self.AZURE_OPENAI_ENDPOINT.rstrip("/")
        idx = ep.find("/v1")
        if idx != -1:
            return ep[:idx + 3]          # …/openai/v1
        # Fallback: append /openai/v1 for standard Azure OpenAI resources
        return ep.rstrip("/") + "/openai/v1"

    model_config = SettingsConfigDict(**_model_config)


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for accessing settings."""
    return settings


if __name__ == "__main__":
    """Test configuration loading."""
    print(f"✅ Configuration loaded successfully!")
    print(f"App Name: {settings.APP_NAME}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Supabase URL: {settings.SUPABASE_URL[:30]}...")
    print(f"Azure OpenAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT[:40]}...")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
