"""
Database models for the web app.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import json


class Participant(Base):
    """Participant/user model."""
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True, index=True)
    prolific_id = Column(String, unique=True, index=True, nullable=True)
    variant = Column(String, nullable=False)  # 'A' or 'B'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversations = relationship("ConversationSession", back_populates="participant", cascade="all, delete-orphan")
    survey_responses = relationship("SurveyResponse", back_populates="participant", cascade="all, delete-orphan")


class ConversationSession(Base):
    """Conversation session model - represents one of the three test conversations."""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
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
    __tablename__ = "user_inputs"
    
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
    
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
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
    conversation_id = Column(Integer, unique=True, nullable=False)  # 1000, 1001, 1002
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

