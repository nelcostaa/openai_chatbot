"""
Snippet Entity - Core domain representation of a story snippet/card.

This is a pure Python class with no framework dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Snippet:
    """
    Domain entity representing a snippet (game card) from a story.

    Snippets are extracted from interview conversations and represent
    meaningful moments or themes in the user's life story.
    """

    id: Optional[int] = None
    story_id: Optional[int] = None
    user_id: Optional[int] = None

    # Content fields
    title: str = ""
    content: str = ""
    theme: Optional[str] = None
    phase: Optional[str] = None

    # State fields
    is_locked: bool = False
    is_active: bool = True

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Content limits (business rules)
    MAX_TITLE_LENGTH = 100
    MAX_CONTENT_LENGTH = 500

    def __post_init__(self):
        """Validate and normalize entity after initialization."""
        # Truncate title if too long
        if len(self.title) > self.MAX_TITLE_LENGTH:
            self.title = self.title[: self.MAX_TITLE_LENGTH]

        # Truncate content if too long
        if len(self.content) > self.MAX_CONTENT_LENGTH:
            self.content = self.content[: self.MAX_CONTENT_LENGTH]

    @property
    def is_archived(self) -> bool:
        """Check if snippet is archived (soft-deleted)."""
        return not self.is_active

    def lock(self) -> None:
        """Lock the snippet to prevent deletion during regeneration."""
        self.is_locked = True
        self.updated_at = datetime.utcnow()

    def unlock(self) -> None:
        """Unlock the snippet."""
        self.is_locked = False
        self.updated_at = datetime.utcnow()

    def toggle_lock(self) -> bool:
        """Toggle lock state and return new state."""
        self.is_locked = not self.is_locked
        self.updated_at = datetime.utcnow()
        return self.is_locked

    def archive(self) -> None:
        """Soft-delete the snippet (archive)."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore an archived snippet."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def update_content(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> None:
        """
        Update snippet content.

        Args:
            title: New title (optional)
            content: New content (optional)
            theme: New theme (optional)
        """
        if title is not None:
            self.title = title[: self.MAX_TITLE_LENGTH]
        if content is not None:
            self.content = content[: self.MAX_CONTENT_LENGTH]
        if theme is not None:
            self.theme = theme
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "theme": self.theme,
            "phase": self.phase,
            "is_locked": self.is_locked,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
