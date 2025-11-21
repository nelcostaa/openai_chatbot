"""
Pytest configuration and shared fixtures for backend tests.
"""

import os
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_gemini_response():
    """Mock successful Gemini API response."""
    mock_response = Mock()
    mock_response.text = "This is a mock AI response for testing purposes."
    return mock_response


@pytest.fixture
def mock_gemini_model(mock_gemini_response):
    """Mock Gemini model with chat interface."""
    mock_chat = Mock()
    mock_chat.send_message.return_value = mock_gemini_response

    mock_model = Mock()
    mock_model.start_chat.return_value = mock_chat

    return mock_model


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        {"role": "user", "content": "Hello, I want to tell my life story."},
        {
            "role": "assistant",
            "content": "Welcome! I'm here to help you share your story.",
        },
        {"role": "user", "content": "Where should I start?"},
    ]


@pytest.fixture
def sample_system_instruction():
    """Sample system instruction."""
    return """You are a compassionate AI interviewer for the Life Story Game.
Your role is to guide users through telling their life story with empathy and curiosity."""


@pytest.fixture(autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["GEMINI_API_KEY"] = "test_api_key_12345"
    os.environ["GEMINI_MODELS"] = "test-model-1,test-model-2,test-model-3"
    yield
    # Cleanup
    if "GEMINI_MODELS" in os.environ:
        del os.environ["GEMINI_MODELS"]
