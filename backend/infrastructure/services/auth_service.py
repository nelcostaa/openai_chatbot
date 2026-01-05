"""
Authentication Service Implementations

Concrete implementations for password hashing and JWT tokens.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.application.interfaces.services import PasswordService, TokenService

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class BcryptPasswordService(PasswordService):
    """Password service using bcrypt hashing."""

    def hash_password(self, password: str) -> str:
        """Hash a plain text password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify a password against its bcrypt hash."""
        return pwd_context.verify(plain, hashed)


class JWTTokenService(TokenService):
    """Token service using JWT."""

    def __init__(self, secret_key: str = None, algorithm: str = None):
        self.secret_key = secret_key or SECRET_KEY
        self.algorithm = algorithm or ALGORITHM

    def create_token(
        self, user_id: int, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
    ) -> str:
        """Create a JWT token for a user."""
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Optional[int]:
        """
        Decode a JWT token and return user ID.

        Returns:
            User ID if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id_str = payload.get("sub")
            if user_id_str:
                return int(user_id_str)
            return None
        except (JWTError, ValueError):
            return None
