"""
Participant management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Participant
from app.schemas import ParticipantCreate, ParticipantSchema
import random

router = APIRouter(prefix="/api/participants", tags=["participants"])


def assign_variant(db: Session) -> str:
    """
    Assign participant to variant A or B, balancing groups.
    """
    # Count current assignments
    count_a = db.query(func.count(Participant.id)).filter(Participant.variant == "A").scalar() or 0
    count_b = db.query(func.count(Participant.id)).filter(Participant.variant == "B").scalar() or 0
    
    # Balance assignment
    if count_a <= count_b:
        return "A"
    else:
        return "B"


@router.post("", response_model=ParticipantSchema)
def create_participant(
    participant_data: ParticipantCreate,
    db: Session = Depends(get_db)
):
    """Create a new participant and assign to variant A or B."""
    # Check if participant already exists
    if participant_data.prolific_id:
        existing = db.query(Participant).filter(
            Participant.prolific_id == participant_data.prolific_id
        ).first()
        if existing:
            return ParticipantSchema.from_orm(existing)
    
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
    
    return ParticipantSchema.from_orm(participant)


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

