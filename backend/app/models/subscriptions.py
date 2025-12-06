from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.db.base_class import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Stripe Data
    stripe_customer_id = Column(String, index=True)
    stripe_subscription_id = Column(String, unique=True)

    # Access Control
    plan_type = Column(String, default="free")
    status = Column(String, nullable=False)
    current_period_end = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscription")
