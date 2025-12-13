"""
Unit tests for backend/app/services/snippets.py and backend/app/api/endpoints/snippets.py

Tests the snippet generation service and API endpoint.
Includes TDD tests for persistent snippets feature.
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
        assert response.status_code == 403

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

        # Verify deletion
        remaining = (
            mock_db_session.query(Snippet)
            .filter(Snippet.story_id == sample_story.id)
            .all()
        )
        assert len(remaining) == 0


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

        # Verify old snippets are gone, new ones exist
        all_snippets = (
            mock_db_session.query(Snippet)
            .filter(Snippet.story_id == sample_story.id)
            .all()
        )
        assert len(all_snippets) == 2  # New snippets only
        titles = [s.title for s in all_snippets]
        assert "Old Snippet" not in titles
        assert "Village Soccer Days" in titles

    def test_get_snippets_unauthorized(self):
        """GET should reject unauthorized requests."""
        response = client.get("/api/snippets/1")
        assert response.status_code == 403

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
        assert response.status_code == 403

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
