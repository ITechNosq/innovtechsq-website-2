"""
Application Configuration
Loads environment variables and provides centralized config access.

SECURE CONFIGURATION:
- All secrets loaded from environment variables
- No hardcoded values
- Default values are placeholders only
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive values must be set in .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============== DATABASE ==============
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/leads_db"
    
    # Admin credentials (for JWT authentication)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "CHANGE_ADMIN_PASSWORD_IN_PRODUCTION"
    
    # Cloudflare Turnstile Secret Key (for CAPTCHA)
    TURNSTILE_SECRET_KEY: str = ""
    
    # JWT secret (for future JWT-based auth)
    JWT_SECRET: str = "CHANGE_JWT_SECRET_IN_PRODUCTION"
    
    # ============== EMAIL ==============
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # Admin email (where lead notifications go)
    ADMIN_EMAIL: str = ""
    
    # ============== RATE LIMITING ==============
    # Redis URL for distributed rate limiting
    REDIS_URL: str = "redis://localhost:6379"
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # ============== CORS ==============
# Allowed origins (comma-separated in env) - Added localhost wildcards for dev
    CORS_ORIGINS: str = "http://localhost,http://127.0.0.1,https://innovtechnosq.co.in"
    
    # ============== APP ==============
    APP_NAME: str = "InnovTech Sq Lead API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============== PAGINATION ==============
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    
    # ============== DUPLICATE PROTECTION ==============
    DUPLICATE_WINDOW_HOURS: int = 24
    
    def get_cors_origins(self) -> list[str]:
        """
        Get CORS origins as a list.
        Parses comma-separated string from environment.
        """
        if not self.CORS_ORIGINS:
            return []  # No origins allowed if not configured!
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG


# Create global settings instance
settings = Settings()


# ============== HELPER FUNCTIONS ==============

def get_database_url() -> str:
    """Get the database URL."""
    return settings.DATABASE_URL


def get_email_config() -> dict:
    """Get email configuration."""
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "admin_email": settings.ADMIN_EMAIL
    }
