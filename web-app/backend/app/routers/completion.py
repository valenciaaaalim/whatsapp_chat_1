"""
Completion URL routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant
from app.participant_state import sync_participant_completion_state
from app.config import settings
from app.routers.participants import build_completion_url
from app.routers.participant_data import build_participant_progress_response, _verify_session_token
from app.utils import require_mobile_request

router = APIRouter(prefix="/api/completion", tags=["completion"])


@router.get("/prolific")
def get_prolific_completion_url(
    request: Request,
    participant_id: int | None = None,
    prolific_id: str | None = None,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Return the Prolific completion URL only when completion is unlocked."""
    require_mobile_request(request)
    participant = None
    if participant_id is not None:
        participant = db.query(Participant).filter(Participant.id == participant_id).first()
    elif prolific_id:
        participant = db.query(Participant).filter(Participant.prolific_id == prolific_id).first()
    else:
        raise HTTPException(
            status_code=400,
            detail="participant_id or prolific_id is required",
        )

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=False)
    progress = build_participant_progress_response(db, participant)
    if not progress.completion_unlocked:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )

    url = build_completion_url(participant.prolific_id)
    code = settings.COMPLETION_CODE or None
    return {
        "completion_url": url or None,
        "completion_code": code,
    }
