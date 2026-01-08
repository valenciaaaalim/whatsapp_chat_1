"""
PII detection endpoint using GLiNER service.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import sys
import os

# Import gliner_service from backend directory
# The file is at web-app/backend/gliner_service.py
# This router is at web-app/backend/app/routers/pii.py
# So we need to go up two levels: ../../gliner_service.py
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from gliner_service import GliNERService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pii", tags=["pii"])

# Global service instance (lazy loaded)
_gliner_service: Optional[GliNERService] = None


def get_gliner_service() -> GliNERService:
    """Get or initialize GLiNER service singleton."""
    global _gliner_service
    if _gliner_service is None:
        _gliner_service = GliNERService()
        _gliner_service.initialize()
    return _gliner_service


class PiiDetectRequest(BaseModel):
    """PII detection request."""
    draft_text: str = Field(..., min_length=1)


class PiiSpan(BaseModel):
    """PII span information."""
    start: int
    end: int
    label: str
    text: str


class PiiDetectResponse(BaseModel):
    """PII detection response."""
    masked_text: str
    pii_spans: List[PiiSpan]


@router.post("/detect", response_model=PiiDetectResponse)
async def detect_pii(request: PiiDetectRequest):
    """
    Detect PII in draft text and return masked text with PII spans.
    Used for live underlining in Group A only.
    """
    try:
        logger.info("PII detect request received (len=%s)", len(request.draft_text))
        service = get_gliner_service()
        logger.info("PII service ready, running mask_and_chunk")
        result = service.mask_and_chunk(request.draft_text)
        logger.info("PII detect complete (spans=%s)", len(result.pii_spans))
        
        # Convert PiiSpan dataclasses to Pydantic models
        pii_spans = [
            PiiSpan(
                start=span.start,
                end=span.end,
                label=span.label,
                text=span.text
            )
            for span in result.pii_spans
        ]
        
        return PiiDetectResponse(
            masked_text=result.masked_text,
            pii_spans=pii_spans
        )
    except Exception as e:
        logger.error(f"PII detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PII detection failed: {str(e)}")


@router.get("/status")
async def pii_status():
    """Return whether the GLiNER model is loaded."""
    try:
        loaded = get_gliner_service().is_loaded()
    except Exception:
        loaded = False
    return {"loaded": loaded}
