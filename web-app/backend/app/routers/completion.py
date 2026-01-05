"""
Completion and Prolific routing routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant, ParticipantRecord
from app.schemas import CompletionRequest
from app.config import settings
from urllib.parse import urlencode
from datetime import datetime

router = APIRouter(prefix="/api/completion", tags=["completion"])


@router.get("/prolific")
def get_prolific_completion_url(
    participant_id: int,
    completion_code: str = None,
    db: Session = Depends(get_db)
):
    """Generate Prolific completion URL."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if participant.completed_at is None:
        participant.completed_at = datetime.utcnow()
        db.commit()

    if participant.prolific_id:
        record = db.query(ParticipantRecord).filter(
            ParticipantRecord.participant_id == participant.prolific_id
        ).first()
        if record and record.completed_at is None:
            record.completed_at = participant.completed_at
            if record.created_at and record.completed_at:
                delta = record.completed_at - record.created_at
                record.duration_of_study = delta.total_seconds()
            db.commit()
    
    # Build completion URL
    base_url = settings.PROLIFIC_COMPLETION_URL
    params = {}
    if completion_code:
        params["cc"] = completion_code
    if participant.prolific_id:
        params["PROLIFIC_PID"] = participant.prolific_id
    
    if params:
        url = f"{base_url}?{urlencode(params)}"
    else:
        url = base_url
    
    return {"completion_url": url}


@router.get("/redirect")
def redirect_to_prolific(
    participant_id: int,
    completion_code: str = None,
    db: Session = Depends(get_db)
):
    """Redirect user to Prolific completion page."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if participant.completed_at is None:
        participant.completed_at = datetime.utcnow()
        db.commit()

    if participant.prolific_id:
        record = db.query(ParticipantRecord).filter(
            ParticipantRecord.participant_id == participant.prolific_id
        ).first()
        if record and record.completed_at is None:
            record.completed_at = participant.completed_at
            if record.created_at and record.completed_at:
                delta = record.completed_at - record.created_at
                record.duration_of_study = delta.total_seconds()
            db.commit()
    
    # Build completion URL
    base_url = settings.PROLIFIC_COMPLETION_URL
    params = {}
    if completion_code:
        params["cc"] = completion_code
    if participant.prolific_id:
        params["PROLIFIC_PID"] = participant.prolific_id
    
    if params:
        url = f"{base_url}?{urlencode(params)}"
    else:
        url = base_url
    
    return RedirectResponse(url=url)
