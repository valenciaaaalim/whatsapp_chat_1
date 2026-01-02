"""
Configuration settings for the FastAPI application.
"""

import os
from typing import List

class Settings:
    """Application settings."""
    
    # CORS settings - update with your Cloudflare domain
    ALLOWED_ORIGINS: List[str] = [
        "https://your-cloudflare-domain.com",
        "http://localhost:3000",  # For local testing
    ]
    
    # GLiNER model settings
    GLINER_MODEL_NAME: str = os.getenv(
        "GLINER_MODEL_NAME",
        "knowledgator/gliner-pii-base-v1.0"
    )
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Cloud Run settings
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    REGION: str = os.getenv("REGION", "us-central1")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "gliner-pii-service")
    
    # Security settings
    MAX_REQUEST_SIZE: int = 50000  # Max characters per request
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))


settings = Settings()

