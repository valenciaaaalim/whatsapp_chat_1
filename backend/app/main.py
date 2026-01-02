"""
FastAPI backend for GLiNER-based PII masking and chunking.
Deployed to Cloud Run with Cloudflare in front for security hardening.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import time

from app.services.gliner_service import GliNERService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GLiNER PII Masking Service",
    description="PII detection and masking using GLiNER model",
    version="1.0.0"
)

# CORS configuration - restrict to your Cloudflare domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
    max_age=3600,
)

# Initialize GLiNER service (lazy loading)
gliner_service: Optional[GliNERService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize GLiNER model on startup."""
    global gliner_service
    logger.info("Initializing GLiNER service...")
    try:
        gliner_service = GliNERService()
        logger.info("GLiNER service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GLiNER service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global gliner_service
    if gliner_service:
        gliner_service.cleanup()
    logger.info("Application shutdown")


# Request/Response models
class MaskRequest(BaseModel):
    text: str = Field(..., description="Text to mask and chunk", min_length=1, max_length=50000)
    max_tokens: int = Field(default=512, description="Maximum tokens per chunk", ge=128, le=2048)


class PiiSpan(BaseModel):
    start: int
    end: int
    label: str
    text: str


class MaskResponse(BaseModel):
    masked_text: str
    chunks: List[str]
    pii_spans: List[PiiSpan]
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    return HealthResponse(
        status="healthy",
        model_loaded=gliner_service is not None and gliner_service.is_loaded(),
        version="1.0.0"
    )


@app.post("/mask", response_model=MaskResponse)
async def mask_and_chunk(request: MaskRequest):
    """
    Mask PII and chunk text using GLiNER.
    
    This endpoint:
    1. Detects PII entities using GLiNER
    2. Masks detected entities with [LABEL] tags
    3. Chunks the masked text respecting token limits
    """
    if not gliner_service or not gliner_service.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="GLiNER service not available"
        )
    
    start_time = time.time()
    
    try:
        result = gliner_service.mask_and_chunk(
            text=request.text,
            max_tokens=request.max_tokens
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(
            f"Processed text: {len(request.text)} chars, "
            f"{len(result.pii_spans)} PII entities, "
            f"{len(result.chunks)} chunks, "
            f"{processing_time:.2f}ms"
        )
        
        return MaskResponse(
            masked_text=result.masked_text,
            chunks=result.chunks,
            pii_spans=[
                PiiSpan(
                    start=span.start,
                    end=span.end,
                    label=span.label,
                    text=span.text
                )
                for span in result.pii_spans
            ],
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


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
    uvicorn.run(app, host="0.0.0.0", port=8080)

