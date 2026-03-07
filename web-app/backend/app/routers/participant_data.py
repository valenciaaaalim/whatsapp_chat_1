"""
Normalized participant data routes.
All endpoints write to normalized study tables.
"""
import logging
import json
from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.database import get_db
from app.models import (
    Participant,
    BaselineAssessment,
    ScenarioResponse,
    PostScenarioSurvey,
    SusResponse,
    EndOfStudySurvey,
    LLMOutput,
)
from app.schemas import (
    BaselineAssessmentCreate,
    BaselineAssessmentResponse,
    AlertInteractionStartRequest,
    AlertInteractionCompleteRequest,
    AlertInteractionDecisionRequest,
    ScenarioResponseCreate,
    ScenarioResponseSchema,
    ScenarioMessageRecord,
    PostScenarioSurveyCreate,
    PostScenarioSurveySchema,
    SusResponseCreate,
    SusResponseSchema,
    EndOfStudySurveyCreate,
    EndOfStudySurveySchema,
    ParticipantDataResponse,
    ParticipantSchema,
    ParticipantProgressResponse,
)
from app.utils import ensure_singapore_tz, get_singapore_time, require_mobile_request
from app.scenario_counters import allocate_alert_round
from app.participant_state import (
    sync_participant_completion_state,
    is_completed_state,
    COMPLETE_STATE_TRUE,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/participants", tags=["participant-data"])

MARKER_ABORT = "[ABORT]"
MARKER_DNI = "[DNI]"
MARKER_FALSE = "[FALSE]"
MARKER_TRUE = "[TRUE]"
MARKER_B = "[B]"
STATUS_PENDING = "[PENDING]"
STATUS_COMPLETE = "[COMPLETE]"
STATUS_ABORT = "[ABORT]"
STATUS_DNI = "[DNI]"
STATUS_B = "[B]"
END_OF_STUDY_MIN_WORDS = 15
MARKER_NO_SHOW = "[NO SHOW]"


def calculate_sus_score(sus_1, sus_2, sus_3, sus_4, sus_5, sus_6, sus_7, sus_8, sus_9, sus_10):
    """
    Calculate SUS score from 10 SUS items.
    Odd items (1,3,5,7,9): score = value - 1
    Even items (2,4,6,8,10): score = 5 - value
    Final score = sum of all scores * 2.5
    """
    scores = [
        sus_1 - 1,      # sus_1 (odd)
        5 - sus_2,      # sus_2 (even)
        sus_3 - 1,      # sus_3 (odd)
        5 - sus_4,      # sus_4 (even)
        sus_5 - 1,      # sus_5 (odd)
        5 - sus_6,      # sus_6 (even)
        sus_7 - 1,      # sus_7 (odd)
        5 - sus_8,      # sus_8 (even)
        sus_9 - 1,      # sus_9 (odd)
        5 - sus_10      # sus_10 (even)
    ]
    total = sum(scores)
    sus_score = total * 2.5
    return round(sus_score, 2)


def get_participant_by_id(db: Session, participant_id: int) -> Participant:
    """Get participant by ID or raise 404."""
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return sync_participant_completion_state(db, participant, mark_active=False)


def get_participant_by_prolific_id(db: Session, prolific_id: str) -> Participant:
    """Get participant by Prolific ID or raise 404."""
    participant = db.query(Participant).filter(Participant.prolific_id == prolific_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return sync_participant_completion_state(db, participant, mark_active=False)


def _verify_session_token(participant: Participant, session_token: Optional[str]) -> None:
    """Reject stale tabs/devices when session token is present on the participant."""
    if participant.session_token is None:
        return  # Legacy participant without token — allow
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Session token required. Please refresh to continue.",
        )
    if participant.session_token != session_token:
        raise HTTPException(
            status_code=401,
            detail="Session invalidated. Another tab or device started a new session. Please refresh.",
        )


def _is_variant_b(variant: str | None) -> bool:
    """Return True when participant is variant B."""
    return (variant or "").strip().upper() == "B"


def _normalize_accepted_rewrite(value: Any, variant: str | None) -> str | None:
    """
    Normalize accepted_rewrite for storage:
    - Variant B => "[B]"
    - Variant A => "true" | "false" | "[ABORT]" | "[DNI]" | null
    """
    if _is_variant_b(variant):
        return MARKER_B
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return "true"
        if normalized == "false":
            return "false"
        if normalized == "abort":
            return MARKER_ABORT
        if normalized == "[abort]":
            return MARKER_ABORT
        if normalized == "dni":
            return MARKER_DNI
        if normalized == "[dni]":
            return MARKER_DNI
        if normalized in {"", "null", "none"}:
            return None
    return None


def _variant_a_only_value(value: Any, variant: str | None) -> Any:
    """Set Variant A-only fields to [B] for variant B participants."""
    if _is_variant_b(variant):
        return MARKER_B
    return value


def _normalize_string_field(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_token_field(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text in {MARKER_ABORT, MARKER_DNI, MARKER_B}:
        return 0
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


def _word_count(value: Any) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return len([part for part in text.split() if part])


def _final_message_is_actual(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text not in {"", MARKER_ABORT, MARKER_DNI, MARKER_FALSE}


def _resolve_scenario_llm_usage(
    db: Session,
    participant_id: int,
    scenario_number: int,
    output_id: str | None,
) -> str | None:
    from app.models import LLMOutput

    if output_id:
        match = db.query(LLMOutput.nth_call).filter(
            LLMOutput.participant_id == participant_id,
            LLMOutput.scenario_id == scenario_number,
            LLMOutput.output_id == output_id,
        ).order_by(LLMOutput.id.desc()).first()
        if match and match[0] is not None:
            return str(match[0])

    fallback = db.query(func.max(LLMOutput.nth_call)).filter(
        LLMOutput.participant_id == participant_id,
        LLMOutput.scenario_id == scenario_number,
    ).scalar()
    if fallback is None:
        return None
    return str(fallback)


def _mark_prior_complete_rows_false(
    db: Session,
    participant_id: int,
    scenario_number: int,
) -> None:
    db.query(ScenarioResponse).filter(
        ScenarioResponse.participant_id == participant_id,
        ScenarioResponse.scenario_number == scenario_number,
        ScenarioResponse.interaction_status == STATUS_COMPLETE,
        ScenarioResponse.is_final_submission_row != MARKER_TRUE,
        ScenarioResponse.final_message.is_(None),
    ).update(
        {
            ScenarioResponse.final_message: MARKER_FALSE,
            ScenarioResponse.is_final_submission_row: MARKER_FALSE,
        },
        synchronize_session=False,
    )


def _set_variant_a_marker_fields(row: ScenarioResponse, marker: str) -> None:
    row.original_input = marker
    row.masked_text = marker
    row.output_id = marker
    row.input_tokens = 0
    row.total_tokens = 0
    row.model = marker
    row.scenario_llm_usage = marker
    row.risk_level = marker
    row.reasoning = marker
    row.suggested_rewrite = marker
    row.primary_risk_factors = marker
    row.linkability_risk_level = marker
    row.linkability_risk_explanation = marker
    row.authentication_baiting_level = marker
    row.authentication_baiting_explanation = marker
    row.contextual_alignment_level = marker
    row.contextual_alignment_explanation = marker
    row.platform_trust_obligation_level = marker
    row.platform_trust_obligation_explanation = marker
    row.psychological_pressure_level = marker
    row.psychological_pressure_explanation = marker
    row.accepted_rewrite = marker


def _latest_scenario_response(
    db: Session,
    participant_id: int,
    scenario_number: int,
) -> ScenarioResponse | None:
    return db.query(ScenarioResponse).filter(
        ScenarioResponse.participant_id == participant_id,
        ScenarioResponse.scenario_number == scenario_number,
    ).order_by(
        ScenarioResponse.alert_round.desc().nullslast(),
        ScenarioResponse.id.desc(),
    ).first()


def _participant_saw_any_warning(db: Session, participant_id: int) -> bool:
    """Return True when the participant actually saw at least one completed warning output."""
    return db.query(ScenarioResponse.id).filter(
        ScenarioResponse.participant_id == participant_id,
        ScenarioResponse.interaction_status == STATUS_COMPLETE,
    ).first() is not None


def _participant_warning_scenarios(db: Session, participant_id: int) -> list[int]:
    """Return scenario numbers where the participant actually saw a completed warning output."""
    rows = db.query(ScenarioResponse.scenario_number).filter(
        ScenarioResponse.participant_id == participant_id,
        ScenarioResponse.interaction_status == STATUS_COMPLETE,
    ).distinct().all()
    return sorted(
        int(row[0]) for row in rows
        if row and row[0] is not None
    )


def build_participant_data_response(db: Session, participant: Participant) -> ParticipantDataResponse:
    """Build full normalized participant response payload."""
    participant_id = participant.id
    baseline_assessment = db.query(BaselineAssessment).filter(
        BaselineAssessment.participant_id == participant_id
    ).first()
    
    scenario_responses = db.query(ScenarioResponse).filter(
        ScenarioResponse.participant_id == participant_id
    ).order_by(
        ScenarioResponse.scenario_number,
        ScenarioResponse.alert_round,
        ScenarioResponse.id,
    ).all()
    
    post_scenario_surveys = db.query(PostScenarioSurvey).filter(
        PostScenarioSurvey.participant_id == participant_id
    ).order_by(PostScenarioSurvey.scenario_number).all()
    
    sus_responses = db.query(SusResponse).filter(
        SusResponse.participant_id == participant_id
    ).first()
    
    end_of_study_survey = db.query(EndOfStudySurvey).filter(
        EndOfStudySurvey.participant_id == participant_id
    ).first()
    
    return ParticipantDataResponse(
        participant=ParticipantSchema.model_validate(participant),
        baseline_assessment=BaselineAssessmentResponse.model_validate(baseline_assessment) if baseline_assessment else None,
        scenario_responses=[ScenarioResponseSchema.model_validate(sr) for sr in scenario_responses],
        post_scenario_surveys=[PostScenarioSurveySchema.model_validate(ps) for ps in post_scenario_surveys],
        sus_responses=SusResponseSchema.model_validate(sus_responses) if sus_responses else None,
        end_of_study_survey=EndOfStudySurveySchema.model_validate(end_of_study_survey) if end_of_study_survey else None
    )


def build_participant_progress_response(db: Session, participant: Participant) -> ParticipantProgressResponse:
    """Compute canonical progression state and redirect target for a participant."""
    participant_id = participant.id
    warning_scenarios = _participant_warning_scenarios(db, participant_id)
    saw_any_warning = bool(warning_scenarios)
    baseline_exists = db.query(BaselineAssessment.id).filter(
        BaselineAssessment.participant_id == participant_id
    ).first() is not None
    end_of_study_exists = db.query(EndOfStudySurvey.id).filter(
        EndOfStudySurvey.participant_id == participant_id
    ).first() is not None

    scenario_rows = db.query(
        ScenarioResponse.scenario_number,
        ScenarioResponse.final_message,
        ScenarioResponse.is_final_submission_row,
    ).filter(
        ScenarioResponse.participant_id == participant_id
    ).all()
    scenario_final_submitted = {
        int(row[0]) for row in scenario_rows
        if row[2] == MARKER_TRUE and _final_message_is_actual(row[1])
    }

    post_scenario_numbers = {
        int(row[0]) for row in db.query(PostScenarioSurvey.scenario_number).filter(
            PostScenarioSurvey.participant_id == participant_id
        ).all()
    }

    if is_completed_state(participant.is_complete) or participant.completed_at is not None or end_of_study_exists:
        return ParticipantProgressResponse(
            is_complete=True,
            max_conversation_index_unlocked=2,
            survey_unlocked=False,
            completion_unlocked=True,
            saw_any_warning=saw_any_warning,
            warning_scenarios=warning_scenarios,
            redirect_path="/completion",
            allowed_paths=["/completion"],
        )

    if not baseline_exists:
        return ParticipantProgressResponse(
            is_complete=False,
            max_conversation_index_unlocked=-1,
            survey_unlocked=True,
            completion_unlocked=False,
            saw_any_warning=saw_any_warning,
            warning_scenarios=warning_scenarios,
            redirect_path="/",
            allowed_paths=["/", "/survey/baseline"],
        )

    for scenario_number in (1, 2, 3):
        conversation_index = scenario_number - 1
        if scenario_number not in scenario_final_submitted:
            path = f"/conversation/{conversation_index}"
            return ParticipantProgressResponse(
                is_complete=False,
                max_conversation_index_unlocked=conversation_index,
                survey_unlocked=False,
                completion_unlocked=False,
                saw_any_warning=saw_any_warning,
                warning_scenarios=warning_scenarios,
                redirect_path=path,
                allowed_paths=[path],
            )
        if scenario_number not in post_scenario_numbers:
            mid_path = f"/survey/mid?index={conversation_index}"
            post_path = f"/survey/post-scenario?index={conversation_index}"
            return ParticipantProgressResponse(
                is_complete=False,
                max_conversation_index_unlocked=conversation_index,
                survey_unlocked=True,
                completion_unlocked=False,
                saw_any_warning=saw_any_warning,
                warning_scenarios=warning_scenarios,
                redirect_path=mid_path,
                allowed_paths=[mid_path, post_path],
            )

    return ParticipantProgressResponse(
        is_complete=False,
        max_conversation_index_unlocked=2,
        survey_unlocked=True,
        completion_unlocked=False,
        saw_any_warning=saw_any_warning,
        warning_scenarios=warning_scenarios,
        redirect_path="/survey/end-of-study",
        allowed_paths=["/survey/end-of-study", "/survey/post"],
    )


# =============================================================================
# Baseline Assessment endpoints (Table 2)
# =============================================================================
@router.post("/{participant_id}/baseline-assessment", response_model=BaselineAssessmentResponse)
def create_baseline_assessment(
    request: Request,
    participant_id: int,
    data: BaselineAssessmentCreate,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Create baseline self-assessment for a participant."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    progress = build_participant_progress_response(db, participant)
    if progress.redirect_path not in {"/", "/survey/baseline"}:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )
    
    # Check if baseline assessment already exists
    existing = db.query(BaselineAssessment).filter(
        BaselineAssessment.participant_id == participant_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Baseline assessment already exists")
    
    baseline = BaselineAssessment(
        participant_id=participant_id,
        recognize_sensitive=data.recognize_sensitive,
        avoid_accidental=data.avoid_accidental,
        familiar_scams=data.familiar_scams,
        contextual_judgment=data.contextual_judgment,
        participant_variant=participant.variant,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    
    return baseline


# =============================================================================
# Scenario Response endpoints (Table 3)
# =============================================================================
@router.post("/{participant_id}/alert-interactions/start", response_model=ScenarioResponseSchema)
def start_alert_interaction(
    request: Request,
    participant_id: int,
    data: AlertInteractionStartRequest,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Create a new Variant A interaction-log row for an alert button click."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    if _is_variant_b(participant.variant):
        raise HTTPException(status_code=400, detail="Alert interactions are only for Group A participants")

    scenario_number = data.scenario_number
    progress = build_participant_progress_response(db, participant)
    expected_path = f"/conversation/{scenario_number - 1}"
    if progress.redirect_path != expected_path:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )

    if db.query(PostScenarioSurvey.id).filter(
        PostScenarioSurvey.participant_id == participant_id,
        PostScenarioSurvey.scenario_number == scenario_number,
    ).first():
        raise HTTPException(status_code=409, detail="Scenario already completed")

    _mark_prior_complete_rows_false(db, participant_id, scenario_number)

    row = ScenarioResponse(
        participant_id=participant_id,
        scenario_number=scenario_number,
        alert_round=allocate_alert_round(db, participant_id, scenario_number),
        interaction_status=STATUS_PENDING,
        is_final_submission_row=MARKER_FALSE,
        participant_variant=participant.variant,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{participant_id}/alert-interactions/{scenario_response_id}/complete", response_model=ScenarioResponseSchema)
def complete_alert_interaction(
    request: Request,
    participant_id: int,
    scenario_response_id: int,
    data: AlertInteractionCompleteRequest,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Persist the completed assessment output for a Variant A alert interaction row."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    if _is_variant_b(participant.variant):
        raise HTTPException(status_code=400, detail="Alert interactions are only for Group A participants")
    progress = build_participant_progress_response(db, participant)
    expected_path = f"/conversation/{data.scenario_number - 1}"
    if progress.redirect_path != expected_path:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )

    row = db.query(ScenarioResponse).filter(
        ScenarioResponse.id == scenario_response_id,
        ScenarioResponse.participant_id == participant_id,
        ScenarioResponse.scenario_number == data.scenario_number,
    ).with_for_update().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Scenario interaction not found")
    if row.interaction_status == STATUS_ABORT:
        raise HTTPException(status_code=409, detail="Scenario interaction already aborted")
    if row.interaction_status == STATUS_COMPLETE:
        raise HTTPException(status_code=409, detail="Scenario interaction already completed")
    if row.is_final_submission_row == MARKER_TRUE:
        raise HTTPException(status_code=409, detail="Scenario interaction already finalized")

    output_id_value = _normalize_string_field(data.output_id)
    row.interaction_status = STATUS_COMPLETE
    row.is_final_submission_row = MARKER_FALSE
    row.original_input = data.original_input
    row.masked_text = data.masked_text
    row.output_id = output_id_value
    row.input_tokens = _normalize_token_field(data.input_tokens)
    row.total_tokens = _normalize_token_field(data.total_tokens)
    row.model = _normalize_string_field(data.model)
    row.scenario_llm_usage = _resolve_scenario_llm_usage(
        db,
        participant_id=participant_id,
        scenario_number=data.scenario_number,
        output_id=output_id_value,
    )
    row.risk_level = data.risk_level
    row.reasoning = data.reasoning
    row.suggested_rewrite = data.suggested_rewrite
    row.primary_risk_factors = (
        json.dumps(data.primary_risk_factors, ensure_ascii=True)
        if data.primary_risk_factors is not None else None
    )
    row.linkability_risk_level = data.linkability_risk_level
    row.linkability_risk_explanation = data.linkability_risk_explanation
    row.authentication_baiting_level = data.authentication_baiting_level
    row.authentication_baiting_explanation = data.authentication_baiting_explanation
    row.contextual_alignment_level = data.contextual_alignment_level
    row.contextual_alignment_explanation = data.contextual_alignment_explanation
    row.platform_trust_obligation_level = data.platform_trust_obligation_level
    row.platform_trust_obligation_explanation = data.platform_trust_obligation_explanation
    row.psychological_pressure_level = data.psychological_pressure_level
    row.psychological_pressure_explanation = data.psychological_pressure_explanation
    row.completed_at = get_singapore_time()

    db.commit()
    db.refresh(row)
    return row


@router.post("/{participant_id}/alert-interactions/{scenario_response_id}/decision", response_model=ScenarioResponseSchema)
def record_alert_interaction_decision(
    request: Request,
    participant_id: int,
    scenario_response_id: int,
    data: AlertInteractionDecisionRequest,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Persist the explicit modal choice for a Variant A alert interaction row."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    if _is_variant_b(participant.variant):
        raise HTTPException(status_code=400, detail="Alert interactions are only for Group A participants")

    row = db.query(ScenarioResponse).filter(
        ScenarioResponse.id == scenario_response_id,
        ScenarioResponse.participant_id == participant_id,
    ).with_for_update().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Scenario interaction not found")
    if row.interaction_status != STATUS_COMPLETE:
        raise HTTPException(status_code=409, detail="Scenario interaction is not ready for a decision")
    if row.accepted_rewrite is not None:
        raise HTTPException(status_code=409, detail="Decision already recorded for this interaction")
    progress = build_participant_progress_response(db, participant)
    expected_path = f"/conversation/{row.scenario_number - 1}"
    if progress.redirect_path != expected_path:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )

    accepted_rewrite_value = _normalize_accepted_rewrite(data.accepted_rewrite, participant.variant)
    if accepted_rewrite_value not in {"true", "false", None}:
        raise HTTPException(status_code=400, detail="Invalid rewrite decision")

    row.accepted_rewrite = accepted_rewrite_value
    db.commit()
    db.refresh(row)
    return row


@router.post("/{participant_id}/scenario-response", response_model=ScenarioResponseSchema)
def create_or_update_scenario_response(
    request: Request,
    participant_id: int,
    data: ScenarioResponseCreate,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Legacy endpoint retained for compatibility with manual/admin usage."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)

    if _is_variant_b(participant.variant):
        existing = db.query(ScenarioResponse).filter(
            ScenarioResponse.participant_id == participant_id,
            ScenarioResponse.scenario_number == data.scenario_number,
            ScenarioResponse.is_final_submission_row == MARKER_TRUE,
        ).first()
        if existing is None:
            existing = ScenarioResponse(
                participant_id=participant_id,
                scenario_number=data.scenario_number,
                interaction_status=STATUS_B,
                is_final_submission_row=MARKER_TRUE,
                scenario_llm_usage=MARKER_B,
                participant_variant=participant.variant,
            )
            db.add(existing)
        existing.original_input = MARKER_B
        existing.masked_text = MARKER_B
        existing.output_id = MARKER_B
        existing.input_tokens = 0
        existing.total_tokens = 0
        existing.model = MARKER_B
        existing.scenario_llm_usage = MARKER_B
        existing.risk_level = MARKER_B
        existing.reasoning = MARKER_B
        existing.suggested_rewrite = MARKER_B
        existing.primary_risk_factors = MARKER_B
        existing.linkability_risk_level = MARKER_B
        existing.linkability_risk_explanation = MARKER_B
        existing.authentication_baiting_level = MARKER_B
        existing.authentication_baiting_explanation = MARKER_B
        existing.contextual_alignment_level = MARKER_B
        existing.contextual_alignment_explanation = MARKER_B
        existing.platform_trust_obligation_level = MARKER_B
        existing.platform_trust_obligation_explanation = MARKER_B
        existing.psychological_pressure_level = MARKER_B
        existing.psychological_pressure_explanation = MARKER_B
        existing.accepted_rewrite = MARKER_B
        existing.final_message = data.final_message
        existing.completed_at = get_singapore_time()
        db.commit()
        db.refresh(existing)
        return existing

    row = ScenarioResponse(
        participant_id=participant_id,
        scenario_number=data.scenario_number,
        alert_round=data.alert_round or allocate_alert_round(db, participant_id, data.scenario_number),
        interaction_status=data.interaction_status or STATUS_COMPLETE,
        is_final_submission_row=data.is_final_submission_row or MARKER_FALSE,
        original_input=data.original_input,
        masked_text=data.masked_text,
        output_id=_normalize_string_field(data.output_id),
        input_tokens=_normalize_token_field(data.input_tokens),
        total_tokens=_normalize_token_field(data.total_tokens),
        model=_normalize_string_field(data.model),
        scenario_llm_usage=_normalize_string_field(data.scenario_llm_usage),
        risk_level=data.risk_level,
        reasoning=data.reasoning,
        suggested_rewrite=data.suggested_rewrite,
        primary_risk_factors=data.primary_risk_factors,
        linkability_risk_level=data.linkability_risk_level,
        linkability_risk_explanation=data.linkability_risk_explanation,
        authentication_baiting_level=data.authentication_baiting_level,
        authentication_baiting_explanation=data.authentication_baiting_explanation,
        contextual_alignment_level=data.contextual_alignment_level,
        contextual_alignment_explanation=data.contextual_alignment_explanation,
        platform_trust_obligation_level=data.platform_trust_obligation_level,
        platform_trust_obligation_explanation=data.platform_trust_obligation_explanation,
        psychological_pressure_level=data.psychological_pressure_level,
        psychological_pressure_explanation=data.psychological_pressure_explanation,
        final_message=data.final_message,
        accepted_rewrite=_normalize_accepted_rewrite(data.accepted_rewrite, participant.variant),
        completed_at=get_singapore_time() if data.final_message else None,
        participant_variant=participant.variant,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/message")
def record_scenario_message(
    request: Request,
    data: ScenarioMessageRecord,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """
    Record scenario message data - compatibility endpoint for frontend.
    Maps conversation_index (0,1,2) to scenario_number (1,2,3).
    """
    require_mobile_request(request)
    if data.conversation_index not in (0, 1, 2):
        raise HTTPException(status_code=400, detail="Invalid conversation index")

    # Frontend currently sends prolific_id; accept numeric participant ids for manual/admin use.
    if isinstance(data.participant_id, int):
        participant = get_participant_by_id(db, data.participant_id)
    else:
        participant = get_participant_by_prolific_id(db, str(data.participant_id))
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    
    scenario_number = data.conversation_index + 1  # Convert 0-indexed to 1-indexed
    progress = build_participant_progress_response(db, participant)
    expected_path = f"/conversation/{data.conversation_index}"
    if progress.redirect_path != expected_path:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )

    if is_completed_state(participant.is_complete):
        raise HTTPException(status_code=409, detail="Participant already completed")

    scenario_survey_exists = db.query(PostScenarioSurvey.id).filter(
        and_(
            PostScenarioSurvey.participant_id == participant.id,
            PostScenarioSurvey.scenario_number == scenario_number
        )
    ).first()
    if scenario_survey_exists:
        raise HTTPException(status_code=409, detail="Scenario already completed")
    
    existing_final = db.query(ScenarioResponse).filter(
        ScenarioResponse.participant_id == participant.id,
        ScenarioResponse.scenario_number == scenario_number,
        ScenarioResponse.is_final_submission_row == MARKER_TRUE,
    ).with_for_update().all()
    if any(_final_message_is_actual(row.final_message) for row in existing_final):
        raise HTTPException(status_code=409, detail="Scenario message already submitted")

    completion_time = get_singapore_time()
    participant_variant = participant.variant
    variant_b = _is_variant_b(participant_variant)
    if variant_b:
        existing = db.query(ScenarioResponse).filter(
            ScenarioResponse.participant_id == participant.id,
            ScenarioResponse.scenario_number == scenario_number,
            ScenarioResponse.is_final_submission_row == MARKER_TRUE,
        ).first()
        if existing is None:
            existing = ScenarioResponse(
                participant_id=participant.id,
                scenario_number=scenario_number,
                interaction_status=STATUS_B,
                is_final_submission_row=MARKER_TRUE,
                participant_variant=participant_variant,
            )
            db.add(existing)
        _set_variant_a_marker_fields(existing, MARKER_B)
        existing.interaction_status = STATUS_B
        existing.is_final_submission_row = MARKER_TRUE
        existing.final_message = data.final_message
        existing.completed_at = completion_time
        logger.info("[DB] Upserted variant B scenario_response for participant %s, scenario %s", participant.id, scenario_number)
    else:
        db.query(ScenarioResponse).filter(
            ScenarioResponse.participant_id == participant.id,
            ScenarioResponse.scenario_number == scenario_number,
        ).update(
            {ScenarioResponse.is_final_submission_row: MARKER_FALSE},
            synchronize_session=False,
        )

        latest = _latest_scenario_response(db, participant.id, scenario_number)
        if latest is None:
            latest = ScenarioResponse(
                participant_id=participant.id,
                scenario_number=scenario_number,
                alert_round=0,
                interaction_status=STATUS_DNI,
                is_final_submission_row=MARKER_TRUE,
                final_message=data.final_message,
                completed_at=completion_time,
                participant_variant=participant_variant,
            )
            _set_variant_a_marker_fields(latest, MARKER_DNI)
            db.add(latest)
            logger.info("[DB] Created Variant A DNI scenario_response for participant %s, scenario %s", participant.id, scenario_number)
        else:
            if latest.interaction_status in {None, STATUS_PENDING}:
                latest.interaction_status = STATUS_ABORT
                _set_variant_a_marker_fields(latest, MARKER_ABORT)
                if latest.final_message in {None, ""}:
                    latest.final_message = MARKER_ABORT
            latest.is_final_submission_row = MARKER_TRUE
            latest.final_message = data.final_message
            latest.completed_at = completion_time
            if latest.participant_variant is None:
                latest.participant_variant = participant_variant
            logger.info(
                "[DB] Finalized Variant A scenario_response id=%s for participant %s, scenario %s",
                latest.id,
                participant.id,
                scenario_number,
            )
    
    db.commit()
    return {"status": "saved"}


# =============================================================================
# Post-Scenario Survey endpoints (Table 4)
# =============================================================================
@router.post("/{participant_id}/post-scenario-survey", response_model=PostScenarioSurveySchema)
def create_post_scenario_survey(
    request: Request,
    participant_id: int,
    data: PostScenarioSurveyCreate,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Create post-scenario survey response for a participant."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    progress = build_participant_progress_response(db, participant)
    expected_mid = f"/survey/mid?index={data.scenario_number - 1}"
    expected_post = f"/survey/post-scenario?index={data.scenario_number - 1}"
    if progress.redirect_path not in {expected_mid, expected_post}:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )
    
    # Check if post-scenario survey already exists
    existing = db.query(PostScenarioSurvey).filter(
        and_(
            PostScenarioSurvey.participant_id == participant_id,
            PostScenarioSurvey.scenario_number == data.scenario_number
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Post-scenario survey already exists for this scenario")

    included_pii_types_value = json.dumps(data.included_pii_types or [], ensure_ascii=True)
    included_pii_other_text_value = (data.included_pii_other_text or "").strip() or None
    variant_b = _is_variant_b(participant.variant)
    warning_scenarios = _participant_warning_scenarios(db, participant_id)
    scenario_saw_warning = data.scenario_number in warning_scenarios
    warning_clarity_value = "[B]" if variant_b else ("0" if not scenario_saw_warning else (str(data.warning_clarity) if data.warning_clarity is not None else None))
    warning_helpful_value = "[B]" if variant_b else ("0" if not scenario_saw_warning else (str(data.warning_helpful) if data.warning_helpful is not None else None))
    rewrite_quality_value = "[B]" if variant_b else ("0" if not scenario_saw_warning else (str(data.rewrite_quality) if data.rewrite_quality is not None else None))

    post_survey = PostScenarioSurvey(
        participant_id=participant_id,
        scenario_number=data.scenario_number,
        confidence_judgment=data.confidence_judgment,
        uncertainty_sharing=data.uncertainty_sharing,
        perceived_risk=data.perceived_risk,
        included_pii_types=included_pii_types_value,
        included_pii_other_text=included_pii_other_text_value,
        warning_clarity=warning_clarity_value,
        warning_helpful=warning_helpful_value,
        rewrite_quality=rewrite_quality_value,
        participant_variant=participant.variant,
    )
    db.add(post_survey)
    db.commit()
    db.refresh(post_survey)
    
    return post_survey


# =============================================================================
# SUS Response endpoints (Table 6)
# =============================================================================
@router.post("/{participant_id}/sus-responses", response_model=SusResponseSchema)
def create_sus_responses(
    request: Request,
    participant_id: int,
    data: SusResponseCreate,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Create SUS responses for a participant (Group A only)."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    progress = build_participant_progress_response(db, participant)
    if progress.redirect_path not in {"/survey/end-of-study", "/survey/post"}:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )
    
    if participant.variant != "A":
        raise HTTPException(status_code=400, detail="SUS responses are only for Group A participants")
    if not _participant_saw_any_warning(db, participant_id):
        raise HTTPException(status_code=400, detail="SUS responses are not applicable when no warnings were shown")
    
    # Check if SUS responses already exist
    existing = db.query(SusResponse).filter(
        SusResponse.participant_id == participant_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="SUS responses already exist")
    
    # Calculate SUS score
    sus_score = calculate_sus_score(
        data.sus_1, data.sus_2, data.sus_3, data.sus_4, data.sus_5,
        data.sus_6, data.sus_7, data.sus_8, data.sus_9, data.sus_10
    )
    
    sus_response = SusResponse(
        participant_id=participant_id,
        sus_1=data.sus_1,
        sus_2=data.sus_2,
        sus_3=data.sus_3,
        sus_4=data.sus_4,
        sus_5=data.sus_5,
        sus_6=data.sus_6,
        sus_7=data.sus_7,
        sus_8=data.sus_8,
        sus_9=data.sus_9,
        sus_10=data.sus_10,
        sus_score=sus_score,
        participant_variant=participant.variant,
    )
    db.add(sus_response)
    db.commit()
    db.refresh(sus_response)
    
    return sus_response


# =============================================================================
# End-of-Study Survey endpoints (Table 7)
# =============================================================================
@router.post("/{participant_id}/end-of-study-survey", response_model=EndOfStudySurveySchema)
def create_end_of_study_survey(
    request: Request,
    participant_id: int,
    data: EndOfStudySurveyCreate,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Create end-of-study survey response for a participant."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    participant = sync_participant_completion_state(db, participant, mark_active=True)
    progress = build_participant_progress_response(db, participant)
    if progress.redirect_path not in {"/survey/end-of-study", "/survey/post"}:
        raise HTTPException(
            status_code=409,
            detail={"message": "Step out of sequence", "redirect_path": progress.redirect_path},
        )
    
    # Check if end-of-study survey already exists
    existing = db.query(EndOfStudySurvey).filter(
        EndOfStudySurvey.participant_id == participant_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="End-of-study survey already exists")
    variant_b = _is_variant_b(participant.variant)
    saw_any_warning = _participant_saw_any_warning(db, participant_id)
    if not data.realism_explanation.strip():
        raise HTTPException(status_code=400, detail="realism_explanation is required")
    if not data.sharing_rationale.strip():
        raise HTTPException(status_code=400, detail="sharing_rationale is required")
    if _word_count(data.realism_explanation) < END_OF_STUDY_MIN_WORDS:
        raise HTTPException(
            status_code=400,
            detail=f"realism_explanation must contain at least {END_OF_STUDY_MIN_WORDS} words",
        )
    if _word_count(data.sharing_rationale) < END_OF_STUDY_MIN_WORDS:
        raise HTTPException(
            status_code=400,
            detail=f"sharing_rationale must contain at least {END_OF_STUDY_MIN_WORDS} words",
        )
    if not variant_b and saw_any_warning:
        if data.trust_system is None:
            raise HTTPException(status_code=400, detail="trust_system is required for Group A")
        if not (data.trust_explanation or "").strip():
            raise HTTPException(status_code=400, detail="trust_explanation is required for Group A")
        if _word_count(data.trust_explanation) < END_OF_STUDY_MIN_WORDS:
            raise HTTPException(
                status_code=400,
                detail=f"trust_explanation must contain at least {END_OF_STUDY_MIN_WORDS} words",
            )
    trust_system_value = "[B]" if variant_b else ("0" if not saw_any_warning else (str(data.trust_system) if data.trust_system is not None else None))
    trust_explanation_value = "[B]" if variant_b else (MARKER_NO_SHOW if not saw_any_warning else data.trust_explanation)

    end_survey = EndOfStudySurvey(
        participant_id=participant_id,
        tasks_realistic=data.tasks_realistic,
        realism_explanation=data.realism_explanation,
        overall_confidence=data.overall_confidence,
        sharing_rationale=data.sharing_rationale,
        trust_system=trust_system_value,
        trust_explanation=trust_explanation_value,
        participant_variant=participant.variant,
    )
    db.add(end_survey)

    if not variant_b and not saw_any_warning:
        existing_sus = db.query(SusResponse).filter(
            SusResponse.participant_id == participant_id
        ).first()
        if existing_sus is None:
            db.add(SusResponse(
                participant_id=participant_id,
                sus_1=0,
                sus_2=0,
                sus_3=0,
                sus_4=0,
                sus_5=0,
                sus_6=0,
                sus_7=0,
                sus_8=0,
                sus_9=0,
                sus_10=0,
                sus_score=0,
                participant_variant=participant.variant,
            ))
    
    # Mark participant as complete
    participant.is_complete = COMPLETE_STATE_TRUE
    completion_time = get_singapore_time().replace(microsecond=0)
    if participant.completed_at is None:
        participant.completed_at = completion_time

    # Calculate duration safely for SQLite rows that may deserialize as naive datetimes.
    created_at = ensure_singapore_tz(participant.created_at)
    completed_at = ensure_singapore_tz(participant.completed_at)
    if completed_at is not None:
        participant.completed_at = completed_at
    if created_at is not None and completed_at is not None:
        participant.duration_seconds = max((completed_at - created_at).total_seconds(), 0.0)

    # Mark all scenario rows as completed when participant submits final survey.
    if participant.completed_at is not None:
        db.query(ScenarioResponse).filter(
            ScenarioResponse.participant_id == participant_id,
            ScenarioResponse.completed_at.is_(None)
        ).update(
            {ScenarioResponse.completed_at: participant.completed_at},
            synchronize_session=False
        )
    
    db.commit()
    db.refresh(end_survey)
    
    return end_survey


# =============================================================================
# Get all participant data
# =============================================================================
@router.get("/{participant_id}/data", response_model=ParticipantDataResponse)
def get_participant_data(
    request: Request,
    participant_id: int,
    db: Session = Depends(get_db)
):
    """Get all data for a single participant across all tables."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    return build_participant_data_response(db, participant)


@router.get("/{participant_id}/progress", response_model=ParticipantProgressResponse)
def get_participant_progress(
    request: Request,
    participant_id: int,
    db: Session = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Get canonical participant progress and next allowed route."""
    require_mobile_request(request)
    participant = get_participant_by_id(db, participant_id)
    _verify_session_token(participant, x_session_token)
    return build_participant_progress_response(db, participant)


@router.get("/by-prolific/{prolific_id}/data", response_model=ParticipantDataResponse)
def get_participant_data_by_prolific_id(
    prolific_id: str,
    db: Session = Depends(get_db)
):
    """Get all data for a single participant using Prolific ID."""
    participant = get_participant_by_prolific_id(db, prolific_id)
    return build_participant_data_response(db, participant)
