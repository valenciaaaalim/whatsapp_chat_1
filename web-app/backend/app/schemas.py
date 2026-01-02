"""
Pydantic schemas for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# Conversation schemas
class MessageSchema(BaseModel):
    """Message schema."""
    id: str
    text: str
    direction: str  # 'SENT' or 'RECEIVED'
    name: Optional[str] = None
    timestamp: Optional[datetime] = None


class ConversationSchema(BaseModel):
    """Conversation schema."""
    conversation_id: int
    scenario: str
    conversation: List[MessageSchema]
    ground_truth: Dict[str, Any]


# Session schemas
class ConversationSessionSchema(BaseModel):
    """Conversation session schema."""
    id: int
    conversation_id: int
    scenario: str
    current_message_index: int
    completed: bool

    class Config:
        from_attributes = True


# Risk assessment schemas
class RiskAssessmentRequest(BaseModel):
    """Risk assessment request."""
    draft_text: str = Field(..., min_length=1)
    conversation_history: List[str] = Field(default_factory=list)
    session_id: int


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH'
    explanation: str
    safer_rewrite: str
    show_warning: bool
    primary_risk_factors: List[str] = Field(default_factory=list)


# User input schemas
class UserInputCapture(BaseModel):
    """User input capture."""
    session_id: int
    message_index: int
    action_type: str  # 'rewrite' or 'ignore'
    pre_click_text: str
    final_submitted_text: str
    risk_level: Optional[str] = None
    warning_explanation: Optional[str] = None
    safer_rewrite_offered: Optional[str] = None


# Survey schemas
class SurveyQuestion(BaseModel):
    """Survey question."""
    question_id: str
    question_text: str
    question_type: str  # 'text', 'multiple_choice', 'rating', etc.
    options: Optional[List[str]] = None


class SurveyResponseSchema(BaseModel):
    """Survey response."""
    survey_type: str  # 'pre', 'mid', 'post', 'comprehension'
    question_id: str
    question_text: str
    response_text: Optional[str] = None
    response_json: Optional[Dict[str, Any]] = None


# Participant schemas
class ParticipantCreate(BaseModel):
    """Participant creation."""
    prolific_id: Optional[str] = None


class ParticipantSchema(BaseModel):
    """Participant schema."""
    id: int
    prolific_id: Optional[str]
    variant: str  # 'A' or 'B'

    class Config:
        from_attributes = True


# Completion schema
class CompletionRequest(BaseModel):
    """Completion request."""
    prolific_completion_code: Optional[str] = None

