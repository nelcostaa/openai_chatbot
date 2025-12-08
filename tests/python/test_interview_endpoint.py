"""
Integration tests for backend/app/api/endpoints/interview.py

Tests the FastAPI interview endpoint.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.main import app
from backend.app.models.message import Message


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestInterviewEndpoint:
    """Test POST /api/interview/{story_id} endpoint."""

    def test_successful_chat_returns_ai_response(
        self, client, mock_db_session, sample_story
    ):
        """Should return AI response with correct format."""

        with patch("backend.app.api.endpoints.interview.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db_session

            with patch("backend.app.services.interview.agent_app") as mock_agent:
                from langchain_core.messages import AIMessage

                mock_agent.invoke.return_value = {
                    "messages": [AIMessage(content="Welcome! Ready to begin?")]
                }

                response = client.post(
                    f"/api/interview/{sample_story.id}", json={"message": "Hello!"}
                )

                assert response.status_code == 200
                data = response.json()

                assert data["role"] == "assistant"
                assert data["content"] == "Welcome! Ready to begin?"
                assert data["phase"] == "GREETING"
                assert "id" in data
                assert isinstance(data["id"], int)

    def test_missing_story_returns_404(self, client, mock_db_session):
        """Should return 404 for non-existent story."""

        with patch("backend.app.api.endpoints.interview.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db_session

            response = client.post("/api/interview/999", json={"message": "Hello!"})

            assert response.status_code == 404
            assert "Story with ID 999 not found" in response.json()["detail"]

    def test_invalid_request_body_returns_422(self, client):
        """Should return 422 for invalid request body."""

        response = client.post("/api/interview/1", json={"wrong_field": "value"})

        assert response.status_code == 422

    def test_agent_error_returns_500(self, client, mock_db_session, sample_story):
        """Should return 500 on agent errors."""

        with patch("backend.app.api.endpoints.interview.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db_session

            with patch("backend.app.services.interview.agent_app") as mock_agent:
                mock_agent.invoke.side_effect = Exception("Agent error")

                response = client.post(
                    f"/api/interview/{sample_story.id}", json={"message": "Hello!"}
                )

                assert response.status_code == 500
                assert "Internal Server Error" in response.json()["detail"]

    def test_service_called_with_correct_parameters(self, client):
        """Should call service with story_id and message content."""
        from backend.app.models.message import Message
        from backend.app.services.interview import InterviewService

        with patch.object(InterviewService, "process_chat") as mock_process:
            # Mock return value
            mock_message = Message(
                id=1,
                story_id=1,
                role="assistant",
                content="AI response",
                phase_context="GREETING",
            )
            mock_process.return_value = mock_message

            response = client.post("/api/interview/1", json={"message": "User message"})

            assert response.status_code == 200

            # Verify service was called correctly
            mock_process.assert_called_once_with(1, "User message")

            # Verify response format
            data = response.json()
            assert data["role"] == "assistant"
            assert data["content"] == "AI response"
            assert data["phase"] == "GREETING"

    def test_phase_context_from_unknown_defaults_to_unknown(
        self, client, mock_db_session, sample_story
    ):
        """Should handle missing phase_context gracefully."""

        with patch("backend.app.api.endpoints.interview.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db_session

            with patch("backend.app.services.interview.agent_app") as mock_agent:
                from langchain_core.messages import AIMessage

                mock_agent.invoke.return_value = {
                    "messages": [AIMessage(content="Response")]
                }

                # Create mock AI message with None phase_context
                with patch(
                    "backend.app.services.interview.InterviewService.process_chat"
                ) as mock_process:
                    mock_message = Mock()
                    mock_message.id = 1
                    mock_message.role = "assistant"
                    mock_message.content = "Response"
                    mock_message.phase_context = None
                    mock_process.return_value = mock_message

                    response = client.post(
                        f"/api/interview/{sample_story.id}", json={"message": "Test"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["phase"] == "UNKNOWN"
