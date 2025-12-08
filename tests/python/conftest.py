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
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    yield
    # Cleanup
    if "GEMINI_MODELS" in os.environ:
        del os.environ["GEMINI_MODELS"]


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.db.base_class import Base

    # Create in-memory SQLite database with thread safety disabled
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_user(mock_db_session):
    """Create a test user."""
    from backend.app.models.user import User
    
    user = User(
        email="test@example.com",
        hashed_password="fake_hash",
        display_name="Test User",
        is_active=True
    )
    mock_db_session.add(user)
    mock_db_session.commit()
    mock_db_session.refresh(user)
    
    return user


@pytest.fixture
def sample_story(mock_db_session, sample_user):
    """Create a test story."""
    from backend.app.models.story import Story
    
    story = Story(
        user_id=sample_user.id,
        title="Test Story",
        current_phase="GREETING",
        status="draft"
    )
    mock_db_session.add(story)
    mock_db_session.commit()
    mock_db_session.refresh(story)
    
    return story


@pytest.fixture
def mock_langchain_response():
    """Mock LangChain AIMessage response."""
    from langchain_core.messages import AIMessage
    
    return AIMessage(content="This is a mock AI response from LangGraph.")
