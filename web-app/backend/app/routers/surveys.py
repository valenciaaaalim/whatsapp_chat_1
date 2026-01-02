"""
Survey routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SurveyResponse, Participant
from app.schemas import SurveyResponseSchema

router = APIRouter(prefix="/api/surveys", tags=["surveys"])


@router.post("/responses")
def submit_survey_response(
    response: SurveyResponseSchema,
    participant_id: int,
    db: Session = Depends(get_db)
):
    """Submit a survey response."""
    # Verify participant exists
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Create survey response
    survey_response = SurveyResponse(
        participant_id=participant_id,
        survey_type=response.survey_type,
        question_id=response.question_id,
        question_text=response.question_text,
        response_text=response.response_text,
        response_json=response.response_json
    )
    db.add(survey_response)
    db.commit()
    db.refresh(survey_response)
    
    return {"id": survey_response.id, "status": "submitted"}


@router.get("/responses/{participant_id}")
def get_survey_responses(
    participant_id: int,
    db: Session = Depends(get_db)
):
    """Get all survey responses for a participant."""
    responses = db.query(SurveyResponse).filter(
        SurveyResponse.participant_id == participant_id
    ).all()
    
    return [
        {
            "id": r.id,
            "survey_type": r.survey_type,
            "question_id": r.question_id,
            "question_text": r.question_text,
            "response_text": r.response_text,
            "response_json": r.response_json,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in responses
    ]

