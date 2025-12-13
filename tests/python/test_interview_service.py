"""
Unit tests for backend/app/services/interview.py

Tests the InterviewService orchestration layer.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.interview import PHASE_CONFIG, InterviewService


class TestInterviewService:
    """Test InterviewService class."""

    def test_process_chat_creates_user_message(self, mock_db_session, sample_story):
        """Should save user message to database."""
        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="AI response")]
            }

            service.process_chat(sample_story.id, "Hello, this is my message")

            # Check user message was saved
            from backend.app.models.message import Message

            messages = mock_db_session.query(Message).filter_by(role="user").all()
            assert len(messages) == 1
            assert messages[0].content == "Hello, this is my message"
            assert messages[0].story_id == sample_story.id
            assert messages[0].phase_context == "GREETING"

    def test_process_chat_creates_ai_message(self, mock_db_session, sample_story):
        """Should save AI response to database."""
        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Welcome to your story!")]
            }

            result, metadata = service.process_chat(sample_story.id, "Hello")

            # Check AI message was saved
            assert result.role == "assistant"
            assert result.content == "Welcome to your story!"
            assert result.story_id == sample_story.id
            assert result.phase_context == "GREETING"
            
            # Check metadata structure
            assert "phase" in metadata
            assert "phase_order" in metadata

    def test_process_chat_loads_conversation_history(
        self, mock_db_session, sample_story
    ):
        """Should load previous messages as context."""
        from backend.app.models.message import Message

        # Create existing messages
        msg1 = Message(
            story_id=sample_story.id,
            role="user",
            content="First message",
            phase_context="GREETING",
        )
        msg2 = Message(
            story_id=sample_story.id,
            role="assistant",
            content="First response",
            phase_context="GREETING",
        )
        mock_db_session.add_all([msg1, msg2])
        mock_db_session.commit()

        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Second response")]
            }

            service.process_chat(sample_story.id, "Second message")

            # Check agent was called with history
            call_args = mock_agent.invoke.call_args[0][0]
            messages = call_args["messages"]

            # Should have: previous user + previous assistant + new user
            assert len(messages) == 3
            assert isinstance(messages[0], HumanMessage)
            assert messages[0].content == "First message"
            assert isinstance(messages[1], AIMessage)
            assert messages[1].content == "First response"
            assert isinstance(messages[2], HumanMessage)
            assert messages[2].content == "Second message"

    def test_process_chat_uses_correct_phase_instruction(
        self, mock_db_session, sample_story
    ):
        """Should use phase-specific system instruction."""
        sample_story.current_phase = "CHILDHOOD"
        mock_db_session.commit()

        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Tell me about your childhood")]
            }

            service.process_chat(sample_story.id, "I grew up in California")

            # Check correct phase instruction was used
            call_args = mock_agent.invoke.call_args[0][0]
            phase_instruction = call_args["phase_instruction"]

            assert phase_instruction == PHASE_CONFIG["CHILDHOOD"]["prompt"]
            assert "childhood memories" in phase_instruction.lower()

    def test_process_chat_uses_default_phase_for_unknown(
        self, mock_db_session, sample_story
    ):
        """Should use GREETING as default for unknown phases."""
        sample_story.current_phase = "UNKNOWN_PHASE"
        mock_db_session.commit()

        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Response")]
            }

            service.process_chat(sample_story.id, "Test message")

            # Should fallback to GREETING instruction
            call_args = mock_agent.invoke.call_args[0][0]
            phase_instruction = call_args["phase_instruction"]

            assert phase_instruction == PHASE_CONFIG["GREETING"]["prompt"]

    def test_process_chat_raises_on_missing_story(self, mock_db_session):
        """Should raise ValueError for non-existent story."""
        service = InterviewService(mock_db_session)

        with pytest.raises(ValueError, match="Story with ID 999 not found"):
            service.process_chat(999, "Test message")

    def test_process_chat_limits_history_to_20_messages(
        self, mock_db_session, sample_story
    ):
        """Should only load last 20 messages as context."""
        from backend.app.models.message import Message

        # Create 25 messages
        for i in range(25):
            role = "user" if i % 2 == 0 else "assistant"
            msg = Message(
                story_id=sample_story.id,
                role=role,
                content=f"Message {i}",
                phase_context="GREETING",
            )
            mock_db_session.add(msg)
        mock_db_session.commit()

        service = InterviewService(mock_db_session)

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Response")]
            }

            service.process_chat(sample_story.id, "New message")

        # Check history was limited
        call_args = mock_agent.invoke.call_args[0][0]
        messages = call_args["messages"]

        # Should have: 20 history messages (new message saved to DB but NOT passed to agent)
        assert len(messages) == 20

    def test_process_chat_commits_immediately_after_user_message(
        self, mock_db_session, sample_story
    ):
        """Should commit user message before calling agent (for persistence)."""
        service = InterviewService(mock_db_session)

        commit_count = 0
        original_commit = mock_db_session.commit

        def track_commits():
            nonlocal commit_count
            commit_count += 1
            original_commit()

        mock_db_session.commit = track_commits

        with patch("backend.app.services.interview.agent_app") as mock_agent:
            # Simulate agent error
            mock_agent.invoke.side_effect = Exception("Agent failed")

            try:
                service.process_chat(sample_story.id, "Test message")
            except Exception:
                pass

            # User message should still be committed (first commit)
            from backend.app.models.message import Message

            user_messages = mock_db_session.query(Message).filter_by(role="user").all()
            assert len(user_messages) == 1
            assert user_messages[0].content == "Test message"
