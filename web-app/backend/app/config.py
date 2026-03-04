"""
Configuration settings for the web app backend.
"""
import os
from typing import List, Optional


def _clean_env(value: Optional[str]) -> Optional[str]:
    """Normalize env strings and strip accidental wrapping quotes."""
    if value is None:
        return None
    normalized = value.strip()
    if len(normalized) >= 2:
        if (normalized[0] == '"' and normalized[-1] == '"') or (
            normalized[0] == "'" and normalized[-1] == "'"
        ):
            normalized = normalized[1:-1].strip()
    return normalized


def _env_bool(name: str, default: bool) -> bool:
    """Parse env bool flags."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Application settings."""
    
    # Database
    DATABASE_URL: Optional[str] = _clean_env(os.getenv("DATABASE_URL"))
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "https://localhost:3000",
    ]
    ALLOWED_ORIGIN_REGEX: Optional[str] = os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?"
    )
    
    # Gemini API
    # Per Google docs, GOOGLE_API_KEY is a supported standard env var.
    # If both are set, prefer GOOGLE_API_KEY.
    GOOGLE_API_KEY: Optional[str] = _clean_env(os.getenv("GOOGLE_API_KEY"))
    GEMINI_API_KEY: Optional[str] = _clean_env(os.getenv("GEMINI_API_KEY"))
    # Legacy alias retained for backwards compatibility.
    GEMINI_MODEL: Optional[str] = _clean_env(os.getenv("GEMINI_MODEL"))
    GEMINI_FIRST_MODEL: Optional[str] = (
        _clean_env(os.getenv("GEMINI_FIRST_MODEL"))
        or GEMINI_MODEL
    )
    GEMINI_SECOND_MODEL: Optional[str] = _clean_env(os.getenv("GEMINI_SECOND_MODEL"))
    FIRST_MODEL_THINKING_POWER: str = (
        _clean_env(os.getenv("FIRST_MODEL_THINKING_POWER"))
        or _clean_env(os.getenv("GEMINI_THINKING_BUDGET"))
        or "-1"
    )
    SECOND_MODEL_THINKING_POWER: str = (
        _clean_env(os.getenv("SECOND_MODEL_THINKING_POWER"))
        or "-1"
    )
    FIRST_MODEL_TIMEOUT_SECONDS: int = int(
        _clean_env(os.getenv("FIRST_MODEL_TIMEOUT_SECONDS"))
        or _clean_env(os.getenv("GEMINI_TIMEOUT_SECONDS"))
        or "20"
    )
    FIRST_MODEL_MAX_ATTEMPTS: int = int(
        _clean_env(os.getenv("FIRST_MODEL_MAX_ATTEMPTS"))
        or _clean_env(os.getenv("GEMINI_MAX_ATTEMPTS"))
        or "1"
    )
    GEMINI_MAX_ATTEMPTS: int = FIRST_MODEL_MAX_ATTEMPTS
    SECOND_MODEL_TIMEOUT_SECONDS: int = int(
        _clean_env(os.getenv("SECOND_MODEL_TIMEOUT_SECONDS"))
        or _clean_env(os.getenv("GEMINI_SECOND_MODEL_TIMEOUT_SECONDS"))
        or "20"
    )
    SECOND_MODEL_MAX_ATTEMPTS: int = int(
        _clean_env(os.getenv("SECOND_MODEL_MAX_ATTEMPTS"))
        or "1"
    )
    GEMINI_THINKING_BUDGET: str = _clean_env(os.getenv("GEMINI_THINKING_BUDGET")) or "-1"
    GEMINI_INCLUDE_THOUGHTS: bool = _env_bool("GEMINI_INCLUDE_THOUGHTS", True)
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
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
