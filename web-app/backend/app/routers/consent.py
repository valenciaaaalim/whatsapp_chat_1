"""
Consent logging routes.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ConsentDecision, Participant
from app.schemas import ConsentDecisionCreate, ConsentDecisionResponse
from app.utils import get_singapore_time, require_mobile_request
from app.participant_state import is_completed_state

router = APIRouter(prefix="/api/consent", tags=["consent"])


@router.post("", response_model=ConsentDecisionResponse)
def log_consent(
    request: Request,
    payload: ConsentDecisionCreate,
    db: Session = Depends(get_db)
):
    """Log consent decision (yes/no) with UTC timestamp."""
    require_mobile_request(request)
    prolific_id = (payload.prolific_id or payload.participant_platform_id or "").strip() or None
    if not prolific_id:
        raise HTTPException(status_code=400, detail="prolific_id is required for consent logging")
    participant = db.query(Participant).filter(
        Participant.prolific_id == prolific_id
    ).first()
    if participant is None:
        raise HTTPException(status_code=404, detail="Participant must exist before consent is logged")
    participant_variant = participant.variant

    decision = ConsentDecision(
        prolific_id=prolific_id,
        consent=payload.consent,
        timestamp_utc=datetime.now(timezone.utc),
        participant_variant=participant_variant,
    )
    db.add(decision)

    # Align participant "start time" with explicit consent-continue action.
    if payload.consent == "yes":
        if participant is not None and not is_completed_state(participant.is_complete):
            if participant.created_at is None:
                participant.created_at = get_singapore_time().replace(microsecond=0)

    db.commit()
    return ConsentDecisionResponse(status="logged")
