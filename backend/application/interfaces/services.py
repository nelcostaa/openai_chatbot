"""
Service Interfaces (Ports)

Abstract interfaces for external services like AI, email, etc.
Implementations are in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from backend.domain.entities.message import Message


@dataclass
class AIResponse:
    """Response from AI service."""

    content: str
    model: str
    attempts: int
    tokens_used: Optional[int] = None


@dataclass
class ChatMessage:
    """Input message for AI chat."""

    role: str
    content: str


class AIService(ABC):
    """Abstract interface for AI chat service."""

    @abstractmethod
    def generate_response(
        self, messages: List[ChatMessage], system_instruction: str
    ) -> AIResponse:
        """
        Generate AI response for a conversation.

        Args:
            messages: Conversation history
            system_instruction: System prompt/instruction

        Returns:
            AIResponse with generated content

        Raises:
            AIServiceError: If generation fails
        """
        pass

    @abstractmethod
    def generate_snippets(self, messages: List[ChatMessage], count: int = 12) -> str:
        """
        Generate story snippets from conversation.

        Args:
            messages: Conversation history
            count: Number of snippets to generate

        Returns:
            JSON string with snippet data

        Raises:
            AIServiceError: If generation fails
        """
        pass


class PasswordService(ABC):
    """Abstract interface for password hashing service."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        pass

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        pass


class TokenService(ABC):
    """Abstract interface for JWT token service."""

    @abstractmethod
    def create_token(self, user_id: int, expires_minutes: int = 30) -> str:
        """Create a JWT token for a user."""
        pass

    @abstractmethod
    def decode_token(self, token: str) -> Optional[int]:
        """
        Decode a JWT token and return user ID.

        Returns:
            User ID if valid, None if invalid/expired
        """
        pass
