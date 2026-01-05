"""
Message Entity - Core domain representation of a chat message.

This is a pure Python class with no framework dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    """Valid message roles in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """
    Domain entity representing a message in a story conversation.

    Messages are immutable after creation - they represent
    historical conversation records.
    """

    id: Optional[int] = None
    story_id: Optional[int] = None
    role: MessageRole = MessageRole.USER
    content: str = ""
    phase_context: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate entity after initialization."""
        # Convert string role to enum if needed
        if isinstance(self.role, str):
            self.role = MessageRole(self.role)

        if not self.content:
            raise ValueError("Message content cannot be empty")

        # Enforce max content length (business rule)
        if len(self.content) > 50000:
            raise ValueError("Message content exceeds maximum length (50000 chars)")

    @property
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant_message(self) -> bool:
        """Check if this is an AI assistant message."""
        return self.role == MessageRole.ASSISTANT

    @property
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM

    @property
    def word_count(self) -> int:
        """Get approximate word count."""
        return len(self.content.split())

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "role": (
                self.role.value if isinstance(self.role, MessageRole) else self.role
            ),
            "content": self.content,
            "phase_context": self.phase_context,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
