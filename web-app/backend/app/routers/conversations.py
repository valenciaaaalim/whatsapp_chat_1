"""
Conversation routes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Conversation, ConversationSession, Participant
from app.schemas import ConversationSchema, ConversationSessionSchema

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/seed", response_model=List[ConversationSchema])
def get_seed_conversations(db: Session = Depends(get_db)):
    """Get all seed conversations."""
    conversations = db.query(Conversation).all()
    result = []
    for conv in conversations:
        # Parse conversation data
        conv_data = conv.conversation_data
        messages = []
        conv_list = conv_data.get("Conversation", [])
        if not conv_list:
            return []
        
        # First name in conversation is the contact (we receive their messages)
        first_name = conv_list[0].get("Name", "")
        
        for i, msg in enumerate(conv_list):
            name = msg.get("Name", "")
            # Messages from first_name are received (contact), others are sent (user)
            direction = "RECEIVED" if name == first_name else "SENT"
            messages.append({
                "id": str(i),
                "text": msg["Message"],
                "direction": direction,
                "name": name,
                "timestamp": None
            })
        result.append(ConversationSchema(
            conversation_id=conv.conversation_id,
            scenario=conv.scenario,
            conversation=messages,
            ground_truth=conv.ground_truth
        ))
    return result


@router.get("/seed/{conversation_id}", response_model=ConversationSchema)
def get_seed_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get a specific seed conversation."""
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv_data = conv.conversation_data
    messages = []
    conv_list = conv_data.get("Conversation", [])
    if not conv_list:
        raise HTTPException(status_code=404, detail="Conversation has no messages")
    
    # First name in conversation is the contact (we receive their messages)
    first_name = conv_list[0].get("Name", "")
    
    for i, msg in enumerate(conv_list):
        name = msg.get("Name", "")
        # Messages from first_name are received (contact), others are sent (user)
        direction = "RECEIVED" if name == first_name else "SENT"
        messages.append({
            "id": str(i),
            "text": msg["Message"],
            "direction": direction,
            "name": name,
            "timestamp": None
        })
    return ConversationSchema(
        conversation_id=conv.conversation_id,
        scenario=conv.scenario,
        conversation=messages,
        ground_truth=conv.ground_truth
    )


@router.post("/sessions/{participant_id}/{conversation_id}", response_model=ConversationSessionSchema)
def create_session(
    participant_id: int,
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Create a new conversation session for a participant."""
    # Verify participant exists
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Verify conversation exists
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if session already exists
    existing = db.query(ConversationSession).filter(
        ConversationSession.participant_id == participant_id,
        ConversationSession.conversation_id == conversation_id
    ).first()
    if existing:
        return ConversationSessionSchema.from_orm(existing)
    
    # Create new session
    session = ConversationSession(
        participant_id=participant_id,
        prolific_id=participant.prolific_id,  # Store prolific_id for easier querying
        conversation_id=conversation_id,
        scenario=conv.scenario,
        current_message_index=0,
        completed=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ConversationSessionSchema.from_orm(session)


@router.get("/sessions/{session_id}", response_model=ConversationSessionSchema)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a conversation session."""
    session = db.query(ConversationSession).filter(
        ConversationSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ConversationSessionSchema.from_orm(session)


@router.patch("/sessions/{session_id}/complete")
def complete_session(session_id: int, db: Session = Depends(get_db)):
    """Mark a conversation session as completed."""
    session = db.query(ConversationSession).filter(
        ConversationSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.completed = True
    db.commit()
    
    return {"status": "completed"}

