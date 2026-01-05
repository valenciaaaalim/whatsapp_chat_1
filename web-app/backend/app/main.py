"""
Main FastAPI application for the web app backend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import time

from app.config import settings
from app.database import init_db
from app.middleware.security import SecurityHeadersMiddleware
from app.routers import (
    participants,
    conversations,
    risk_assessment,
    user_inputs,
    surveys,
    completion,
    participant_records
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="WhatsApp Risk Assessment Web App",
    description="Web application for user testing of WhatsApp risk assessment",
    version="1.0.0"
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(participants.router)
app.include_router(conversations.router)
app.include_router(risk_assessment.router)
app.include_router(user_inputs.router)
app.include_router(surveys.router)
app.include_router(completion.router)
app.include_router(participant_records.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    logger.info("Starting up application...")
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
