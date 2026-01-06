"""
Participant management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Participant, ParticipantRecord
from app.schemas import ParticipantCreate, ParticipantSchema, ParticipantCreateResponse
from app.config import settings
from app.utils import get_singapore_time
import random
from urllib.parse import urlencode

router = APIRouter(prefix="/api/participants", tags=["participants"])


def assign_variant(db: Session) -> str:
    """
    Assign participant to variant A or B, alternating between A and B.
    """
    # Get the last participant's variant to alternate
    last_participant = db.query(Participant).order_by(Participant.id.desc()).first()
    
    if not last_participant:
        # First participant gets A
        return "A"
    
    # Alternate: if last was A, assign B; if last was B, assign A
    return "B" if last_participant.variant == "A" else "A"

def build_completion_url(prolific_id: str | None) -> str:
    """Build the Prolific completion URL for a participant."""
    base_url = settings.PROLIFIC_COMPLETION_URL
    params = {}
    if prolific_id:
        params["PROLIFIC_PID"] = prolific_id
    if params:
        return f"{base_url}?{urlencode(params)}"
    return base_url


@router.post("", response_model=ParticipantCreateResponse)
def create_participant(
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db)
):
    """Create a new participant and assign to variant A or B."""
    # Check if participant already exists (by prolific_id if provided, or by any existing record if prolific_id is None)
    if participant_data.prolific_id:
        existing = db.query(Participant).filter(
            Participant.prolific_id == participant_data.prolific_id
        ).first()
        if existing:
            status = "completed" if existing.completed_at else "existing"
            completion_url = build_completion_url(existing.prolific_id) if existing.completed_at else None
            return ParticipantCreateResponse(
                id=existing.id,
                prolific_id=existing.prolific_id,
                variant=existing.variant,
                status=status,
                completion_url=completion_url
            )
    else:
        # If no prolific_id provided, don't create duplicate participants
        # This prevents creating multiple participants with null prolific_id
        raise HTTPException(
            status_code=400, 
            detail="prolific_id is required. Please provide PROLIFIC_PID in URL or ensure prolific_id is set."
        )
    
    # Assign variant
    variant = assign_variant(db)
    
    # Create participant
    participant = Participant(
        prolific_id=participant_data.prolific_id,
        variant=variant
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    
    # Create corresponding participant_record entry (empty record, will be filled as they progress)
    if participant.prolific_id:
        existing_record = db.query(ParticipantRecord).filter(
            ParticipantRecord.prolific_id == participant.prolific_id
        ).first()
        if not existing_record:
            # Set created_at to Singapore time explicitly
            record = ParticipantRecord(
                prolific_id=participant.prolific_id,
                variant=variant,
                created_at=get_singapore_time()
            )
            db.add(record)
            db.commit()
    
    return ParticipantCreateResponse(
        id=participant.id,
        prolific_id=participant.prolific_id,
        variant=participant.variant,
        status="new",
        completion_url=None
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
    return ParticipantSchema.from_orm(participant)
