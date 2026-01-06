"""
Flattened participant record routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Participant, ParticipantRecord
from app.schemas import (
    ParticipantRecordMessage,
    ParticipantRecordPreSurvey,
    ParticipantRecordMidSurveyA,
    ParticipantRecordMidSurveyB,
    ParticipantRecordSus,
    ParticipantRecordPostExtra
)

router = APIRouter(prefix="/api/participant-records", tags=["participant-records"])


def get_or_create_record(
    db: Session,
    participant_id: str,
    variant: str | None = None
) -> ParticipantRecord:
    record = db.query(ParticipantRecord).filter(
        ParticipantRecord.prolific_id == participant_id
    ).first()
    if record:
        if variant and not record.variant:
            record.variant = variant
            db.commit()
        return record
    record = ParticipantRecord(prolific_id=participant_id, variant=variant)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/message")
def record_final_message(
    payload: ParticipantRecordMessage,
    db: Session = Depends(get_db)
):
    if payload.conversation_index not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="Invalid conversation index")

    record = get_or_create_record(db, payload.participant_id, payload.variant)
    slot = payload.conversation_index + 1
    setattr(record, f"msg_{slot}", payload.final_message)
    db.commit()

    return {"status": "saved"}


@router.post("/pre-survey")
def record_pre_survey(
    payload: ParticipantRecordPreSurvey,
    db: Session = Depends(get_db)
):
    """Record pre-study survey (4 Likert items) - both variants."""
    # Ensure we have exactly 4 answers
    if len(payload.answers) != 4:
        raise HTTPException(status_code=400, detail=f"Expected 4 pre-survey answers, got {len(payload.answers)}")
    
    record = get_or_create_record(db, payload.participant_id, payload.variant)
    for idx, answer in enumerate(payload.answers, start=1):
        setattr(record, f"pre_{idx}", answer)
    db.commit()
    return {"status": "saved"}


@router.post("/mid-survey-a")
def record_mid_survey_a(
    payload: ParticipantRecordMidSurveyA,
    db: Session = Depends(get_db)
):
    """Record Variant A mid-survey (3 questions per conversation)."""
    if payload.conversation_index not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="Invalid conversation index")

    record = get_or_create_record(db, payload.participant_id, payload.variant)
    slot = payload.conversation_index + 1
    setattr(record, f"midA_{slot}_q1", payload.q1)
    setattr(record, f"midA_{slot}_q2", payload.q2)
    setattr(record, f"midA_{slot}_q3", payload.q3)
    db.commit()

    return {"status": "saved"}


@router.post("/mid-survey-b")
def record_mid_survey_b(
    payload: ParticipantRecordMidSurveyB,
    db: Session = Depends(get_db)
):
    """Record Variant B mid-survey (2 questions per conversation)."""
    if payload.conversation_index not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="Invalid conversation index")

    record = get_or_create_record(db, payload.participant_id, payload.variant)
    slot = payload.conversation_index + 1
    setattr(record, f"midB_{slot}_q1", payload.q1)
    setattr(record, f"midB_{slot}_q2", payload.q2)
    db.commit()

    return {"status": "saved"}


@router.post("/sus")
def record_sus(
    payload: ParticipantRecordSus,
    db: Session = Depends(get_db)
):
    """Record SUS answers (10 questions) - Variant A only."""
    participant = db.query(Participant).filter(
        Participant.prolific_id == payload.participant_id
    ).first()
    
    # Allow if participant not found (for local testing) or if variant is A
    if participant and participant.variant != "A":
        return {"status": "skipped", "message": "SUS survey is only for Variant A"}

    # Get variant from participant if found, otherwise use payload variant
    variant = participant.variant if participant else (payload.variant or "A")
    record = get_or_create_record(db, payload.participant_id, variant)
    
    if len(payload.answers) != 10:
        raise HTTPException(status_code=400, detail=f"Expected 10 SUS answers, got {len(payload.answers)}")
    
    for idx, answer in enumerate(payload.answers, start=1):
        setattr(record, f"sus_{idx}", answer)
    db.commit()

    return {"status": "saved"}


@router.post("/post-extra")
def record_post_extra(
    payload: ParticipantRecordPostExtra,
    db: Session = Depends(get_db)
):
    """Record post-survey extra questions (2 questions) - Variant A only."""
    participant = db.query(Participant).filter(
        Participant.prolific_id == payload.participant_id
    ).first()
    
    # Allow if participant not found (for local testing) or if variant is A
    if participant and participant.variant != "A":
        return {"status": "skipped", "message": "Post-survey extra questions are only for Variant A"}

    # Get variant from participant if found, otherwise use payload variant
    variant = participant.variant if participant else (payload.variant or "A")
    record = get_or_create_record(db, payload.participant_id, variant)
    
    if not payload.trust or not payload.realism:
        raise HTTPException(status_code=400, detail="Both trust and realism answers are required")
    
    record.post_trust = payload.trust
    record.post_realism = payload.realism
    db.commit()

    return {"status": "saved"}
