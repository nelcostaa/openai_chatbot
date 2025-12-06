from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from backend.app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile Fields
    display_name = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user")  # 'user', 'admin'
    preferences = Column(JSON, default={})  # UI settings

    # Access Control
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stories = relationship(
        "Story", back_populates="owner", cascade="all, delete-orphan"
    )
    subscription = relationship("Subscription", back_populates="user", uselist=False)
