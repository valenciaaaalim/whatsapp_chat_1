from __future__ import annotations

from sqlalchemy import func, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import LLMOutput, ParticipantScenarioCounter, ScenarioResponse


def _ensure_counter_row(db: Session, participant_id: int, scenario_number: int) -> ParticipantScenarioCounter:
    values = {
        "participant_id": participant_id,
        "scenario_number": scenario_number,
        "next_alert_round": 1,
        "next_llm_nth_call": 1,
        "llm_cap_used": 0,
    }
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect == "postgresql":
        stmt = pg_insert(ParticipantScenarioCounter).values(**values).on_conflict_do_nothing(
            index_elements=["participant_id", "scenario_number"]
        )
        db.execute(stmt)
    elif dialect == "sqlite":
        stmt = sqlite_insert(ParticipantScenarioCounter).values(**values).on_conflict_do_nothing(
            index_elements=["participant_id", "scenario_number"]
        )
        db.execute(stmt)
    else:
        existing = db.query(ParticipantScenarioCounter).filter(
            ParticipantScenarioCounter.participant_id == participant_id,
            ParticipantScenarioCounter.scenario_number == scenario_number,
        ).first()
        if existing is None:
            db.add(ParticipantScenarioCounter(**values))
            db.flush()

    query = db.query(ParticipantScenarioCounter).filter(
        ParticipantScenarioCounter.participant_id == participant_id,
        ParticipantScenarioCounter.scenario_number == scenario_number,
    )
    if dialect == "postgresql":
        query = query.with_for_update()
    row = query.first()
    if row is None:
        raise RuntimeError("Failed to initialize participant scenario counter")
    return row


def allocate_alert_round(db: Session, participant_id: int, scenario_number: int) -> int:
    row = _ensure_counter_row(db, participant_id, scenario_number)
    current = int(row.next_alert_round or 1)
    row.next_alert_round = current + 1
    db.flush()
    return current


def reserve_llm_cap_slot(db: Session, participant_id: int, scenario_number: int, limit: int) -> tuple[bool, int]:
    row = _ensure_counter_row(db, participant_id, scenario_number)
    current = int(row.llm_cap_used or 0)
    if current >= limit:
        return False, current
    row.llm_cap_used = current + 1
    db.flush()
    return True, int(row.llm_cap_used)


def release_llm_cap_slot(db: Session, participant_id: int, scenario_number: int) -> None:
    row = _ensure_counter_row(db, participant_id, scenario_number)
    current = int(row.llm_cap_used or 0)
    if current > 0:
        row.llm_cap_used = current - 1
        db.flush()


def allocate_llm_nth_call(db: Session, participant_id: int, scenario_number: int) -> int:
    row = _ensure_counter_row(db, participant_id, scenario_number)
    current = int(row.next_llm_nth_call or 1)
    row.next_llm_nth_call = current + 1
    db.flush()
    return current


def sync_participant_scenario_counters(db: Session) -> None:
    alert_rows = (
        db.query(
            ScenarioResponse.participant_id,
            ScenarioResponse.scenario_number,
            func.max(ScenarioResponse.alert_round),
        )
        .filter(ScenarioResponse.scenario_number.isnot(None))
        .group_by(ScenarioResponse.participant_id, ScenarioResponse.scenario_number)
        .all()
    )
    llm_rows = (
        db.query(
            LLMOutput.participant_id,
            LLMOutput.scenario_id,
            func.max(LLMOutput.nth_call),
            func.count(LLMOutput.id),
        )
        .group_by(LLMOutput.participant_id, LLMOutput.scenario_id)
        .all()
    )

    merged: dict[tuple[int, int], dict[str, int]] = {}
    for participant_id, scenario_number, max_alert in alert_rows:
        key = (int(participant_id), int(scenario_number))
        merged.setdefault(key, {})
        merged[key]["next_alert_round"] = int(max_alert or 0) + 1
    for participant_id, scenario_number, max_nth, cap_used in llm_rows:
        key = (int(participant_id), int(scenario_number))
        merged.setdefault(key, {})
        merged[key]["next_llm_nth_call"] = int(max_nth or 0) + 1
        merged[key]["llm_cap_used"] = int(cap_used or 0)

    if not merged:
        return

    keys = list(merged.keys())
    existing_rows = (
        db.query(ParticipantScenarioCounter)
        .filter(tuple_(ParticipantScenarioCounter.participant_id, ParticipantScenarioCounter.scenario_number).in_(keys))
        .all()
    )
    existing_map = {
        (row.participant_id, row.scenario_number): row
        for row in existing_rows
    }

    for (participant_id, scenario_number), values in merged.items():
        row = existing_map.get((participant_id, scenario_number))
        if row is None:
            row = ParticipantScenarioCounter(
                participant_id=participant_id,
                scenario_number=scenario_number,
                next_alert_round=values.get("next_alert_round", 1),
                next_llm_nth_call=values.get("next_llm_nth_call", 1),
                llm_cap_used=values.get("llm_cap_used", 0),
            )
            db.add(row)
            continue
        row.next_alert_round = max(int(row.next_alert_round or 1), values.get("next_alert_round", 1))
        row.next_llm_nth_call = max(int(row.next_llm_nth_call or 1), values.get("next_llm_nth_call", 1))
        row.llm_cap_used = max(int(row.llm_cap_used or 0), values.get("llm_cap_used", 0))

    db.commit()
