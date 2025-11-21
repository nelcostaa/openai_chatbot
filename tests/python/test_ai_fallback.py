"""
Unit tests for ai_fallback module.

Tests the pure function logic for Gemini AI fallback cascade without
making actual API calls.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.ai_fallback import (
    configure_gemini,
    format_messages_for_gemini,
    get_model_cascade,
    run_gemini_fallback,
)


class TestConfigureGemini:
    """Test Gemini API configuration."""

    def test_configure_with_explicit_key(self):
        """Should configure with explicitly provided key."""
        with patch("api.ai_fallback.genai.configure") as mock_configure:
            configure_gemini(api_key="explicit_key_123")
            mock_configure.assert_called_once_with(api_key="explicit_key_123")

    def test_configure_from_env_gemini_key(self):
        """Should read GEMINI_API_KEY from environment."""
        with patch("api.ai_fallback.genai.configure") as mock_configure:
            configure_gemini()  # Uses GEMINI_API_KEY from conftest fixture
            mock_configure.assert_called_once()

    def test_configure_raises_without_key(self):
        """Should raise ValueError if no key available."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
                configure_gemini()


class TestGetModelCascade:
    """Test model cascade retrieval."""

    def test_get_from_environment(self):
        """Should parse comma-separated models from environment."""
        # Uses GEMINI_MODELS from conftest fixture
        models = get_model_cascade()
        assert models == ["test-model-1", "test-model-2", "test-model-3"]

    def test_get_default_when_no_env(self):
        """Should return default cascade when env var not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch.dict("os.environ", {"GEMINI_API_KEY": "test"}):
                models = get_model_cascade()
                assert len(models) == 6
                assert models[0] == "gemini-2.5-flash"

    def test_strips_whitespace(self):
        """Should strip whitespace from model names."""
        with patch.dict(
            "os.environ", {"GEMINI_MODELS": " model-a , model-b  ,  model-c "}
        ):
            models = get_model_cascade()
            assert models == ["model-a", "model-b", "model-c"]


class TestFormatMessagesForGemini:
    """Test message format conversion."""

    def test_format_user_and_assistant_messages(self):
        """Should convert user/assistant roles to Gemini format."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        result = format_messages_for_gemini(messages)

        assert len(result) == 2
        assert result[0] == {"role": "user", "parts": [{"text": "Hello"}]}
        assert result[1] == {"role": "model", "parts": [{"text": "Hi there!"}]}

    def test_skips_system_messages(self):
        """Should skip system messages (handled separately)."""
        messages = [
            {"role": "system", "content": "You are an AI"},
            {"role": "user", "content": "Hello"},
        ]

        result = format_messages_for_gemini(messages)

        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_handles_empty_content(self):
        """Should handle messages with empty content."""
        messages = [{"role": "user", "content": ""}]
        result = format_messages_for_gemini(messages)
        assert result[0]["parts"][0]["text"] == ""


class TestRunGeminiFallback:
    """Test AI generation with fallback logic."""

    def test_successful_first_attempt(self, sample_messages, sample_system_instruction):
        """Should succeed on first model without fallback."""
        mock_response = Mock()
        mock_response.text = "AI response here"

        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response

        mock_model = Mock()
        mock_model.start_chat.return_value = mock_chat

        with patch("api.ai_fallback.genai.GenerativeModel", return_value=mock_model):
            result = run_gemini_fallback(
                messages=sample_messages,
                system_instruction=sample_system_instruction,
            )

        assert result["success"] is True
        assert result["content"] == "AI response here"
        assert result["model"] == "test-model-1"
        assert result["attempts"] == 1
        assert result["error"] is None

    def test_fallback_on_rate_limit(self, sample_messages, sample_system_instruction):
        """Should fallback to next model on 429 rate limit."""
        # First model fails with rate limit
        mock_model_1 = Mock()
        mock_model_1.start_chat.side_effect = Exception(
            "429 RESOURCE_EXHAUSTED rate limit exceeded"
        )

        # Second model succeeds
        mock_response = Mock()
        mock_response.text = "Success on second model"
        mock_chat_2 = Mock()
        mock_chat_2.send_message.return_value = mock_response
        mock_model_2 = Mock()
        mock_model_2.start_chat.return_value = mock_chat_2

        with patch(
            "api.ai_fallback.genai.GenerativeModel",
            side_effect=[mock_model_1, mock_model_2],
        ):
            result = run_gemini_fallback(
                messages=sample_messages,
                system_instruction=sample_system_instruction,
            )

        assert result["success"] is True
        assert result["content"] == "Success on second model"
        assert result["model"] == "test-model-2"
        assert result["attempts"] == 2

    def test_all_models_exhausted(self, sample_messages, sample_system_instruction):
        """Should return failure when all models hit rate limit."""
        mock_model = Mock()
        mock_model.start_chat.side_effect = Exception("429 rate limit exceeded")

        with patch("api.ai_fallback.genai.GenerativeModel", return_value=mock_model):
            result = run_gemini_fallback(
                messages=sample_messages,
                system_instruction=sample_system_instruction,
            )

        assert result["success"] is False
        assert result["content"] == ""
        assert result["model"] is None
        assert result["attempts"] == 3  # All 3 test models tried
        assert "exhausted rate limits" in result["error"]

    def test_non_rate_limit_error_stops_cascade(
        self, sample_messages, sample_system_instruction
    ):
        """Should stop immediately on non-rate-limit errors."""
        mock_model = Mock()
        mock_model.start_chat.side_effect = Exception("Invalid API key")

        with patch("api.ai_fallback.genai.GenerativeModel", return_value=mock_model):
            result = run_gemini_fallback(
                messages=sample_messages,
                system_instruction=sample_system_instruction,
            )

        assert result["success"] is False
        assert result["attempts"] == 1  # Stopped after first attempt
        assert "Invalid API key" in result["error"]

    def test_validates_empty_messages(self, sample_system_instruction):
        """Should raise ValueError for empty messages."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            run_gemini_fallback(
                messages=[],
                system_instruction=sample_system_instruction,
            )

    def test_validates_no_user_message(self, sample_system_instruction):
        """Should work even with only assistant messages (uses last message content)."""
        messages = [{"role": "assistant", "content": "Hello"}]

        mock_response = Mock()
        mock_response.text = "Response"
        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_model = Mock()
        mock_model.start_chat.return_value = mock_chat

        with patch("api.ai_fallback.genai.GenerativeModel", return_value=mock_model):
            result = run_gemini_fallback(
                messages=messages,
                system_instruction=sample_system_instruction,
            )

        # Should succeed - uses last message content regardless of role
        assert result["success"] is True

    def test_uses_custom_model_list(self, sample_messages, sample_system_instruction):
        """Should use provided custom model list."""
        custom_models = ["custom-model-a", "custom-model-b"]

        mock_response = Mock()
        mock_response.text = "Response from custom model"
        mock_chat = Mock()
        mock_chat.send_message.return_value = mock_response
        mock_model = Mock()
        mock_model.start_chat.return_value = mock_chat

        with patch(
            "api.ai_fallback.genai.GenerativeModel", return_value=mock_model
        ) as mock_gen:
            result = run_gemini_fallback(
                messages=sample_messages,
                system_instruction=sample_system_instruction,
                models=custom_models,
            )

        assert result["success"] is True
        # Verify custom model was used (no system_instruction parameter)
        mock_gen.assert_called_with("custom-model-a")
