"""
Unit tests for backend/app/services/snippets.py and backend/app/api/endpoints/snippets.py

Tests the snippet generation service and API endpoint.
Includes TDD tests for persistent snippets feature.
Includes tests for lock, soft-delete, archive, and restore functionality.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.main import app
from backend.app.models.snippets import Snippet
from backend.app.services.snippets import SnippetService, get_model_cascade

client = TestClient(app)


# --- Fixtures ---


@pytest.fixture
def sample_messages_in_db(mock_db_session, sample_story):
    """Create sample messages in the database for a story."""
    from backend.app.models.message import Message

    messages = [
        Message(
            story_id=sample_story.id,
            role="user",
            content="I grew up in a small town in Portugal.",
            phase_context="CHILDHOOD",
        ),
        Message(
            story_id=sample_story.id,
            role="assistant",
            content="That sounds lovely! What was your favorite childhood memory?",
            phase_context="CHILDHOOD",
        ),
        Message(
            story_id=sample_story.id,
            role="user",
            content="Playing soccer with my friends in the village square every evening.",
            phase_context="CHILDHOOD",
        ),
        Message(
            story_id=sample_story.id,
            role="assistant",
            content="What wonderful memories! Did you continue playing as you grew older?",
            phase_context="CHILDHOOD",
        ),
    ]

    for msg in messages:
        mock_db_session.add(msg)
    mock_db_session.commit()

    return messages


@pytest.fixture
def mock_gemini_snippets_response():
    """Mock Gemini response with valid snippet JSON."""
    return AIMessage(
        content=json.dumps(
            {
                "snippets": [
                    {
                        "title": "Village Soccer Days",
                        "content": "Growing up in a small Portuguese town, they spent every evening playing soccer with friends in the village square.",
                        "phase": "CHILDHOOD",
                        "theme": "friendship",
                    },
                    {
                        "title": "Roots in Portugal",
                        "content": "Their childhood was shaped by the warmth of a tight-knit community in rural Portugal.",
                        "phase": "CHILDHOOD",
                        "theme": "family",
                    },
                ]
            }
        )
    )


# --- SnippetService Tests ---


class TestSnippetService:
    """Tests for SnippetService class."""

    def test_get_story_messages_returns_correct_format(
        self, mock_db_session, sample_story, sample_messages_in_db
    ):
        """Should return messages as list of dicts with role and content."""
        service = SnippetService(mock_db_session)
        messages = service.get_story_messages(sample_story.id)

        assert len(messages) == 4
        assert all("role" in msg and "content" in msg for msg in messages)
        assert messages[0]["role"] == "user"
        assert "Portugal" in messages[0]["content"]

    def test_get_story_messages_empty_story(self, mock_db_session, sample_story):
        """Should return empty list for story with no messages."""
        service = SnippetService(mock_db_session)
        messages = service.get_story_messages(sample_story.id)

        assert messages == []

    def test_generate_snippets_story_not_found(self, mock_db_session):
        """Should return error for non-existent story."""
        service = SnippetService(mock_db_session)
        result = service.generate_snippets(99999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_generate_snippets_no_messages(self, mock_db_session, sample_story):
        """Should return error when story has no messages."""
        service = SnippetService(mock_db_session)
        result = service.generate_snippets(sample_story.id)

        assert result["success"] is False
        assert "no messages" in result["error"].lower()

    def test_generate_snippets_success(
        self,
        mock_db_session,
        sample_story,
        sample_messages_in_db,
        mock_gemini_snippets_response,
    ):
        """Should generate snippets successfully with mocked Gemini."""
        service = SnippetService(mock_db_session)

        with patch("backend.app.services.snippets.ChatGoogleGenerativeAI") as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = mock_gemini_snippets_response
            MockLLM.return_value = mock_llm_instance

            result = service.generate_snippets(sample_story.id)

            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["snippets"]) == 2
            assert result["snippets"][0]["title"] == "Village Soccer Days"
            assert result["snippets"][0]["theme"] == "friendship"

    def test_generate_snippets_model_cascade(
        self,
        mock_db_session,
        sample_story,
        sample_messages_in_db,
        mock_gemini_snippets_response,
    ):
        """Should try fallback models on rate limit."""
        service = SnippetService(mock_db_session)

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 Resource exhausted")
            return mock_gemini_snippets_response

        with patch("backend.app.services.snippets.ChatGoogleGenerativeAI") as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.side_effect = side_effect
            MockLLM.return_value = mock_llm_instance

            result = service.generate_snippets(sample_story.id)

            # Should succeed after fallback
            assert result["success"] is True
            assert call_count == 2  # First failed, second succeeded


class TestSnippetServiceParsing:
    """Tests for _parse_response method."""

    def test_parse_valid_json(self, mock_db_session):
        """Should parse valid JSON correctly."""
        service = SnippetService(mock_db_session)
        response = json.dumps(
            {
                "snippets": [
                    {
                        "title": "Test",
                        "content": "Test content",
                        "phase": "CHILDHOOD",
                        "theme": "growth",
                    }
                ]
            }
        )

        result = service._parse_response(response, "test-model")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["model"] == "test-model"

    def test_parse_json_with_markdown_fence(self, mock_db_session):
        """Should handle JSON wrapped in markdown code blocks."""
        service = SnippetService(mock_db_session)
        response = """```json
{
    "snippets": [
        {"title": "Test", "content": "Content here", "phase": "PRESENT", "theme": "legacy"}
    ]
}
```"""

        result = service._parse_response(response, "test-model")

        assert result["success"] is True
        assert result["count"] == 1

    def test_parse_truncates_long_content(self, mock_db_session):
        """Should truncate content over 300 characters."""
        service = SnippetService(mock_db_session)
        long_content = "A" * 350  # 350 characters
        response = json.dumps(
            {
                "snippets": [
                    {
                        "title": "Test",
                        "content": long_content,
                        "phase": "CHILDHOOD",
                        "theme": "growth",
                    }
                ]
            }
        )

        result = service._parse_response(response, "test-model")

        assert result["success"] is True
        assert len(result["snippets"][0]["content"]) == 300
        assert result["snippets"][0]["content"].endswith("...")

    def test_parse_invalid_json(self, mock_db_session):
        """Should return error for invalid JSON."""
        service = SnippetService(mock_db_session)
        result = service._parse_response("not valid json {{{", "test-model")

        assert result["success"] is False
        assert "json" in result["error"].lower()

    def test_parse_skips_invalid_snippets(self, mock_db_session):
        """Should skip snippets missing required fields."""
        service = SnippetService(mock_db_session)
        response = json.dumps(
            {
                "snippets": [
                    {
                        "title": "Valid",
                        "content": "Has content",
                        "phase": "CHILDHOOD",
                        "theme": "growth",
                    },
                    {"title": "", "content": "No title"},  # Invalid - empty title
                    {"title": "No content", "content": ""},  # Invalid - empty content
                    "not a dict",  # Invalid - not a dict
                ]
            }
        )

        result = service._parse_response(response, "test-model")

        assert result["success"] is True
        assert result["count"] == 1  # Only valid snippet


class TestGetModelCascade:
    """Tests for get_model_cascade function."""

    def test_returns_default_models(self):
        """Should return default models when env not set."""
        import os

        # Clear env var if set
        env_models = os.environ.pop("GEMINI_MODELS", None)

        try:
            models = get_model_cascade()
            assert len(models) > 0
            # First model should be gemma (our primary) or gemini (fallback)
            first_model = models[0].lower()
            assert "gemma" in first_model or "gemini" in first_model
        finally:
            # Restore env var
            if env_models:
                os.environ["GEMINI_MODELS"] = env_models

    def test_reads_from_environment(self):
        """Should read models from GEMINI_MODELS env var."""
        import os

        os.environ["GEMINI_MODELS"] = "model-a, model-b, model-c"

        try:
            models = get_model_cascade()
            assert models == ["model-a", "model-b", "model-c"]
        finally:
            del os.environ["GEMINI_MODELS"]


# --- Endpoint Tests ---


class TestSnippetsEndpoint:
    """Tests for POST /api/snippets/{story_id} endpoint."""

    def test_generate_snippets_unauthorized(self):
        """Should reject request without authentication."""
        response = client.post("/api/snippets/1")
        assert response.status_code == 401

    def test_generate_snippets_story_not_found(self, mock_db_session, sample_user):
        """Should return 404 for non-existent story."""
        from backend.app.api.endpoints.snippets import router
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post("/api/snippets/99999")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides = {}

    def test_generate_snippets_forbidden_other_user(
        self, mock_db_session, sample_user, sample_story
    ):
        """Should return 403 when user doesn't own story."""
        from backend.app.api.endpoints.snippets import router
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db
        from backend.app.models.user import User

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="fake_hash",
            display_name="Other User",
            is_active=True,
        )
        mock_db_session.add(other_user)
        mock_db_session.commit()
        mock_db_session.refresh(other_user)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return other_user  # Different user than story owner

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post(f"/api/snippets/{sample_story.id}")
            assert response.status_code == 403
            assert "not authorized" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides = {}

    def test_generate_snippets_success(
        self,
        mock_db_session,
        sample_user,
        sample_story,
        sample_messages_in_db,
        mock_gemini_snippets_response,
    ):
        """Should return snippets on successful generation.

        Tests the service layer directly to avoid TestClient session isolation
        issues with in-memory SQLite.
        """
        service = SnippetService(mock_db_session)

        with patch("backend.app.services.snippets.ChatGoogleGenerativeAI") as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = mock_gemini_snippets_response
            MockLLM.return_value = mock_llm_instance

            result = service.generate_snippets(sample_story.id)

            assert result["success"] is True
            assert result["count"] == 2
            assert len(result["snippets"]) == 2
            assert result["snippets"][0]["title"] == "Village Soccer Days"

            # Also verify snippets were persisted
            saved = (
                mock_db_session.query(Snippet)
                .filter(Snippet.story_id == sample_story.id)
                .all()
            )
            assert len(saved) == 2

    def test_generate_snippets_no_messages_returns_error_in_body(
        self, mock_db_session, sample_user, sample_story
    ):
        """Should return success=False in body when no messages (not HTTP error)."""
        from backend.app.api.endpoints.snippets import router
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post(f"/api/snippets/{sample_story.id}")

            assert response.status_code == 200  # HTTP 200, but success=False in body
            data = response.json()
            assert data["success"] is False
            assert "no messages" in data["error"].lower()
        finally:
            app.dependency_overrides = {}
            app.dependency_overrides = {}


