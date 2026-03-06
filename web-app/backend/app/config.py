"""
Configuration settings for the web app backend.
"""
import logging
import os
from typing import List, Optional


logger = logging.getLogger(__name__)


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


def _env_int(name: str, default: int) -> int:
    """Parse env var as int, warning and falling back on invalid values."""
    raw = _clean_env(os.getenv(name))
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        logger.warning("Invalid integer for %s=%r; using default %s", name, raw, default)
        return default


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
    GEMINI_API_KEY: Optional[str] = _clean_env(os.getenv("GEMINI_API_KEY"))
    GEMINI_FIRST_MODEL: Optional[str] = _clean_env(os.getenv("GEMINI_FIRST_MODEL"))
    GEMINI_SECOND_MODEL: Optional[str] = _clean_env(os.getenv("GEMINI_SECOND_MODEL"))
    FIRST_MODEL_THINKING_POWER: str = (
        _clean_env(os.getenv("FIRST_MODEL_THINKING_POWER"))
        or "-1"
    )
    SECOND_MODEL_THINKING_POWER: str = (
        _clean_env(os.getenv("SECOND_MODEL_THINKING_POWER"))
        or "-1"
    )
    FIRST_MODEL_TIMEOUT_SECONDS: int = _env_int("FIRST_MODEL_TIMEOUT_SECONDS", 20)
    FIRST_MODEL_MAX_ATTEMPTS: int = _env_int("FIRST_MODEL_MAX_ATTEMPTS", 1)
    SECOND_MODEL_TIMEOUT_SECONDS: int = _env_int("SECOND_MODEL_TIMEOUT_SECONDS", 20)
    SECOND_MODEL_MAX_ATTEMPTS: int = _env_int("SECOND_MODEL_MAX_ATTEMPTS", 1)
    GEMINI_INCLUDE_THOUGHTS: bool = _env_bool("GEMINI_INCLUDE_THOUGHTS", True)

    # Frontend GLiNER typing debounce (milliseconds), served via backend config endpoint.
    GLINER_DEBOUNCE_MS: int = _env_int("GLINER_DEBOUNCE_MS", 400)
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = _env_int("PORT", 8080)
    
    # Prolific completion — set via env vars, no hardcoded defaults
    PROLIFIC_COMPLETION_URL: Optional[str] = _clean_env(os.getenv("PROLIFIC_COMPLETION_URL"))
    COMPLETION_URL: Optional[str] = _clean_env(os.getenv("COMPLETION_URL"))
    COMPLETION_CODE: Optional[str] = _clean_env(os.getenv("COMPLETION_CODE"))

    LLM_SCENARIO_MAX_CALLS: int = _env_int("LLM_SCENARIO_MAX_CALLS", 10)

    # Participation requirements
    REQUIRE_MOBILE: bool = _env_bool("REQUIRE_MOBILE", False)


settings = Settings()
