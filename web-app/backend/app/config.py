"""
Configuration settings for the web app backend.
"""
import os
from pathlib import Path
from typing import List, Optional

class Settings:
    """Application settings."""
    
    # Database
    _default_db_path = (Path(__file__).resolve().parent.parent / "data" / "web_app.db")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{_default_db_path}"
    )
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "https://localhost:3000",
    ]
    
    # Gemini API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-pro")
    GEMINI_TIMEOUT_SECONDS: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    CSRF_SECRET: str = os.getenv("CSRF_SECRET", "change-me-in-production")
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # XML Extractor service
    XML_EXTRACTOR_URL: str = os.getenv(
        "XML_EXTRACTOR_URL",
        "http://xml-extractor:8080"
    )
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Cloud Run settings
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    REGION: str = os.getenv("REGION", "us-central1")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "web-app-backend")
    
    # Prolific
    PROLIFIC_COMPLETION_URL: str = os.getenv(
        "PROLIFIC_COMPLETION_URL",
        "https://app.prolific.co/submissions/complete"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))


settings = Settings()
