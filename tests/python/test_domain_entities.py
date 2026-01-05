"""
Tests for domain entities.

Tests pure domain logic without any infrastructure dependencies.
"""

from datetime import datetime

import pytest

from backend.domain.entities.message import Message, MessageRole
from backend.domain.entities.snippet import Snippet
from backend.domain.entities.story import (
    AGE_PHASE_MAPPING,
    AgeRange,
    Phase,
    Story,
    StoryStatus,
)
from backend.domain.entities.user import User
from backend.domain.exceptions import ValidationError


class TestUserEntity:
    """Tests for User domain entity."""

    def test_create_user_with_valid_email(self):
        """Should create user with valid email."""
        user = User(email="test@example.com", display_name="Test User")
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.is_active == True
        assert user.role == "user"

    def test_create_user_with_invalid_email_raises(self):
        """Should raise ValueError for invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid-email", display_name="Test")

    def test_user_is_admin_with_admin_role(self):
        """Should return True for admin role."""
        user = User(email="admin@test.com", role="admin")
        assert user.is_admin() == True

    def test_user_is_admin_with_superuser(self):
        """Should return True for superuser."""
        user = User(email="super@test.com", is_superuser=True)
        assert user.is_admin() == True

    def test_user_can_access_own_story(self):
        """User should be able to access their own story."""
        user = User(id=1, email="test@test.com")
        assert user.can_access_story(1) == True
        assert user.can_access_story(2) == False

    def test_admin_can_access_any_story(self):
        """Admin should be able to access any story."""
        admin = User(id=1, email="admin@test.com", role="admin")
        assert admin.can_access_story(999) == True

    def test_deactivate_user(self):
        """Should deactivate user."""
        user = User(email="test@test.com", is_active=True)
        user.deactivate()
        assert user.is_active == False


class TestStoryEntity:
    """Tests for Story domain entity."""

    def test_create_story_defaults(self):
        """Should create story with default values."""
        story = Story(user_id=1)
        assert story.current_phase == Phase.GREETING
        assert story.status == StoryStatus.DRAFT
        assert story.title == "Untitled Story"

    def test_set_age_range(self):
        """Should set age range and configure phases."""
        story = Story(user_id=1)
        story.set_age_range(AgeRange.AGE_31_45)
        assert story.age_range == AgeRange.AGE_31_45

    def test_set_age_range_twice_raises(self):
        """Should raise if age range already set."""
        story = Story(user_id=1)
        story.set_age_range(AgeRange.AGE_18_30)
        with pytest.raises(ValueError, match="Age range already set"):
            story.set_age_range(AgeRange.AGE_31_45)

    def test_available_phases_for_under_18(self):
        """Should return correct phases for under 18."""
        story = Story(user_id=1)
        story.set_age_range(AgeRange.UNDER_18)
        phases = story.available_phases
        assert Phase.EARLY_ADULTHOOD not in phases
        assert Phase.MIDLIFE not in phases
        assert Phase.CHILDHOOD in phases

    def test_available_phases_for_31_45(self):
        """Should return correct phases for 31-45."""
        story = Story(user_id=1)
        story.set_age_range(AgeRange.AGE_31_45)
        phases = story.available_phases
        assert Phase.EARLY_ADULTHOOD in phases
        assert Phase.MIDLIFE in phases

    def test_advance_phase(self):
        """Should advance to next phase."""
        story = Story(user_id=1, current_phase=Phase.GREETING)
        story.set_age_range(AgeRange.AGE_31_45)
        story.advance_phase()
        assert story.current_phase == Phase.AGE_SELECTION

    def test_advance_phase_at_end_raises(self):
        """Should raise if at final phase."""
        story = Story(user_id=1, current_phase=Phase.SYNTHESIS)
        story.set_age_range(AgeRange.AGE_31_45)
        with pytest.raises(ValueError, match="Already at final phase"):
            story.advance_phase()

    def test_progress_percentage(self):
        """Should calculate progress correctly."""
        story = Story(user_id=1, current_phase=Phase.GREETING)
        story.set_age_range(AgeRange.AGE_31_45)
        assert story.progress_percentage == 0.0

        story.current_phase = Phase.SYNTHESIS
        assert story.progress_percentage == 100.0

    def test_jump_to_phase(self):
        """Should jump to specific phase."""
        story = Story(user_id=1, current_phase=Phase.GREETING)
        story.set_age_range(AgeRange.AGE_31_45)
        story.jump_to_phase(Phase.CHILDHOOD)
        assert story.current_phase == Phase.CHILDHOOD


class TestMessageEntity:
    """Tests for Message domain entity."""

    def test_create_message(self):
        """Should create message with valid content."""
        msg = Message(story_id=1, role=MessageRole.USER, content="Hello!")
        assert msg.content == "Hello!"
        assert msg.role == MessageRole.USER

    def test_create_message_empty_content_raises(self):
        """Should raise for empty content."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Message(story_id=1, role=MessageRole.USER, content="")

    def test_is_user_message(self):
        """Should identify user message."""
        msg = Message(story_id=1, role=MessageRole.USER, content="test")
        assert msg.is_user_message == True
        assert msg.is_assistant_message == False

    def test_to_dict(self):
        """Should convert to dictionary."""
        msg = Message(id=1, story_id=2, role=MessageRole.ASSISTANT, content="Hello!")
        d = msg.to_dict()
        assert d["id"] == 1
        assert d["story_id"] == 2
        assert d["role"] == "assistant"
        assert d["content"] == "Hello!"


class TestSnippetEntity:
    """Tests for Snippet domain entity."""

    def test_create_snippet(self):
        """Should create snippet."""
        snippet = Snippet(
            story_id=1,
            user_id=1,
            title="My Memory",
            content="A great memory from childhood",
            theme="family",
        )
        assert snippet.title == "My Memory"
        assert snippet.is_locked == False
        assert snippet.is_active == True

    def test_truncate_long_title(self):
        """Should truncate title over 100 chars."""
        long_title = "A" * 150
        snippet = Snippet(story_id=1, title=long_title, content="test")
        assert len(snippet.title) == 100

    def test_truncate_long_content(self):
        """Should truncate content over 500 chars."""
        long_content = "B" * 600
        snippet = Snippet(story_id=1, title="Test", content=long_content)
        assert len(snippet.content) == 500

    def test_toggle_lock(self):
        """Should toggle lock state."""
        snippet = Snippet(story_id=1, title="Test", content="test")
        assert snippet.is_locked == False
        snippet.toggle_lock()
        assert snippet.is_locked == True
        snippet.toggle_lock()
        assert snippet.is_locked == False

    def test_archive_and_restore(self):
        """Should archive and restore."""
        snippet = Snippet(story_id=1, title="Test", content="test")
        assert snippet.is_active == True
        snippet.archive()
        assert snippet.is_active == False
        assert snippet.is_archived == True
        snippet.restore()
        assert snippet.is_active == True
