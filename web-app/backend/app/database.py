"""
Database setup and session management.
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Create database engine
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite-specific
    )
else:
    engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def migrate_participant_records_columns():
    """
    Idempotent migration to add final_masked_* and final_rewrite_* columns.
    Uses PRAGMA table_info to check for existing columns before adding.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        logger.info("Migration only supported for SQLite databases")
        return
    
    columns_to_add = [
        ('final_masked_1', 'TEXT'),
        ('final_rewrite_1', 'TEXT'),
        ('final_masked_2', 'TEXT'),
        ('final_rewrite_2', 'TEXT'),
        ('final_masked_3', 'TEXT'),
        ('final_rewrite_3', 'TEXT'),
    ]
    
    try:
        with engine.begin() as conn:  # Use begin() for automatic transaction management
            # Get existing columns
            result = conn.execute(text("PRAGMA table_info('participant_records')"))
            existing_columns = {row[1] for row in result}
            
            # Add missing columns
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    logger.info(f"Adding column {column_name} to participant_records")
                    conn.execute(text(f"ALTER TABLE participant_records ADD COLUMN {column_name} {column_type} NULL"))
                else:
                    logger.debug(f"Column {column_name} already exists, skipping")
        
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


def reorder_participant_records_columns():
    """
    Rebuild participant_records with a consistent column order for analysis.
    This is SQLite-only and is idempotent (skips if order already matches).
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        logger.info("Reorder migration only supported for SQLite databases")
        return

    desired_columns = [
        ("prolific_id", "TEXT PRIMARY KEY"),
        ("variant", "TEXT"),
        ("created_at", "DATETIME"),
        ("completed_at", "DATETIME"),
        ("duration_of_study", "FLOAT"),
        ("pre_1", "TEXT"),
        ("pre_2", "TEXT"),
        ("pre_3", "TEXT"),
        ("pre_4", "TEXT"),
        ("midA_1_q1", "TEXT"),
        ("midA_1_q2", "TEXT"),
        ("midA_1_q3", "TEXT"),
        ("midA_2_q1", "TEXT"),
        ("midA_2_q2", "TEXT"),
        ("midA_2_q3", "TEXT"),
        ("midA_3_q1", "TEXT"),
        ("midA_3_q2", "TEXT"),
        ("midA_3_q3", "TEXT"),
        ("midB_1_q1", "TEXT"),
        ("midB_1_q2", "TEXT"),
        ("midB_1_q3", "TEXT"),
        ("midB_2_q1", "TEXT"),
        ("midB_2_q2", "TEXT"),
        ("midB_2_q3", "TEXT"),
        ("midB_3_q1", "TEXT"),
        ("midB_3_q2", "TEXT"),
        ("midB_3_q3", "TEXT"),
        ("sus_1", "TEXT"),
        ("sus_2", "TEXT"),
        ("sus_3", "TEXT"),
        ("sus_4", "TEXT"),
        ("sus_5", "TEXT"),
        ("sus_6", "TEXT"),
        ("sus_7", "TEXT"),
        ("sus_8", "TEXT"),
        ("sus_9", "TEXT"),
        ("sus_10", "TEXT"),
        ("post_trust", "TEXT"),
        ("post_realism", "TEXT"),
    ]
    # Group by scenario: input/masked/rewrite/msg + midA questions for each scenario
    desired_columns = (
        desired_columns[:9]
        + [
            ("input_1", "TEXT"),
            ("final_masked_1", "TEXT"),
            ("final_rewrite_1", "TEXT"),
            ("msg_1", "TEXT"),
            ("midA_1_q1", "TEXT"),
            ("midA_1_q2", "TEXT"),
            ("midA_1_q3", "TEXT"),
            ("input_2", "TEXT"),
            ("final_masked_2", "TEXT"),
            ("final_rewrite_2", "TEXT"),
            ("msg_2", "TEXT"),
            ("midA_2_q1", "TEXT"),
            ("midA_2_q2", "TEXT"),
            ("midA_2_q3", "TEXT"),
            ("input_3", "TEXT"),
            ("final_masked_3", "TEXT"),
            ("final_rewrite_3", "TEXT"),
            ("msg_3", "TEXT"),
            ("midA_3_q1", "TEXT"),
            ("midA_3_q2", "TEXT"),
            ("midA_3_q3", "TEXT"),
        ]
        + [
            ("midB_1_q1", "TEXT"),
            ("midB_1_q2", "TEXT"),
            ("midB_1_q3", "TEXT"),
            ("midB_2_q1", "TEXT"),
            ("midB_2_q2", "TEXT"),
            ("midB_2_q3", "TEXT"),
            ("midB_3_q1", "TEXT"),
            ("midB_3_q2", "TEXT"),
            ("midB_3_q3", "TEXT"),
            ("sus_1", "TEXT"),
            ("sus_2", "TEXT"),
            ("sus_3", "TEXT"),
            ("sus_4", "TEXT"),
            ("sus_5", "TEXT"),
            ("sus_6", "TEXT"),
            ("sus_7", "TEXT"),
            ("sus_8", "TEXT"),
            ("sus_9", "TEXT"),
            ("sus_10", "TEXT"),
            ("post_trust", "TEXT"),
            ("post_realism", "TEXT"),
        ]
    )

    desired_names = [name for name, _ in desired_columns]

    try:
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info('participant_records')"))
            existing_columns = [row[1] for row in result]
            if not existing_columns:
                logger.info("participant_records not found; skipping reorder migration")
                return

            if existing_columns == desired_names:
                logger.info("participant_records already in desired column order")
                return

            logger.info("Rebuilding participant_records to enforce column order")
            columns_sql = ", ".join([f"{name} {col_type}" for name, col_type in desired_columns])
            conn.execute(text(f"CREATE TABLE participant_records_new ({columns_sql})"))

            select_exprs = []
            existing_set = set(existing_columns)
            for name in desired_names:
                if name in existing_set:
                    select_exprs.append(name)
                else:
                    select_exprs.append(f"NULL AS {name}")

            insert_cols = ", ".join(desired_names)
            select_cols = ", ".join(select_exprs)
            conn.execute(text(
                f"INSERT INTO participant_records_new ({insert_cols}) "
                f"SELECT {select_cols} FROM participant_records"
            ))

            conn.execute(text("DROP TABLE participant_records"))
            conn.execute(text("ALTER TABLE participant_records_new RENAME TO participant_records"))
            logger.info("participant_records reorder migration completed")
    except Exception as e:
        logger.error(f"Reorder migration failed: {e}", exc_info=True)
        raise
