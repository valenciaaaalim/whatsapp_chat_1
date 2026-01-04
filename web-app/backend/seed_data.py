"""
Seed script to load conversations from annotated_test.json into the database.
"""
import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import Conversation

def load_conversations_from_json(json_path: Path) -> list:
    """Load conversations from annotated_test.json."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data.get("Conversations", [])


def seed_conversations(db: Session, conversations_data: list):
    """Seed conversations into database."""
    for conv_data in conversations_data:
        conversation_list = conv_data.get("Conversation", [])
        ground_truth = conv_data.get("GroundTruth", {})
        conversation_id = ground_truth.get("ConversationID")
        scenario = ground_truth.get("Scenario", "Unknown")
        is_malicious = ground_truth.get("IsMalicious", False)
        
        if conversation_id is None:
            print(f"Warning: Conversation missing ConversationID, skipping")
            continue
        
        # Check if conversation already exists
        existing = db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()
        
        if existing:
            print(f"Conversation {conversation_id} already exists, skipping")
            continue
        
        # Create conversation record
        conversation = Conversation(
            conversation_id=conversation_id,
            scenario=scenario,
            conversation_data={"Conversation": conversation_list},
            ground_truth=ground_truth,
            is_malicious=is_malicious
        )
        db.add(conversation)
        print(f"Added conversation {conversation_id}: {scenario}")
    
    db.commit()


def main():
    """Main seeding function."""
    # Initialize database
    init_db()
    
    # Find annotated_test.json
    # Try multiple possible locations (local development vs Docker)
    script_dir = Path(__file__).parent.resolve()
    possible_paths = [
        #Path("/app/annotated_test.json"),  # In Docker container (mounted)
        #script_dir.parent.parent / "annotated_test.json",  # From web-app/backend/ to repo root
        #script_dir / "annotated_test.json",  # Same directory
        script_dir/ "app/annotated_test.json",  # From web-app/ to repo root
    ]
    
    json_path = None
    for path in possible_paths:
        if path.exists():
            json_path = path
            break
    
    if not json_path:
        print(f"Error: annotated_test.json not found. Tried:")
        for path in possible_paths:
            print(f"  - {path}")
        sys.exit(1)
    
    # Load conversations
    print(f"Loading conversations from {json_path}")
    conversations_data = load_conversations_from_json(json_path)
    print(f"Found {len(conversations_data)} conversations")
    
    # Seed database
    db = SessionLocal()
    try:
        seed_conversations(db, conversations_data)
        print("Seeding completed successfully")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

