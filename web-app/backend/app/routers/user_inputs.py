"""
User input capture routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserInput, ConversationSession
from app.schemas import UserInputCapture

router = APIRouter(prefix="/api/user-inputs", tags=["user-inputs"])


@router.post("")
def capture_user_input(
    input_data: UserInputCapture,
    db: Session = Depends(get_db)
):
    """Capture user input (pre-click and final submitted text)."""
    # Verify session exists
    session = db.query(ConversationSession).filter(
        ConversationSession.id == input_data.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create user input record
    user_input = UserInput(
        session_id=input_data.session_id,
        message_index=input_data.message_index,
        action_type=input_data.action_type,
        pre_click_text=input_data.pre_click_text,
        final_submitted_text=input_data.final_submitted_text
    )
    db.add(user_input)
    db.commit()
    db.refresh(user_input)
    
    return {"id": user_input.id, "status": "captured"}


@router.post("/with-warning")
def capture_user_input_with_warning(
    input_data: UserInputCapture,
    db: Session = Depends(get_db)
):
    """Capture user input along with warning information."""
    # Verify session exists
    session = db.query(ConversationSession).filter(
        ConversationSession.id == input_data.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create user input record with warning data
    user_input = UserInput(
        session_id=input_data.session_id,
        message_index=input_data.message_index,
        action_type=input_data.action_type,
        pre_click_text=input_data.pre_click_text,
        final_submitted_text=input_data.final_submitted_text,
        warning_shown=True,
        risk_level=input_data.risk_level,
        warning_explanation=input_data.warning_explanation,
        safer_rewrite_offered=input_data.safer_rewrite_offered
    )
    db.add(user_input)
    db.commit()
    db.refresh(user_input)
    
    return {"id": user_input.id, "status": "captured"}

