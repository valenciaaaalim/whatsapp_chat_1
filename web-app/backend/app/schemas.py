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
    question_order: Optional[int] = None  # Order of question in survey (1, 2, 3, ...)
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


class ParticipantCreateResponse(BaseModel):
    """Participant creation response."""
    id: int
    prolific_id: Optional[str]
    variant: str
    status: str  # 'new', 'existing', 'completed'
    completion_url: Optional[str] = None


# Completion schema
class CompletionRequest(BaseModel):
    """Completion request."""
    prolific_completion_code: Optional[str] = None


class ParticipantRecordMessage(BaseModel):
    """Record the final message for a conversation."""
    participant_id: str
    conversation_index: int
    final_message: str
    variant: Optional[str] = None


class ParticipantRecordPreSurvey(BaseModel):
    """Record pre-study survey (4 Likert items)."""
    participant_id: str
    answers: List[str] = Field(..., min_length=4, max_length=4)
    variant: Optional[str] = None


class ParticipantRecordMidSurveyA(BaseModel):
    """Record Variant A mid-survey (3 questions per conversation)."""
    participant_id: str
    conversation_index: int
    q1: str  # "The warning was clear."
    q2: str  # "The warning helped me notice something new."
    q3: str  # "The suggested rewrite preserved what I wanted to say."
    variant: Optional[str] = None


class ParticipantRecordMidSurveyB(BaseModel):
    """Record Variant B mid-survey (2 questions per conversation)."""
    participant_id: str
    conversation_index: int
    q1: str  # "Which type of personal information did you end up disclosing?" (multi-choice)
    q2: str  # "How likely is it that the other person was malicious?" (1–5)
    variant: Optional[str] = None


class ParticipantRecordSus(BaseModel):
    """Record SUS answers (10 questions)."""
    participant_id: str
    answers: List[str] = Field(..., min_length=10, max_length=10)
    variant: Optional[str] = None


class ParticipantRecordPostExtra(BaseModel):
    """Record post-survey extra questions for Variant A (2 questions)."""
    participant_id: str
    trust: str  # "Overall, I trusted the information presented by the system/interface." (1–5 Likert scale)
    realism: str  # "Overall, the study tasks felt realistic." (1–5 Likert scale)
    variant: Optional[str] = None