# =============================================================================
# TDD TESTS FOR PERSISTENT SNIPPETS FEATURE
# These tests are written FIRST (TDD) and should FAIL until implementation
# =============================================================================


class TestSnippetModelPersistence:
    """TDD tests for Snippet model with all required columns."""

    def test_snippet_model_has_title_column(
        self, mock_db_session, sample_story, sample_user
    ):
        """Snippet model should have title column."""
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Test Title",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        assert snippet.title == "Test Title"

    def test_snippet_model_has_theme_column(
        self, mock_db_session, sample_story, sample_user
    ):
        """Snippet model should have theme column."""
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Test",
            content="Test content",
            theme="friendship",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        assert snippet.theme == "friendship"

    def test_snippet_model_has_phase_column(
        self, mock_db_session, sample_story, sample_user
    ):
        """Snippet model should have phase column."""
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Test",
            content="Test content",
            theme="growth",
            phase="YOUNG_ADULT",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        assert snippet.phase == "YOUNG_ADULT"

    def test_story_has_snippets_relationship(
        self, mock_db_session, sample_story, sample_user
    ):
        """Story model should have snippets relationship."""
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Test",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(sample_story)

        # Story should have snippets attribute that returns list
        assert hasattr(sample_story, "snippets")
        assert len(sample_story.snippets) == 1
        assert sample_story.snippets[0].title == "Test"

    def test_user_has_snippets_relationship(
        self, mock_db_session, sample_story, sample_user
    ):
        """User model should have snippets relationship."""
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Test",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(sample_user)

        # User should have snippets attribute that returns list
        assert hasattr(sample_user, "snippets")
        assert len(sample_user.snippets) == 1


