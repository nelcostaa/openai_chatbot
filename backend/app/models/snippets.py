"""
Snippet model for persisting AI-generated life story snippets.

Snippets are extracted from interview conversations and represent
memorable moments or themes from the user's life story.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.base_class import Base


class Snippet(Base):
    """
    Represents a generated snippet from a life story interview.

    Snippets are AI-generated summaries of significant moments or themes
    extracted from the interview conversation. Each snippet has:
    - A title (e.g., "Village Soccer Days")
    - Content (the snippet text, max 300 chars for card display)
    - Phase (which life phase it relates to: CHILDHOOD, YOUNG_ADULT, etc.)
    - Theme (category: family, friendship, growth, adventure, etc.)
    """

    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)

    # Snippet content fields
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    theme = Column(
        String(50), nullable=True
    )  # family, friendship, growth, adventure, etc.
    phase = Column(String(50), nullable=True)  # CHILDHOOD, YOUNG_ADULT, ADULTHOOD, etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="snippets")
    story = relationship("Story", back_populates="snippets")

    def __repr__(self):
        return (
            f"<Snippet(id={self.id}, title='{self.title[:30]}...', phase={self.phase})>"
        )

    def to_dict(self):
        """Convert snippet to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "theme": self.theme,
            "phase": self.phase,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
