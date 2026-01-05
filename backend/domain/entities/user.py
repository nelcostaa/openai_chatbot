"""
User Entity - Core domain representation of a user.

This is a pure Python class with no framework dependencies.
It contains business rules for user validation and behavior.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class User:
    """
    Domain entity representing a user in the system.

    This entity is framework-agnostic and contains only business logic.
    Persistence is handled by the infrastructure layer via repositories.
    """

    id: Optional[int] = None
    email: str = ""
    display_name: str = ""
    full_name: Optional[str] = None
    role: str = "user"
    preferences: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Password hash is stored separately - not part of entity behavior
    _hashed_password: Optional[str] = field(default=None, repr=False)

    def __post_init__(self):
        """Validate entity after initialization."""
        if self.email and not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")

        if self.role not in ("user", "admin"):
            raise ValueError(f"Invalid role: {self.role}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation."""
        return "@" in email and "." in email.split("@")[-1]

    @property
    def hashed_password(self) -> Optional[str]:
        """Get hashed password (read-only after set)."""
        return self._hashed_password

    def set_hashed_password(self, hashed: str) -> None:
        """Set the hashed password (should only be called by auth service)."""
        self._hashed_password = hashed

    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == "admin" or self.is_superuser

    def can_access_story(self, story_owner_id: int) -> bool:
        """Check if user can access a specific story."""
        if self.is_admin():
            return True
        return self.id == story_owner_id

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False

    def activate(self) -> None:
        """Activate the user account."""
        self.is_active = True

    def update_profile(
        self,
        display_name: Optional[str] = None,
        full_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update user profile information."""
        if display_name is not None:
            self.display_name = display_name
        if full_name is not None:
            self.full_name = full_name
        if preferences is not None:
            self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()