class TestSnippetServicePersistence:
    """TDD tests for SnippetService persistence functionality."""

    def test_generate_snippets_saves_to_database(
        self,
        mock_db_session,
        sample_story,
        sample_user,
        sample_messages_in_db,
        mock_gemini_snippets_response,
    ):
        """generate_snippets should persist snippets to database."""
        service = SnippetService(mock_db_session)

        with patch("backend.app.services.snippets.ChatGoogleGenerativeAI") as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = mock_gemini_snippets_response
            MockLLM.return_value = mock_llm_instance

            result = service.generate_snippets(sample_story.id)

            assert result["success"] is True

            # Verify snippets were saved to database
            saved_snippets = (
                mock_db_session.query(Snippet)
                .filter(Snippet.story_id == sample_story.id)
                .all()
            )
            assert len(saved_snippets) == 2
            assert saved_snippets[0].title == "Village Soccer Days"
            assert saved_snippets[0].theme == "friendship"
            assert saved_snippets[0].phase == "CHILDHOOD"

    def test_get_existing_snippets_returns_cached(
        self, mock_db_session, sample_story, sample_user
    ):
        """get_existing_snippets should return snippets from database."""
        # Pre-populate database with snippets
        snippet1 = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Cached Snippet 1",
            content="Content 1",
            theme="growth",
            phase="CHILDHOOD",
        )
        snippet2 = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Cached Snippet 2",
            content="Content 2",
            theme="family",
            phase="YOUNG_ADULT",
        )
        mock_db_session.add_all([snippet1, snippet2])
        mock_db_session.commit()

        service = SnippetService(mock_db_session)
        result = service.get_existing_snippets(sample_story.id)

        assert result["success"] is True
        assert result["count"] == 2
        assert result["cached"] is True
        assert result["snippets"][0]["title"] == "Cached Snippet 1"

    def test_get_existing_snippets_empty_when_none(self, mock_db_session, sample_story):
        """get_existing_snippets should return empty when no snippets exist."""
        service = SnippetService(mock_db_session)
        result = service.get_existing_snippets(sample_story.id)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["cached"] is False
        assert result["snippets"] == []

    def test_delete_snippets_removes_from_database(
        self, mock_db_session, sample_story, sample_user
    ):
        """delete_snippets should remove all snippets for a story."""
        # Pre-populate database
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="To Delete",
            content="Content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()

        service = SnippetService(mock_db_session)
        service.delete_snippets(sample_story.id)

        # Note: delete_snippets now soft-deletes by setting is_active=False
        # Verify snippet is soft-deleted (still in DB but is_active=False)
        remaining = (
            mock_db_session.query(Snippet)
            .filter(Snippet.story_id == sample_story.id)
            .all()
        )
        assert len(remaining) == 1  # Still exists
        assert remaining[0].is_active is False  # But is soft-deleted


