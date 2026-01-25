"""
Configuration management for the application.
Loads environment variables and provides validated settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "AI English Assessment Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_DB_URL: str
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
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
    SENDGRID_API_KEY: str = ""
    
    # Site24x7 Monitoring
    SITE24X7_API_KEY: str = ""
    SITE24X7_ENABLED: bool = False
    
    def get_cors_origins(self) -> List[str]:
        """Parse and return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    
    model_config = SettingsConfigDict(
        env_file=".env.backend",
        case_sensitive=True,
        env_parse_none_str="null",
    )


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
