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
from app.utils import get_singapore_time, ensure_singapore_tz

router = APIRouter(prefix="/api/completion", tags=["completion"])


@router.get("/prolific")
def get_prolific_completion_url(
    participant_id: int,
    completion_code: str = None,
    prolific_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Generate Prolific completion URL."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if participant.prolific_id is None and prolific_id:
        participant.prolific_id = prolific_id
    if participant.completed_at is None:
        now_sgt = get_singapore_time()
        participant.completed_at = now_sgt
        participant.updated_at = now_sgt
    db.commit()

    if participant.prolific_id:
        record = db.query(ParticipantRecord).filter(
            ParticipantRecord.prolific_id == participant.prolific_id
        ).first()
        if not record:
            record = ParticipantRecord(
                prolific_id=participant.prolific_id,
                variant=participant.variant,
                created_at=get_singapore_time()
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        if record.completed_at is None:
            record.completed_at = get_singapore_time()
        if not record.created_at:
            record.created_at = get_singapore_time()
        if record.created_at and record.completed_at:
            created_at = ensure_singapore_tz(record.created_at)
            completed_at = ensure_singapore_tz(record.completed_at)
            if created_at and completed_at:
                delta = completed_at - created_at
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
    prolific_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Redirect user to Prolific completion page."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if participant.prolific_id is None and prolific_id:
        participant.prolific_id = prolific_id
    if participant.completed_at is None:
        now_sgt = get_singapore_time()
        participant.completed_at = now_sgt
        participant.updated_at = now_sgt
        db.commit()

    if participant.prolific_id:
        record = db.query(ParticipantRecord).filter(
            ParticipantRecord.prolific_id == participant.prolific_id
        ).first()
        if not record:
            record = ParticipantRecord(
                prolific_id=participant.prolific_id,
                variant=participant.variant,
                created_at=get_singapore_time()
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        if record.completed_at is None:
            record.completed_at = get_singapore_time()
        if not record.created_at:
            record.created_at = get_singapore_time()
        if record.created_at and record.completed_at:
            created_at = ensure_singapore_tz(record.created_at)
            completed_at = ensure_singapore_tz(record.completed_at)
            if created_at and completed_at:
                delta = completed_at - created_at
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