class TestSnippetsEndpointCaching:
    """TDD tests for GET endpoint and caching behavior."""

    def test_get_snippets_returns_cached(
        self, mock_db_session, sample_user, sample_story
    ):
        """GET /api/snippets/{story_id} should return cached snippets."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Pre-populate database
        snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Cached",
            content="Content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(f"/api/snippets/{sample_story.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cached"] is True
            assert data["count"] == 1
            assert data["snippets"][0]["title"] == "Cached"
        finally:
            app.dependency_overrides = {}

    def test_get_snippets_empty_when_none(
        self, mock_db_session, sample_user, sample_story
    ):
        """GET /api/snippets/{story_id} should return empty when no snippets."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(f"/api/snippets/{sample_story.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cached"] is False
            assert data["count"] == 0
        finally:
            app.dependency_overrides = {}

    def test_post_snippets_clears_existing_before_regenerate(
        self,
        mock_db_session,
        sample_user,
        sample_story,
        sample_messages_in_db,
        mock_gemini_snippets_response,
    ):
        """POST should clear existing snippets before regenerating.

        This tests the service layer directly since the endpoint test has
        session isolation issues with in-memory SQLite.
        """
        # Pre-populate with old snippets
        old_snippet = Snippet(
            story_id=sample_story.id,
            user_id=sample_user.id,
            title="Old Snippet",
            content="Old content",
            theme="legacy",
            phase="PRESENT",
        )
        mock_db_session.add(old_snippet)
        mock_db_session.commit()

        # Verify old snippet exists
        old_count = (
            mock_db_session.query(Snippet)
            .filter(Snippet.story_id == sample_story.id)
            .count()
        )
        assert old_count == 1

        # Use service directly instead of HTTP endpoint
        service = SnippetService(mock_db_session)

        with patch("backend.app.services.snippets.ChatGoogleGenerativeAI") as MockLLM:
            mock_llm_instance = Mock()
            mock_llm_instance.invoke.return_value = mock_gemini_snippets_response
            MockLLM.return_value = mock_llm_instance

            result = service.generate_snippets(sample_story.id)

            assert result["success"] is True

        # Verify old snippets are soft-deleted, new ones exist
        # Note: delete_snippets now soft-deletes (is_active=False) instead of hard-deleting
        active_snippets = (
            mock_db_session.query(Snippet)
            .filter(Snippet.story_id == sample_story.id)
            .filter(Snippet.is_active == True)
            .all()
        )
        assert len(active_snippets) == 2  # New snippets only (active)
        titles = [s.title for s in active_snippets]
        assert "Old Snippet" not in titles
        assert "Village Soccer Days" in titles

    def test_get_snippets_unauthorized(self):
        """GET should reject unauthorized requests."""
        response = client.get("/api/snippets/1")
        assert response.status_code == 401

    def test_get_snippets_forbidden_other_user(
        self, mock_db_session, sample_user, sample_story
    ):
        """GET should return 403 when user doesn't own story."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db
        from backend.app.models.user import User

        other_user = User(
            email="other@example.com",
            hashed_password="fake_hash",
            display_name="Other User",
            is_active=True,
        )
        mock_db_session.add(other_user)
        mock_db_session.commit()
        mock_db_session.refresh(other_user)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return other_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(f"/api/snippets/{sample_story.id}")
            assert response.status_code == 403
        finally:
            app.dependency_overrides = {}


class TestUpdateSnippetEndpoint:
    """Tests for PUT /api/snippets/{snippet_id} endpoint."""

    def test_update_snippet_unauthorized(self):
        """PUT should reject unauthorized requests."""
        response = client.put("/api/snippets/1", json={"title": "New Title"})
        assert response.status_code == 401

    def test_update_snippet_not_found(self, mock_db_session, sample_user):
        """PUT should return 404 for non-existent snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.put("/api/snippets/99999", json={"title": "New Title"})
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides = {}

    def test_update_snippet_forbidden_other_user(
        self, mock_db_session, sample_user, sample_story
    ):
        """PUT should return 403 when user doesn't own the snippet's story."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db
        from backend.app.models.user import User

        # Create a snippet owned by sample_user
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Original Title",
            content="Original content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password="fake_hash",
            display_name="Other User",
            is_active=True,
        )
        mock_db_session.add(other_user)
        mock_db_session.commit()
        mock_db_session.refresh(other_user)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return other_user  # Not the owner

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.put(
                f"/api/snippets/{snippet.id}", json={"title": "Hacked Title"}
            )
            assert response.status_code == 403
            assert "not authorized" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides = {}

    def test_update_snippet_success_title_only(
        self, mock_db_session, sample_user, sample_story
    ):
        """PUT should update only the title when only title is provided."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            # Create a snippet AFTER setting up overrides
            snippet = Snippet(
                user_id=sample_user.id,
                story_id=sample_story.id,
                title="Original Title",
                content="Original content",
                theme="growth",
                phase="CHILDHOOD",
            )
            mock_db_session.add(snippet)
            mock_db_session.commit()
            mock_db_session.refresh(snippet)

            response = client.put(
                f"/api/snippets/{snippet.id}", json={"title": "Updated Title"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Title"
            assert data["content"] == "Original content"  # Unchanged
            assert data["theme"] == "growth"  # Unchanged
            assert data["phase"] == "CHILDHOOD"  # Unchanged
        finally:
            app.dependency_overrides = {}

    def test_update_snippet_success_all_fields(
        self, mock_db_session, sample_user, sample_story
    ):
        """PUT should update all provided fields."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Create a snippet
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Original Title",
            content="Original content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.put(
                f"/api/snippets/{snippet.id}",
                json={
                    "title": "New Title",
                    "content": "New content for the card",
                    "theme": "adventure",
                    "phase": "EARLY_ADULTHOOD",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Title"
            assert data["content"] == "New content for the card"
            assert data["theme"] == "adventure"
            assert data["phase"] == "EARLY_ADULTHOOD"
            assert data["id"] == snippet.id
        finally:
            app.dependency_overrides = {}

    def test_update_snippet_truncates_long_content(
        self, mock_db_session, sample_user, sample_story
    ):
        """PUT should truncate content over 300 characters."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Create a snippet
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Original Title",
            content="Original content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            long_content = "A" * 350  # Over 300 chars
            response = client.put(
                f"/api/snippets/{snippet.id}", json={"content": long_content}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["content"]) == 300
            assert data["content"] == "A" * 300
        finally:
            app.dependency_overrides = {}

    def test_update_snippet_truncates_long_title(
        self, mock_db_session, sample_user, sample_story
    ):
        """PUT should truncate title over 200 characters."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Create a snippet
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Original Title",
            content="Original content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            long_title = "B" * 250  # Over 200 chars
            response = client.put(
                f"/api/snippets/{snippet.id}", json={"title": long_title}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["title"]) == 200
            assert data["title"] == "B" * 200
        finally:
            app.dependency_overrides = {}


# =============================================================================
# LOCK, ARCHIVE, RESTORE TESTS
# =============================================================================


class TestSnippetServiceLockAndArchive:
    """Tests for snippet lock, soft-delete, and archive functionality in SnippetService."""

    def test_snippet_default_values(self, mock_db_session, sample_user, sample_story):
        """New snippets should have is_locked=False and is_active=True by default."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test Snippet",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        assert snippet.is_locked is False
        assert snippet.is_active is True

    def test_toggle_lock(self, mock_db_session, sample_user, sample_story):
        """toggle_lock should flip the is_locked state."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test Snippet",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
            is_locked=False,
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        service = SnippetService(mock_db_session)

        # Toggle to locked
        result = service.toggle_lock(snippet.id)
        assert result is not None
        assert result["is_locked"] is True

        # Toggle back to unlocked
        result = service.toggle_lock(snippet.id)
        assert result["is_locked"] is False

    def test_toggle_lock_not_found(self, mock_db_session):
        """toggle_lock should return None for non-existent snippet."""
        service = SnippetService(mock_db_session)
        result = service.toggle_lock(99999)
        assert result is None

    def test_soft_delete_snippet(self, mock_db_session, sample_user, sample_story):
        """soft_delete_snippet should set is_active to False."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test Snippet",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        service = SnippetService(mock_db_session)
        result = service.soft_delete_snippet(snippet.id)

        assert result is not None
        assert result["is_active"] is False

    def test_restore_snippet(self, mock_db_session, sample_user, sample_story):
        """restore_snippet should set is_active back to True."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test Snippet",
            content="Test content",
            theme="growth",
            phase="CHILDHOOD",
            is_active=False,  # Start as archived
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        service = SnippetService(mock_db_session)
        result = service.restore_snippet(snippet.id)

        assert result is not None
        assert result["is_active"] is True

    def test_get_existing_snippets_excludes_archived(
        self, mock_db_session, sample_user, sample_story
    ):
        """get_existing_snippets should only return active snippets by default."""
        # Create active snippet
        active_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Active Snippet",
            content="Active content",
            theme="growth",
            phase="CHILDHOOD",
            is_active=True,
        )
        # Create archived snippet
        archived_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Archived Snippet",
            content="Archived content",
            theme="family",
            phase="PRESENT",
            is_active=False,
        )
        mock_db_session.add(active_snippet)
        mock_db_session.add(archived_snippet)
        mock_db_session.commit()

        service = SnippetService(mock_db_session)
        result = service.get_existing_snippets(sample_story.id)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["snippets"][0]["title"] == "Active Snippet"

    def test_get_archived_snippets(self, mock_db_session, sample_user, sample_story):
        """get_archived_snippets should only return archived (is_active=False) snippets."""
        # Create active snippet
        active_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Active Snippet",
            content="Active content",
            theme="growth",
            phase="CHILDHOOD",
            is_active=True,
        )
        # Create archived snippet
        archived_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Archived Snippet",
            content="Archived content",
            theme="family",
            phase="PRESENT",
            is_active=False,
        )
        mock_db_session.add(active_snippet)
        mock_db_session.add(archived_snippet)
        mock_db_session.commit()

        service = SnippetService(mock_db_session)
        result = service.get_archived_snippets(sample_story.id)

        assert result["success"] is True
        assert result["count"] == 1
        assert result["snippets"][0]["title"] == "Archived Snippet"

    def test_delete_snippets_preserves_locked(
        self, mock_db_session, sample_user, sample_story
    ):
        """delete_snippets should only soft-delete unlocked snippets."""
        # Create locked snippet
        locked_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Locked Snippet",
            content="Locked content",
            theme="growth",
            phase="CHILDHOOD",
            is_locked=True,
            is_active=True,
        )
        # Create unlocked snippet
        unlocked_snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Unlocked Snippet",
            content="Unlocked content",
            theme="family",
            phase="PRESENT",
            is_locked=False,
            is_active=True,
        )
        mock_db_session.add(locked_snippet)
        mock_db_session.add(unlocked_snippet)
        mock_db_session.commit()
        mock_db_session.refresh(locked_snippet)
        mock_db_session.refresh(unlocked_snippet)

        service = SnippetService(mock_db_session)
        deleted_count = service.delete_snippets(sample_story.id)

        # Should only soft-delete the unlocked one
        assert deleted_count == 1

        # Refresh to get updated state
        mock_db_session.refresh(locked_snippet)
        mock_db_session.refresh(unlocked_snippet)

        # Locked snippet should still be active
        assert locked_snippet.is_active is True
        # Unlocked snippet should be archived
        assert unlocked_snippet.is_active is False

    def test_get_locked_snippet_count(self, mock_db_session, sample_user, sample_story):
        """get_locked_snippet_count should return correct count."""
        # Create locked snippet
        locked1 = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Locked 1",
            content="Content",
            is_locked=True,
            is_active=True,
        )
        locked2 = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Locked 2",
            content="Content",
            is_locked=True,
            is_active=True,
        )
        unlocked = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Unlocked",
            content="Content",
            is_locked=False,
            is_active=True,
        )
        mock_db_session.add_all([locked1, locked2, unlocked])
        mock_db_session.commit()

        service = SnippetService(mock_db_session)
        count = service.get_locked_snippet_count(sample_story.id)

        assert count == 2

    def test_permanently_delete_snippet(
        self, mock_db_session, sample_user, sample_story
    ):
        """permanently_delete_snippet should remove snippet from database."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="To Delete",
            content="Content",
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)
        snippet_id = snippet.id

        service = SnippetService(mock_db_session)
        result = service.permanently_delete_snippet(snippet_id)

        assert result is True

        # Verify it's gone
        deleted = (
            mock_db_session.query(Snippet).filter(Snippet.id == snippet_id).first()
        )
        assert deleted is None

    def test_to_dict_includes_lock_and_active(
        self, mock_db_session, sample_user, sample_story
    ):
        """Snippet.to_dict() should include is_locked and is_active fields."""
        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test",
            content="Content",
            is_locked=True,
            is_active=False,
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        data = snippet.to_dict()

        assert "is_locked" in data
        assert "is_active" in data
        assert data["is_locked"] is True
        assert data["is_active"] is False


class TestLockSnippetEndpoint:
    """Tests for PATCH /api/snippets/{snippet_id}/lock endpoint."""

    def test_lock_snippet_unauthorized(self):
        """PATCH /lock should reject unauthorized requests."""
        response = client.patch("/api/snippets/1/lock")
        assert response.status_code == 401

    def test_lock_snippet_not_found(self, mock_db_session, sample_user):
        """PATCH /lock should return 404 for non-existent snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.patch("/api/snippets/99999/lock")
            assert response.status_code == 404
        finally:
            app.dependency_overrides = {}

    def test_lock_snippet_success(self, mock_db_session, sample_user, sample_story):
        """PATCH /lock should toggle snippet lock status."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Test Snippet",
            content="Content",
            is_locked=False,
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            # Lock the snippet
            response = client.patch(f"/api/snippets/{snippet.id}/lock")
            assert response.status_code == 200
            data = response.json()
            assert data["is_locked"] is True

            # Unlock the snippet
            response = client.patch(f"/api/snippets/{snippet.id}/lock")
            assert response.status_code == 200
            data = response.json()
            assert data["is_locked"] is False
        finally:
            app.dependency_overrides = {}


class TestArchivedSnippetsEndpoint:
    """Tests for GET /api/snippets/{story_id}/archived endpoint."""

    def test_archived_snippets_unauthorized(self):
        """GET /archived should reject unauthorized requests."""
        response = client.get("/api/snippets/1/archived")
        assert response.status_code == 401

    def test_archived_snippets_success(
        self, mock_db_session, sample_user, sample_story
    ):
        """GET /archived should return archived snippets."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Create archived snippet
        archived = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Archived",
            content="Content",
            is_active=False,
        )
        # Create active snippet (should not be returned)
        active = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Active",
            content="Content",
            is_active=True,
        )
        mock_db_session.add(archived)
        mock_db_session.add(active)
        mock_db_session.commit()

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(f"/api/snippets/{sample_story.id}/archived")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["count"] == 1
            assert data["snippets"][0]["title"] == "Archived"
        finally:
            app.dependency_overrides = {}


class TestRestoreSnippetEndpoint:
    """Tests for POST /api/snippets/{snippet_id}/restore endpoint."""

    def test_restore_snippet_unauthorized(self):
        """POST /restore should reject unauthorized requests."""
        response = client.post("/api/snippets/1/restore")
        assert response.status_code == 401

    def test_restore_snippet_not_found(self, mock_db_session, sample_user):
        """POST /restore should return 404 for non-existent snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post("/api/snippets/99999/restore")
            assert response.status_code == 404
        finally:
            app.dependency_overrides = {}

    def test_restore_snippet_success(self, mock_db_session, sample_user, sample_story):
        """POST /restore should restore archived snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Archived Snippet",
            content="Content",
            is_active=False,  # Archived
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post(f"/api/snippets/{snippet.id}/restore")
            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is True
        finally:
            app.dependency_overrides = {}


class TestDeleteSnippetEndpoint:
    """Tests for DELETE /api/snippets/{snippet_id} endpoint."""

    def test_delete_snippet_unauthorized(self):
        """DELETE should reject unauthorized requests."""
        response = client.delete("/api/snippets/1")
        assert response.status_code == 401

    def test_delete_snippet_not_found(self, mock_db_session, sample_user):
        """DELETE should return 404 for non-existent snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.delete("/api/snippets/99999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides = {}

    def test_delete_snippet_soft_delete(
        self, mock_db_session, sample_user, sample_story
    ):
        """DELETE should soft-delete snippet by default."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="To Delete",
            content="Content",
            is_active=True,
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.delete(f"/api/snippets/{snippet.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False

            # Verify snippet still exists in DB (soft-deleted)
            mock_db_session.refresh(snippet)
            assert snippet.is_active is False
        finally:
            app.dependency_overrides = {}

    def test_delete_snippet_permanent(self, mock_db_session, sample_user, sample_story):
        """DELETE with ?permanent=true should permanently delete snippet."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        snippet = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="To Delete Permanently",
            content="Content",
            is_active=True,
        )
        mock_db_session.add(snippet)
        mock_db_session.commit()
        mock_db_session.refresh(snippet)
        snippet_id = snippet.id

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.delete(f"/api/snippets/{snippet_id}?permanent=true")
            assert response.status_code == 200

            # Verify snippet is permanently deleted
            deleted = (
                mock_db_session.query(Snippet).filter(Snippet.id == snippet_id).first()
            )
            assert deleted is None
        finally:
            app.dependency_overrides = {}


class TestGetSnippetsWithLockedCount:
    """Tests for GET /api/snippets/{story_id} returning locked_count."""

    def test_get_snippets_includes_locked_count(
        self, mock_db_session, sample_user, sample_story
    ):
        """GET should include locked_count in response."""
        from backend.app.core.auth import get_current_active_user
        from backend.app.db.session import get_db

        # Create snippets
        locked = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Locked",
            content="Content",
            is_locked=True,
            is_active=True,
        )
        unlocked = Snippet(
            user_id=sample_user.id,
            story_id=sample_story.id,
            title="Unlocked",
            content="Content",
            is_locked=False,
            is_active=True,
        )
        mock_db_session.add(locked)
        mock_db_session.add(unlocked)
        mock_db_session.commit()

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(f"/api/snippets/{sample_story.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert data["locked_count"] == 1
        finally:
            app.dependency_overrides = {}
