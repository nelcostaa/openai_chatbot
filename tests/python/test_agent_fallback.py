"""
Unit tests for backend/app/core/agent.py

Tests the LangGraph agent with model fallback cascade logic.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.agent import get_model_cascade, chatbot_node, AgentState


class TestGetModelCascade:
    """Test model cascade configuration."""

    def test_get_from_environment(self):
        """Should parse comma-separated models from GEMINI_MODELS env var."""
        # conftest sets GEMINI_MODELS=test-model-1,test-model-2,test-model-3
        models = get_model_cascade()
        assert models == ["test-model-1", "test-model-2", "test-model-3"]

    def test_get_default_when_no_env(self):
        """Should return default cascade when GEMINI_MODELS not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
                models = get_model_cascade()
                assert len(models) == 5
                assert models[0] == "gemini-2.0-flash-exp"
                assert models[2] == "gemini-2.5-flash"

    def test_strips_whitespace(self):
        """Should strip whitespace from model names."""
        with patch.dict("os.environ", {"GEMINI_MODELS": " model-a , model-b  ,  model-c "}):
            models = get_model_cascade()
            assert models == ["model-a", "model-b", "model-c"]

    def test_filters_empty_strings(self):
        """Should filter out empty strings from model list."""
        with patch.dict("os.environ", {"GEMINI_MODELS": "model-a,,model-b,"}):
            models = get_model_cascade()
            assert models == ["model-a", "model-b"]


class TestChatbotNode:
    """Test chatbot_node with fallback logic."""

    def test_success_on_first_model(self, mock_langchain_response):
        """Should succeed immediately if first model works."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "You are a helpful assistant."
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1", "model-2"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                mock_llm = Mock()
                mock_llm.invoke.return_value = mock_langchain_response
                mock_llm_class.return_value = mock_llm

                result = chatbot_node(state)

                # Should only try first model
                assert mock_llm_class.call_count == 1
                assert result["messages"][0].content == "This is a mock AI response from LangGraph."

    def test_fallback_on_rate_limit(self, mock_langchain_response):
        """Should fallback to next model on 429 rate limit error."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "You are a helpful assistant."
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1", "model-2", "model-3"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                # First model fails with 429
                mock_llm_1 = Mock()
                mock_llm_1.invoke.side_effect = Exception("429 rate limit exceeded")
                
                # Second model fails with quota
                mock_llm_2 = Mock()
                mock_llm_2.invoke.side_effect = Exception("quota exhausted")
                
                # Third model succeeds
                mock_llm_3 = Mock()
                mock_llm_3.invoke.return_value = mock_langchain_response
                
                mock_llm_class.side_effect = [mock_llm_1, mock_llm_2, mock_llm_3]

                result = chatbot_node(state)

                # Should try all 3 models
                assert mock_llm_class.call_count == 3
                assert result["messages"][0].content == "This is a mock AI response from LangGraph."

    def test_fallback_on_resource_exhausted(self, mock_langchain_response):
        """Should detect resource_exhausted as rate limit."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "Test instruction"
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1", "model-2"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                mock_llm_1 = Mock()
                mock_llm_1.invoke.side_effect = Exception("resource_exhausted for API")
                
                mock_llm_2 = Mock()
                mock_llm_2.invoke.return_value = mock_langchain_response
                
                mock_llm_class.side_effect = [mock_llm_1, mock_llm_2]

                result = chatbot_node(state)

                assert mock_llm_class.call_count == 2
                assert result["messages"][0].content == "This is a mock AI response from LangGraph."

    def test_abort_on_non_rate_limit_error(self):
        """Should abort immediately on non-rate-limit errors."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "Test instruction"
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1", "model-2", "model-3"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                mock_llm = Mock()
                mock_llm.invoke.side_effect = ValueError("Invalid input format")
                mock_llm_class.return_value = mock_llm

                with pytest.raises(ValueError, match="Invalid input format"):
                    chatbot_node(state)

                # Should only try first model
                assert mock_llm_class.call_count == 1

    def test_raise_after_all_models_exhausted(self):
        """Should raise exception if all models hit rate limits."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "Test instruction"
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1", "model-2"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                mock_llm = Mock()
                mock_llm.invoke.side_effect = Exception("429 rate limit")
                mock_llm_class.return_value = mock_llm

                with pytest.raises(Exception, match="All 2 models exhausted rate limits"):
                    chatbot_node(state)

                assert mock_llm_class.call_count == 2

    def test_prepends_system_message(self, mock_langchain_response):
        """Should prepend phase instruction as system message."""
        state = {
            "messages": [HumanMessage(content="Hello")],
            "phase_instruction": "You are a warm interviewer."
        }

        with patch("backend.app.core.agent.get_model_cascade") as mock_cascade:
            mock_cascade.return_value = ["model-1"]
            
            with patch("backend.app.core.agent.ChatGoogleGenerativeAI") as mock_llm_class:
                mock_llm = Mock()
                mock_llm.invoke.return_value = mock_langchain_response
                mock_llm_class.return_value = mock_llm

                chatbot_node(state)

                # Check that invoke was called with system message + user messages
                call_args = mock_llm.invoke.call_args[0][0]
                assert len(call_args) == 2  # System + 1 user message
                assert isinstance(call_args[0], SystemMessage)
                assert call_args[0].content == "You are a warm interviewer."
