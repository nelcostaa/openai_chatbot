#!/usr/bin/env python3
"""Create test data for interview endpoint testing."""

from sqlalchemy.orm import sessionmaker

from backend.app.db.base import Base  # Import all models
from backend.app.db.session import engine
from backend.app.models.story import Story
from backend.app.models.user import User

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Check if test user exists
    test_user = db.query(User).filter(User.email == "test@example.com").first()

    if not test_user:
        test_user = User(
            email="test@example.com",
            hashed_password="$2b$12$fake_hash_for_testing",
            display_name="Test User",
            is_active=True,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user ID: {test_user.id}")
    else:
        print(f"✅ Test user ID: {test_user.id}")

    # Check if test story exists
    test_story = db.query(Story).filter(Story.user_id == test_user.id).first()

    if not test_story:
        test_story = Story(
            user_id=test_user.id,
            title="My Life Story",
            current_phase="GREETING",
            status="draft",
        )
        db.add(test_story)
        db.commit()
        db.refresh(test_story)
        print(f"✅ Created test story ID: {test_story.id}")
    else:
        print(f"✅ Test story ID: {test_story.id}")

    print(f"\n📊 USE THIS STORY_ID FOR TESTING: {test_story.id}")
    print(f"📊 Current Phase: {test_story.current_phase}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    db.close()
