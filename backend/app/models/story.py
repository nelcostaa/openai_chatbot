from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.db.base_class import Base


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Story Metadata
    title = Column(String, default="Untitled Story")
    route_type = Column(String, default="chronological")
    current_phase = Column(String, default="GREETING")
    age_range = Column(String, nullable=True)
    status = Column(String, default="draft")  # 'draft', 'completed'

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="stories")
    messages = relationship(
        "Message", back_populates="story", cascade="all, delete-orphan"
    )
    summaries = relationship(
        "Summary", back_populates="story", cascade="all, delete-orphan"
    )
    snippets = relationship(
        "Snippet", back_populates="story", cascade="all, delete-orphan"
    )
