"""
Repository Interfaces (Ports)

Abstract interfaces that define how the application layer
accesses data. Implementations are in the infrastructure layer.

These follow the Repository Pattern from Domain-Driven Design.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.domain.entities.message import Message
from backend.domain.entities.snippet import Snippet
from backend.domain.entities.story import Story
from backend.domain.entities.user import User


class UserRepository(ABC):
    """Abstract interface for user data access."""

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        """Save (create or update) a user."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if a user with this email exists."""
        pass


class StoryRepository(ABC):
    """Abstract interface for story data access."""

    @abstractmethod
    def get_by_id(self, story_id: int) -> Optional[Story]:
        """Get story by ID."""
        pass

    @abstractmethod
    def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Story]:
        """Get all stories for a user."""
        pass

    @abstractmethod
    def save(self, story: Story) -> Story:
        """Save (create or update) a story."""
        pass

    @abstractmethod
    def delete(self, story_id: int) -> bool:
        """Delete a story by ID."""
        pass

    @abstractmethod
    def count_by_user_id(self, user_id: int) -> int:
        """Count stories for a user."""
        pass


class MessageRepository(ABC):
    """Abstract interface for message data access."""

    @abstractmethod
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID."""
        pass

    @abstractmethod
    def get_by_story_id(
        self, story_id: int, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """Get all messages for a story."""
        pass

    @abstractmethod
    def save(self, message: Message) -> Message:
        """Save a new message."""
        pass

    @abstractmethod
    def delete_by_story_id(self, story_id: int) -> int:
        """Delete all messages for a story. Returns count deleted."""
        pass

    @abstractmethod
    def count_by_story_id(self, story_id: int) -> int:
        """Count messages for a story."""
        pass


class SnippetRepository(ABC):
    """Abstract interface for snippet data access."""

    @abstractmethod
    def get_by_id(self, snippet_id: int) -> Optional[Snippet]:
        """Get snippet by ID."""
        pass

    @abstractmethod
    def get_by_story_id(
        self, story_id: int, include_archived: bool = False
    ) -> List[Snippet]:
        """Get all snippets for a story."""
        pass

    @abstractmethod
    def get_by_user_id(
        self, user_id: int, include_archived: bool = False
    ) -> List[Snippet]:
        """Get all snippets for a user."""
        pass

    @abstractmethod
    def save(self, snippet: Snippet) -> Snippet:
        """Save (create or update) a snippet."""
        pass

    @abstractmethod
    def save_many(self, snippets: List[Snippet]) -> List[Snippet]:
        """Save multiple snippets at once."""
        pass

    @abstractmethod
    def delete(self, snippet_id: int) -> bool:
        """Permanently delete a snippet."""
        pass

    @abstractmethod
    def delete_unlocked_by_story_id(self, story_id: int) -> int:
        """Delete all unlocked snippets for a story. Returns count deleted."""
        pass

    @abstractmethod
    def count_locked_by_story_id(self, story_id: int) -> int:
        """Count locked snippets for a story."""
        pass
