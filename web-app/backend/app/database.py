"""
Database setup and session management.
Normalized schema and database utilities.
"""
import logging
import os

from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Prefer direct env lookup for startup resilience.
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

# Create database engine
engine: Engine | None = None
if not DATABASE_URL:
    logger.warning("DATABASE_URL not set, DB features disabled.")
else:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    except Exception:
        logger.exception("Failed to create DB engine; DB features disabled.")
        engine = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

# Base class for models
Base = declarative_base()


def is_db_configured() -> bool:
    """Return whether database engine is available."""
    return engine is not None


def require_db() -> Engine:
    """Require a configured DB engine for DB-backed request handlers."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    return engine


def get_db_dialect() -> str:
    """Return active SQL dialect name, e.g. postgresql."""
    if engine is not None:
        return engine.url.get_backend_name()
    if DATABASE_URL and "://" in DATABASE_URL:
        return DATABASE_URL.split("://", 1)[0]
    return "disabled"


def _ensure_participant_views() -> None:
    """
    Create participant convenience views split by variant.
    """
    view_defs = {
        "v_baseline_assessment_A": """
            SELECT
                ba.id,
                ba.participant_id,
                ba.recognize_sensitive,
                ba.avoid_accidental,
                ba.familiar_scams,
                ba.contextual_judgment,
                p.variant AS participant_variant
            FROM baseline_assessment ba
            JOIN participants p ON p.id = ba.participant_id
            WHERE p.variant = 'A'
        """,
        "v_scenario_responses_A": """
            SELECT
                sr.id,
                sr.participant_id,
                sr.scenario_number,
                sr.alert_round,
                sr.interaction_status,
                sr.is_final_submission_row,
                sr.original_input,
                sr.masked_text,
                sr.output_id,
                sr.input_tokens,
                sr.total_tokens,
                sr.model,
                sr.scenario_llm_usage,
                sr.risk_level,
                sr.reasoning,
                sr.suggested_rewrite,
                sr.final_message,
                sr.primary_risk_factors,
                sr.linkability_risk_level,
                sr.linkability_risk_explanation,
                sr.authentication_baiting_level,
                sr.authentication_baiting_explanation,
                sr.contextual_alignment_level,
                sr.contextual_alignment_explanation,
                sr.platform_trust_obligation_level,
                sr.platform_trust_obligation_explanation,
                sr.psychological_pressure_level,
                sr.psychological_pressure_explanation,
                sr.accepted_rewrite,
                sr.completed_at,
                p.variant AS participant_variant
            FROM scenario_responses sr
            JOIN participants p ON p.id = sr.participant_id
            WHERE p.variant = 'A'
        """,
        "v_post_scenario_survey_A": """
            SELECT
                pss.id,
                pss.participant_id,
                pss.scenario_number,
                pss.confidence_judgment,
                pss.uncertainty_sharing,
                pss.perceived_risk,
                pss.included_pii_types,
                pss.included_pii_other_text,
                pss.warning_clarity,
                pss.warning_helpful,
                pss.rewrite_quality,
                p.variant AS participant_variant
            FROM post_scenario_survey pss
            JOIN participants p ON p.id = pss.participant_id
            WHERE p.variant = 'A'
        """,
        "v_end_of_study_survey_A": """
            SELECT
                eos.id,
                eos.participant_id,
                eos.tasks_realistic,
                eos.realism_explanation,
                eos.overall_confidence,
                eos.sharing_rationale,
                eos.trust_system,
                eos.trust_explanation,
                p.variant AS participant_variant
            FROM end_of_study_survey eos
            JOIN participants p ON p.id = eos.participant_id
            WHERE p.variant = 'A'
        """,
        "v_sus_responses_A": """
            SELECT
                sus.id,
                sus.participant_id,
                sus.sus_1,
                sus.sus_2,
                sus.sus_3,
                sus.sus_4,
                sus.sus_5,
                sus.sus_6,
                sus.sus_7,
                sus.sus_8,
                sus.sus_9,
                sus.sus_10,
                sus.sus_score,
                p.variant AS participant_variant
            FROM sus_responses sus
            JOIN participants p ON p.id = sus.participant_id
            WHERE p.variant = 'A'
        """,
        "v_baseline_assessment_B": """
            SELECT
                ba.id,
                ba.participant_id,
                ba.recognize_sensitive,
                ba.avoid_accidental,
                ba.familiar_scams,
                ba.contextual_judgment,
                p.variant AS participant_variant
            FROM baseline_assessment ba
            JOIN participants p ON p.id = ba.participant_id
            WHERE p.variant = 'B'
        """,
        "v_scenario_responses_B": """
            SELECT
                sr.id,
                sr.participant_id,
                sr.scenario_number,
                sr.final_message,
                sr.completed_at,
                p.variant AS participant_variant
            FROM scenario_responses sr
            JOIN participants p ON p.id = sr.participant_id
            WHERE p.variant = 'B'
        """,
        "v_post_scenario_survey_B": """
            SELECT
                pss.id,
                pss.participant_id,
                pss.scenario_number,
                pss.confidence_judgment,
                pss.uncertainty_sharing,
                pss.perceived_risk,
                pss.included_pii_types,
                pss.included_pii_other_text,
                p.variant AS participant_variant
            FROM post_scenario_survey pss
            JOIN participants p ON p.id = pss.participant_id
            WHERE p.variant = 'B'
        """,
        "v_end_of_study_survey_B": """
            SELECT
                eos.id,
                eos.participant_id,
                eos.tasks_realistic,
                eos.realism_explanation,
                eos.overall_confidence,
                eos.sharing_rationale,
                p.variant AS participant_variant
            FROM end_of_study_survey eos
            JOIN participants p ON p.id = eos.participant_id
            WHERE p.variant = 'B'
        """,
    }
    db_engine = require_db()
    legacy_views = [
        "v_baseline_assessment",
        "v_scenario_responses",
        "v_post_scenario_survey",
        "v_pii_disclosure",
        "v_sus_responses",
        "v_end_of_study_survey",
        "v_participant_llm_usage",
        "v_participant_scenario_llm_usage",
        "v_llm_outputs",
    ]
    with db_engine.begin() as conn:
        for legacy in legacy_views:
            conn.execute(text(f"DROP VIEW IF EXISTS {legacy}"))
        for view_name, select_sql in view_defs.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {view_name}"))
            conn.execute(text(f"CREATE VIEW {view_name} AS {select_sql}"))


def _ensure_schema_columns() -> None:
    """Apply backward-compatible schema changes and remove deprecated tables."""
    db_engine = require_db()
    inspector = inspect(db_engine)
    table_names = set(inspector.get_table_names())
    dialect = db_engine.dialect.name
    statements = []

    # Drop legacy views that may depend on deprecated tables/columns.
    drop_view_statements = [
        "DROP VIEW IF EXISTS v_baseline_assessment",
        "DROP VIEW IF EXISTS v_scenario_responses",
        "DROP VIEW IF EXISTS v_post_scenario_survey",
        "DROP VIEW IF EXISTS v_pii_disclosure",
        "DROP VIEW IF EXISTS v_sus_responses",
        "DROP VIEW IF EXISTS v_end_of_study_survey",
        "DROP VIEW IF EXISTS v_participant_llm_usage",
        "DROP VIEW IF EXISTS v_participant_scenario_llm_usage",
        "DROP VIEW IF EXISTS v_llm_outputs",
    ]

    if "scenario_responses" in table_names:
        existing_columns = {col.get("name") for col in inspector.get_columns("scenario_responses")}
        existing_column_types = {
            col.get("name"): str(col.get("type", "")).lower()
            for col in inspector.get_columns("scenario_responses")
        }
        if "Reasoning" in existing_columns and "reasoning" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses RENAME COLUMN "Reasoning" TO reasoning')
        if dialect == "postgresql":
            statements.append("ALTER TABLE scenario_responses DROP CONSTRAINT IF EXISTS uq_scenario_response_participant_scenario")

        if "alert_round" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "alert_round" INTEGER')
        if "interaction_status" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "interaction_status" VARCHAR')
        if "is_final_submission_row" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "is_final_submission_row" VARCHAR')
        if "output_id" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "output_id" VARCHAR')
        if "total_tokens" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "total_tokens" INTEGER')
        if "input_tokens" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "input_tokens" INTEGER')
        if "model" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "model" VARCHAR')
        if "scenario_llm_usage" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "scenario_llm_usage" VARCHAR')
        if "participant_variant" not in existing_columns:
            statements.append('ALTER TABLE scenario_responses ADD COLUMN "participant_variant" VARCHAR')
        if "started_at" in existing_columns:
            statements.append('ALTER TABLE scenario_responses DROP COLUMN IF EXISTS "started_at"')
        statements.append(
            """
            UPDATE scenario_responses sr
            SET participant_variant = (
                SELECT p.variant FROM participants p WHERE p.id = sr.participant_id
            )
            WHERE sr.participant_variant IS NULL
            """
        )

        if (
            "accepted_rewrite" in existing_columns
            and "boolean" in existing_column_types.get("accepted_rewrite", "")
            and dialect == "postgresql"
        ):
            statements.append(
                """
                ALTER TABLE scenario_responses
                ALTER COLUMN accepted_rewrite TYPE VARCHAR
                USING CASE
                    WHEN accepted_rewrite IS TRUE THEN 'true'
                    WHEN accepted_rewrite IS FALSE THEN 'false'
                    ELSE NULL
                END
                """
            )
        if dialect == "postgresql" and "integer" not in existing_column_types.get("input_tokens", ""):
            statements.append(
                """
                ALTER TABLE scenario_responses
                ALTER COLUMN input_tokens TYPE INTEGER
                USING CASE
                    WHEN input_tokens IS NULL THEN NULL
                    WHEN trim(input_tokens::text) ~ '^[0-9]+$' THEN trim(input_tokens::text)::integer
                    ELSE 0
                END
                """
            )
        if dialect == "postgresql" and "integer" not in existing_column_types.get("total_tokens", ""):
            statements.append(
                """
                ALTER TABLE scenario_responses
                ALTER COLUMN total_tokens TYPE INTEGER
                USING CASE
                    WHEN total_tokens IS NULL THEN NULL
                    WHEN trim(total_tokens::text) ~ '^[0-9]+$' THEN trim(total_tokens::text)::integer
                    ELSE 0
                END
                """
            )
        statements.append(
            """
            UPDATE scenario_responses sr
            SET interaction_status = CASE
                WHEN sr.interaction_status IS NOT NULL THEN sr.interaction_status
                WHEN EXISTS (
                    SELECT 1 FROM participants p
                    WHERE p.id = sr.participant_id AND p.variant = 'B'
                ) THEN '[B]'
                WHEN lower(trim(COALESCE(sr.accepted_rewrite, ''))) = '[abort]' THEN '[ABORT]'
                WHEN lower(trim(COALESCE(sr.accepted_rewrite, ''))) = 'abort' THEN '[ABORT]'
                WHEN sr.output_id IS NOT NULL
                  OR sr.model IS NOT NULL
                  OR sr.masked_text IS NOT NULL
                  OR sr.suggested_rewrite IS NOT NULL
                  OR sr.risk_level IS NOT NULL
                  OR sr.reasoning IS NOT NULL THEN '[COMPLETE]'
                WHEN sr.final_message IS NOT NULL AND trim(sr.final_message) <> '' THEN '[DNI]'
                ELSE '[PENDING]'
            END
            """
        )
        statements.append(
            """
            UPDATE scenario_responses sr
            SET is_final_submission_row = CASE
                WHEN sr.is_final_submission_row IS NOT NULL THEN sr.is_final_submission_row
                WHEN sr.final_message IS NOT NULL AND trim(sr.final_message) <> '' THEN '[TRUE]'
                ELSE '[FALSE]'
            END
            """
        )
        statements.append(
            """
            UPDATE scenario_responses sr
            SET alert_round = CASE
                WHEN sr.alert_round IS NOT NULL THEN sr.alert_round
                WHEN sr.interaction_status = '[DNI]' THEN 0
                ELSE 1
            END
            """
        )
        statements.append(
            """
            UPDATE scenario_responses sr
            SET scenario_llm_usage = (
                SELECT CAST(lo.nth_call AS TEXT)
                FROM llm_outputs lo
                WHERE lo.participant_id = sr.participant_id
                  AND lo.scenario_id = sr.scenario_number
                  AND (
                    (sr.output_id IS NOT NULL AND lo.output_id = sr.output_id)
                    OR sr.output_id IS NULL
                  )
                ORDER BY
                    CASE WHEN sr.output_id IS NOT NULL AND lo.output_id = sr.output_id THEN 0 ELSE 1 END,
                    lo.called_at DESC,
                    lo.id DESC
                LIMIT 1
            )
            WHERE sr.scenario_llm_usage IS NULL
            """
        )
        statements.append(
            """
            UPDATE scenario_responses sr
            SET scenario_llm_usage = CASE
                WHEN sr.scenario_llm_usage IS NOT NULL THEN sr.scenario_llm_usage
                WHEN sr.interaction_status = '[DNI]' THEN '[DNI]'
                WHEN sr.interaction_status = '[B]' THEN '[B]'
                ELSE NULL
            END
            """
        )

    if "participants" in table_names:
        participant_columns = {col.get("name") for col in inspector.get_columns("participants")}
        participant_types = {
            col.get("name"): str(col.get("type", "")).lower()
            for col in inspector.get_columns("participants")
        }
        if dialect == "postgresql" and "boolean" in participant_types.get("is_complete", ""):
            statements.append(
                """
                ALTER TABLE participants
                ALTER COLUMN is_complete TYPE VARCHAR
                USING CASE
                    WHEN is_complete IS TRUE THEN 'True'
                    WHEN is_complete IS FALSE THEN 'False'
                    ELSE 'Progress'
                END
                """
            )
        if "participant_variant" not in participant_columns:
            statements.append('ALTER TABLE participants ADD COLUMN "participant_variant" VARCHAR')
        if "session_token" not in participant_columns:
            statements.append('ALTER TABLE participants ADD COLUMN "session_token" VARCHAR')
        statements.append(
            """
            UPDATE participants
            SET is_complete = CASE
                WHEN is_complete IS NULL THEN 'Progress'
                WHEN lower(trim(CAST(is_complete AS TEXT))) IN ('true', 't', '1', '[v]') THEN 'True'
                WHEN lower(trim(CAST(is_complete AS TEXT))) IN ('false', 'f', '0') THEN 'False'
                WHEN lower(trim(CAST(is_complete AS TEXT))) IN ('progress', 'in progress', 'in_progress', 'none', 'null', '') THEN 'Progress'
                ELSE 'Progress'
            END
            """
        )
        if dialect == "postgresql":
            statements.append("ALTER TABLE participants ALTER COLUMN is_complete SET DEFAULT 'Progress'")
            statements.append("ALTER TABLE participants ALTER COLUMN is_complete SET NOT NULL")
        statements.append(
            """
            UPDATE participants
            SET participant_variant = variant
            WHERE participant_variant IS NULL
            """
        )

    if "post_scenario_survey" in table_names:
        pss_columns = {col.get("name") for col in inspector.get_columns("post_scenario_survey")}
        pss_types = {
            col.get("name"): str(col.get("type", "")).lower()
            for col in inspector.get_columns("post_scenario_survey")
        }
        if "included_pii_types" not in pss_columns:
            statements.append('ALTER TABLE post_scenario_survey ADD COLUMN "included_pii_types" TEXT')
        if "included_pii_other_text" not in pss_columns:
            statements.append('ALTER TABLE post_scenario_survey ADD COLUMN "included_pii_other_text" TEXT')
        if "participant_variant" not in pss_columns:
            statements.append('ALTER TABLE post_scenario_survey ADD COLUMN "participant_variant" VARCHAR')
        statements.append(
            """
            UPDATE post_scenario_survey pss
            SET participant_variant = (
                SELECT p.variant FROM participants p WHERE p.id = pss.participant_id
            )
            WHERE pss.participant_variant IS NULL
            """
        )
    if "post_scenario_survey" in table_names and dialect == "postgresql":
        for col_name in ("warning_clarity", "warning_helpful", "rewrite_quality"):
            if "integer" in pss_types.get(col_name, ""):
                statements.append(
                    f"""
                    ALTER TABLE post_scenario_survey
                    ALTER COLUMN {col_name} TYPE VARCHAR
                    USING CASE
                        WHEN {col_name} IS NULL THEN NULL
                        ELSE {col_name}::text
                    END
                    """
                )

    if "end_of_study_survey" in table_names and dialect == "postgresql":
        eos_types = {
            col.get("name"): str(col.get("type", "")).lower()
            for col in inspector.get_columns("end_of_study_survey")
        }
        if "integer" in eos_types.get("trust_system", ""):
            statements.append(
                """
                ALTER TABLE end_of_study_survey
                ALTER COLUMN trust_system TYPE VARCHAR
                USING CASE
                    WHEN trust_system IS NULL THEN NULL
                    ELSE trust_system::text
                END
                """
            )

    if "llm_outputs" in table_names:
        llm_columns = {col.get("name") for col in inspector.get_columns("llm_outputs")}
        llm_types = {
            col.get("name"): str(col.get("type", "")).lower()
            for col in inspector.get_columns("llm_outputs")
        }

        if "created_at" in llm_columns and "called_at" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs RENAME COLUMN created_at TO called_at")
        if "error_text" in llm_columns and "error" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs RENAME COLUMN error_text TO error")
        if "output_id" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN output_id VARCHAR")
        if "total_tokens" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN total_tokens INTEGER")
        if "input_tokens" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN input_tokens INTEGER")
        if "nth_call" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN nth_call INTEGER")
        if "participant_variant" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN participant_variant VARCHAR")
        if "app_status" not in llm_columns:
            statements.append("ALTER TABLE llm_outputs ADD COLUMN app_status VARCHAR")
        if "cap_reached" in llm_columns:
            statements.append("ALTER TABLE llm_outputs DROP COLUMN IF EXISTS cap_reached")
        statements.append(
            """
            UPDATE llm_outputs lo
            SET participant_variant = (
                SELECT p.variant FROM participants p WHERE p.id = lo.participant_id
            )
            WHERE lo.participant_variant IS NULL
            """
        )
        statements.append(
            """
            UPDATE llm_outputs
            SET app_status = 'ABORTED',
                error = NULL
            WHERE error = 'ABORTED'
            """
        )

        if dialect == "postgresql" and "llm_used" in llm_columns and "boolean" in llm_types.get("llm_used", ""):
            statements.append(
                """
                ALTER TABLE llm_outputs
                ALTER COLUMN llm_used TYPE VARCHAR
                USING CASE
                    WHEN llm_used IS TRUE THEN 'true'
                    WHEN llm_used IS FALSE THEN 'false'
                    ELSE NULL
                END
                """
            )
        if dialect == "postgresql":
            statements.append(
                """
                WITH ranked AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY participant_id, scenario_id
                            ORDER BY called_at, id
                        ) AS seq
                    FROM llm_outputs
                )
                UPDATE llm_outputs lo
                SET nth_call = ranked.seq
                FROM ranked
                WHERE lo.id = ranked.id
                  AND lo.nth_call IS NULL
                """
            )

    for table_name in ("baseline_assessment", "sus_responses", "end_of_study_survey"):
        if table_name not in table_names:
            continue
        table_columns = {col.get("name") for col in inspector.get_columns(table_name)}
        if "participant_variant" not in table_columns:
            statements.append(f'ALTER TABLE {table_name} ADD COLUMN "participant_variant" VARCHAR')
        statements.append(
            f"""
            UPDATE {table_name} t
            SET participant_variant = (
                SELECT p.variant FROM participants p WHERE p.id = t.participant_id
            )
            WHERE t.participant_variant IS NULL
            """
        )

    if "consent_decisions" in table_names:
        consent_columns = {col.get("name") for col in inspector.get_columns("consent_decisions")}
        if "participant_platform_id" in consent_columns and "prolific_id" not in consent_columns:
            statements.append('ALTER TABLE consent_decisions RENAME COLUMN "participant_platform_id" TO "prolific_id"')
            consent_columns.remove("participant_platform_id")
            consent_columns.add("prolific_id")
        if "participant_variant" not in consent_columns:
            statements.append('ALTER TABLE consent_decisions ADD COLUMN "participant_variant" VARCHAR')
        statements.append(
            """
            UPDATE consent_decisions cd
            SET participant_variant = (
                SELECT p.variant
                FROM participants p
                WHERE p.prolific_id = cd.prolific_id
                LIMIT 1
            )
            WHERE cd.participant_variant IS NULL
            """
        )
        if dialect == "postgresql":
            statements.append('ALTER TABLE consent_decisions ALTER COLUMN "prolific_id" SET NOT NULL')
            statements.append('ALTER TABLE consent_decisions ALTER COLUMN "participant_variant" SET NOT NULL')

    if dialect == "postgresql":
        statements.append('ALTER TABLE participants ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE scenario_responses ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE post_scenario_survey ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE baseline_assessment ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE sus_responses ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE end_of_study_survey ALTER COLUMN "participant_variant" SET NOT NULL')
        statements.append('ALTER TABLE llm_outputs ALTER COLUMN "participant_variant" SET NOT NULL')

    # Remove deprecated tables.
    statements.append("DROP TABLE IF EXISTS participant_scenario_llm_usage")
    statements.append("DROP TABLE IF EXISTS participant_llm_usage")
    statements.append("DROP TABLE IF EXISTS pii_disclosure")

    with db_engine.begin() as conn:
        for stmt in drop_view_statements:
            conn.execute(text(stmt))
        for stmt in statements:
            conn.execute(text(stmt))
        conn.execute(text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_scenario_responses_final_row
            ON scenario_responses (participant_id, scenario_number)
            WHERE is_final_submission_row = '[TRUE]'
            """
        ))
        conn.execute(text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_scenario_responses_alert_round
            ON scenario_responses (participant_id, scenario_number, alert_round)
            WHERE alert_round IS NOT NULL
            """
        ))
        # FK indexes for common query patterns
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_scenario_responses_participant_id ON scenario_responses (participant_id)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_post_scenario_survey_participant_id ON post_scenario_survey (participant_id)"
        ))
        # CHECK constraint on is_complete (idempotent: skip if already exists)
        if dialect == "postgresql":
            exists = conn.execute(text(
                "SELECT 1 FROM pg_constraint WHERE conname = 'ck_participants_is_complete'"
            )).fetchone()
            if not exists:
                conn.execute(text(
                    "ALTER TABLE participants ADD CONSTRAINT ck_participants_is_complete "
                    "CHECK (is_complete IN ('Progress', 'True', 'False'))"
                ))
            exists_sc = conn.execute(text(
                "SELECT 1 FROM pg_constraint WHERE conname = 'ck_llm_outputs_scenario_id'"
            )).fetchone()
            if not exists_sc:
                conn.execute(text(
                    "ALTER TABLE llm_outputs ADD CONSTRAINT ck_llm_outputs_scenario_id "
                    "CHECK (scenario_id BETWEEN 1 AND 3)"
                ))


def get_db():
    """Dependency to get database session."""
    db_engine = require_db()
    db = SessionLocal(bind=db_engine)
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    Creates the normalized tables:
    1. participants
    2. consent_decisions
    3. baseline_assessment
    4. scenario_responses
    5. llm_outputs
    6. post_scenario_survey
    7. end_of_study_survey
    8. sus_responses
    """
    if engine is None:
        logger.warning("Skipping DB initialization because database is not configured.")
        return
    # Ensure all model classes are imported so Base.metadata knows every table.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _ensure_schema_columns()
    from app.scenario_counters import sync_participant_scenario_counters
    sync_db = SessionLocal(bind=engine)
    try:
        sync_participant_scenario_counters(sync_db)
    finally:
        sync_db.close()
    _ensure_participant_views()
    from app.participant_state import sync_all_participant_completion_states
    db = SessionLocal(bind=engine)
    try:
        sync_all_participant_completion_states(db)
    finally:
        db.close()
    logger.info("Database tables initialized")


def reset_db() -> None:
    """
    Drop all tables and recreate them.
    WARNING: This will delete all data!
    """
    db_engine = require_db()
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    _ensure_schema_columns()
    from app.scenario_counters import sync_participant_scenario_counters
    sync_db = SessionLocal(bind=db_engine)
    try:
        sync_participant_scenario_counters(sync_db)
    finally:
        sync_db.close()
    _ensure_participant_views()
    logger.info("Database reset - all tables dropped and recreated")


def get_table_info() -> dict:
    """Get information about all tables in the database (for debugging)."""
    db_engine = require_db()
    tables = {}
    try:
        inspector = inspect(db_engine)
        with db_engine.connect() as conn:
            discovered = inspector.get_table_names()
            preferred_order = [
                "participants",
                "consent_decisions",
                "baseline_assessment",
                "scenario_responses",
                "llm_outputs",
                "participant_scenario_counters",
                "post_scenario_survey",
                "end_of_study_survey",
                "sus_responses",
            ]
            ordered_tables = [name for name in preferred_order if name in discovered]
            ordered_tables.extend([name for name in discovered if name not in preferred_order])

            for table_name in ordered_tables:
                columns_meta = inspector.get_columns(table_name)
                columns = [
                    {
                        "name": col.get("name"),
                        "type": str(col.get("type")),
                        "nullable": bool(col.get("nullable", True)),
                    }
                    for col in columns_meta
                ]
                count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
                tables[table_name] = {"columns": columns, "row_count": count}
    except Exception as e:
        logger.error(f"Error getting table info: {e}")

    return tables
