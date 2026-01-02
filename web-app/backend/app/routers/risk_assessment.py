"""
Risk assessment routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import RiskAssessmentRequest, RiskAssessmentResponse
from app.services.gemini_service import GeminiService
from app.services.risk_assessment import RiskAssessmentService
from app.models import ConversationSession

router = APIRouter(prefix="/api/risk", tags=["risk"])


def get_risk_assessment_service() -> RiskAssessmentService:
    """Dependency to get risk assessment service."""
    gemini_service = GeminiService()
    return RiskAssessmentService(gemini_service)


@router.post("/assess", response_model=RiskAssessmentResponse)
def assess_risk(
    request: RiskAssessmentRequest,
    db: Session = Depends(get_db),
    risk_service: RiskAssessmentService = Depends(get_risk_assessment_service)
):
    """Assess risk of a draft message."""
    # Verify session exists
    session = db.query(ConversationSession).filter(
        ConversationSession.id == request.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Perform risk assessment
    # Note: In production, you'd want to mask PII first using GLiNER service
    # For now, we'll pass the text directly (masking can be added later)
    result = risk_service.assess_risk(
        draft_text=request.draft_text,
        conversation_history=request.conversation_history
    )
    
    return RiskAssessmentResponse(
        risk_level=result["risk_level"],
        explanation=result["explanation"],
        safer_rewrite=result["safer_rewrite"],
        show_warning=result["show_warning"],
        primary_risk_factors=result.get("primary_risk_factors", [])
    )

