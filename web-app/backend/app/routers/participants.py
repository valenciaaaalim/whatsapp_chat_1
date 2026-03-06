"""
Participant management routes.
"""
import random
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant
from app.schemas import ParticipantCreate, ParticipantSchema, ParticipantCreateResponse
from app.config import settings
from app.utils import get_singapore_time, require_mobile_request
from app.participant_state import sync_participant_completion_state, is_completed_state

router = APIRouter(prefix="/api/participants", tags=["participants"])


def assign_variant(db: Session) -> str:
    """
    Assign participant to variant A or B randomly.
    """
    return random.choice(["A", "B"])


def build_completion_url(prolific_id: str | None) -> str:
    """Build the Prolific completion URL for a participant."""
    # Prefer COMPLETION_URL / COMPLETION_CODE env vars over legacy PROLIFIC_COMPLETION_URL
    if settings.COMPLETION_URL:
        url = settings.COMPLETION_URL.strip()
        if settings.COMPLETION_CODE and "cc=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}cc={settings.COMPLETION_CODE.strip()}"
        return url
    base_url = (settings.PROLIFIC_COMPLETION_URL or "").strip()
    return base_url


@router.post("", response_model=ParticipantCreateResponse)
def create_participant(
    request: Request,
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db),
):
    """Create a new participant and assign to variant A or B."""
    require_mobile_request(request)

    # Check if participant already exists (by prolific_id if provided)
    if participant_data.prolific_id:
        existing = db.query(Participant).filter(
            Participant.prolific_id == participant_data.prolific_id
        ).first()
        if existing:
            existing = sync_participant_completion_state(db, existing, mark_active=True)
            completed = is_completed_state(existing.is_complete)
            status = "completed" if completed else "existing"
            completion_url = build_completion_url(existing.prolific_id) if completed else None
            # Rotate session token so the new tab/device gets the active session
            new_token = secrets.token_urlsafe(32)
            existing.session_token = new_token
            db.add(existing)
            db.commit()
            return ParticipantCreateResponse(
                id=existing.id,
                prolific_id=existing.prolific_id,
                variant=existing.variant,
                status=status,
                completion_url=completion_url,
                session_token=new_token,
            )
    else:
        # If no prolific_id provided, don't create duplicate participants
        raise HTTPException(
            status_code=400,
            detail="prolific_id is required. Please provide PROLIFIC_PID in URL or ensure prolific_id is set."
        )

    # Assign variant
    variant = assign_variant(db)

    # Create participant
    now_sgt = get_singapore_time()
    session_token = secrets.token_urlsafe(32)
    participant = Participant(
        prolific_id=participant_data.prolific_id,
        variant=variant,
        participant_variant=variant,
        created_at=now_sgt,
        is_complete="Progress",
        session_token=session_token,
    )
    db.add(participant)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Participant).filter(
            Participant.prolific_id == participant_data.prolific_id
        ).first()
        if existing:
            existing = sync_participant_completion_state(db, existing, mark_active=True)
            completed = is_completed_state(existing.is_complete)
            status = "completed" if completed else "existing"
            completion_url = build_completion_url(existing.prolific_id) if completed else None
            new_token = secrets.token_urlsafe(32)
            existing.session_token = new_token
            db.add(existing)
            db.commit()
            return ParticipantCreateResponse(
                id=existing.id,
                prolific_id=existing.prolific_id,
                variant=existing.variant,
                status=status,
                completion_url=completion_url,
                session_token=new_token,
            )
        raise
    db.refresh(participant)

    return ParticipantCreateResponse(
        id=participant.id,
        prolific_id=participant.prolific_id,
        variant=participant.variant,
        status="new",
        completion_url=None,
        session_token=session_token,
    )


@router.get("/{participant_id}", response_model=ParticipantSchema)
def get_participant(
    participant_id: int,
    db: Session = Depends(get_db)
):
    """Get participant by ID."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    participant = sync_participant_completion_state(db, participant, mark_active=False)
    return ParticipantSchema.model_validate(participant)


@router.get("/by-prolific/{prolific_id}", response_model=ParticipantSchema)
def get_participant_by_prolific_id(
    prolific_id: str,
    db: Session = Depends(get_db)
):
    """Get participant by Prolific ID."""
    participant = db.query(Participant).filter(Participant.prolific_id == prolific_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    participant = sync_participant_completion_state(db, participant, mark_active=False)
    return ParticipantSchema.model_validate(participant)
