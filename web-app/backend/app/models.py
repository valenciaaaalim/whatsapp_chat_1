"""
Database models for the web app.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.utils import get_singapore_time
import json


class Participant(Base):
    """Participant/user model."""
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    prolific_id = Column(String, unique=True, index=True, nullable=True)
    variant = Column(String, nullable=False)  # 'A' or 'B'
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_singapore_time)
    updated_at = Column(DateTime(timezone=True), default=get_singapore_time, onupdate=get_singapore_time)
    
    # Relationships
    conversations = relationship("ConversationSession", back_populates="participant", cascade="all, delete-orphan")
    survey_responses = relationship("SurveyResponse", back_populates="participant", cascade="all, delete-orphan")


class ConversationSession(Base):
    """Conversation session model - represents one of the three test conversations."""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    prolific_id = Column(String, nullable=True, index=True)  # Store prolific_id for easier querying
    conversation_id = Column(Integer, nullable=False)  # 1000, 1001, or 1002 from annotated_test.json
    scenario = Column(String, nullable=False)  # e.g., "Academic Collaboration"
    current_message_index = Column(Integer, default=0)  # Track progress through conversation
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    participant = relationship("Participant", back_populates="conversations")
    user_inputs = relationship("UserInput", back_populates="session", cascade="all, delete-orphan")


class UserInput(Base):
    """User input capture - stores text before Rewrite/Ignore and final submitted text."""
    __tablename__ = "user_inputs (ignore)"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conversation_sessions.id"), nullable=False)
    message_index = Column(Integer, nullable=False)  # Which message in the conversation
    action_type = Column(String, nullable=False)  # 'rewrite' or 'ignore'
    
    # Input capture
    pre_click_text = Column(Text, nullable=True)  # Text before clicking Rewrite/Ignore
    final_submitted_text = Column(Text, nullable=True)  # Final text that was submitted
    
    # Warning data
    warning_shown = Column(Boolean, default=False)
    risk_level = Column(String, nullable=True)  # 'LOW', 'MEDIUM', 'HIGH'
    warning_explanation = Column(Text, nullable=True)
    safer_rewrite_offered = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ConversationSession", back_populates="user_inputs")


class SurveyResponse(Base):
    """Survey response model."""
    __tablename__ = "survey_responses"
    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "survey_type",
            "question_id",
            name="uq_survey_response_participant_type_question"
        ),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    prolific_id = Column(String, nullable=True, index=True)  # Store prolific_id for easier querying
    question_order = Column(Integer, nullable=True)  # Store question order (1, 2, 3, ...) for sorting
    survey_type = Column(String, nullable=False)  # 'pre', 'mid', 'post', 'comprehension'
    question_id = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    response_json = Column(JSON, nullable=True)  # For structured responses
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    participant = relationship("Participant", back_populates="survey_responses")


class Conversation(Base):
    """Seed conversation data from annotated_test.json."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, unique=True, nullable=False, index=True)  # 1000, 1001, 1002
    scenario = Column(String, nullable=False)
    conversation_data = Column(JSON, nullable=False)  # Full conversation JSON
    ground_truth = Column(JSON, nullable=False)  # Ground truth data
    is_malicious = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Audit log for analytics and tracking."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=True)
    event_type = Column(String, nullable=False)  # 'conversation_start', 'input_capture', 'survey_response', etc.
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ParticipantRecord(Base):
    """Flattened participant response record for analysis/export."""
    __tablename__ = "participant_records"

    prolific_id = Column(String, primary_key=True)
    variant = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_singapore_time)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_of_study = Column(Float, nullable=True)

    # Pre-study survey (both variants) - 4 Likert items about confidence and familiarity
    pre_1 = Column(Text, nullable=True)
    pre_2 = Column(Text, nullable=True)
    pre_3 = Column(Text, nullable=True)
    pre_4 = Column(Text, nullable=True)

    # Conversation data
    input_1 = Column(Text, nullable=True)
    msg_1 = Column(Text, nullable=True)
    input_2 = Column(Text, nullable=True)
    msg_2 = Column(Text, nullable=True)
    input_3 = Column(Text, nullable=True)
    msg_3 = Column(Text, nullable=True)

    # Variant A mid-survey (3 questions × 3 conversations)
    # Conversation 1
    midA_1_q1 = Column(Text, nullable=True)  # "The warning was clear."
    midA_1_q2 = Column(Text, nullable=True)  # "The warning helped me notice something new."
    midA_1_q3 = Column(Text, nullable=True)  # "The suggested rewrite preserved what I wanted to say."
    # Conversation 2
    midA_2_q1 = Column(Text, nullable=True)
    midA_2_q2 = Column(Text, nullable=True)
    midA_2_q3 = Column(Text, nullable=True)
    # Conversation 3
    midA_3_q1 = Column(Text, nullable=True)
    midA_3_q2 = Column(Text, nullable=True)
    midA_3_q3 = Column(Text, nullable=True)

    # Variant B mid-survey (3 questions × 3 conversations)
    # Conversation 1
    midB_1_q1 = Column(Text, nullable=True)  # "Which type of personal information did you end up disclosing?" (multi-choice)
    midB_1_q2 = Column(Text, nullable=True)  # "How likely is it that the other person was malicious?" (1–5)
    midB_1_q3 = Column(Text, nullable=True)  # "How important was the personal information?" (1–5)
    # Conversation 2
    midB_2_q1 = Column(Text, nullable=True)
    midB_2_q2 = Column(Text, nullable=True)
    midB_2_q3 = Column(Text, nullable=True)
    # Conversation 3
    midB_3_q1 = Column(Text, nullable=True)
    midB_3_q2 = Column(Text, nullable=True)
    midB_3_q3 = Column(Text, nullable=True)

    # Post-survey: SUS questions (Variant A only)
    sus_1 = Column(Text, nullable=True)
    sus_2 = Column(Text, nullable=True)
    sus_3 = Column(Text, nullable=True)
    sus_4 = Column(Text, nullable=True)
    sus_5 = Column(Text, nullable=True)
    sus_6 = Column(Text, nullable=True)
    sus_7 = Column(Text, nullable=True)
    sus_8 = Column(Text, nullable=True)
    sus_9 = Column(Text, nullable=True)
    sus_10 = Column(Text, nullable=True)

    # Post-survey: Extra questions (Variant A only)
    post_trust = Column(Text, nullable=True)  # "Overall, I trusted the information presented by the system/interface." (1–5 Likert scale)
    post_realism = Column(Text, nullable=True)  # "Overall, the study tasks felt realistic." (1–5 Likert scale)
