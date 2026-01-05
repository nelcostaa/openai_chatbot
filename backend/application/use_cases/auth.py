"""
Authentication Use Cases

Application logic for user registration and authentication.
"""

from dataclasses import dataclass
from typing import Optional

from backend.application.interfaces.repositories import UserRepository
from backend.application.interfaces.services import PasswordService, TokenService
from backend.domain.entities.user import User
from backend.domain.exceptions import (
    AuthorizationError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)


@dataclass
class RegisterUserInput:
    """Input DTO for user registration."""

    email: str
    password: str
    display_name: str


@dataclass
class RegisterUserOutput:
    """Output DTO for user registration."""

    user_id: int
    email: str
    display_name: str
    access_token: str


@dataclass
class LoginInput:
    """Input DTO for user login."""

    email: str
    password: str


@dataclass
class LoginOutput:
    """Output DTO for user login."""

    user_id: int
    access_token: str
    token_type: str = "bearer"


class RegisterUserUseCase:
    """
    Use case for registering a new user.

    Business rules:
    - Email must be unique
    - Password must be hashed before storage
    - Return JWT token on successful registration
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self.user_repo = user_repo
        self.password_service = password_service
        self.token_service = token_service

    def execute(self, input_dto: RegisterUserInput) -> RegisterUserOutput:
        """
        Execute the registration use case.

        Args:
            input_dto: Registration data

        Returns:
            Registration result with token

        Raises:
            DuplicateEntityError: If email already exists
            ValidationError: If input is invalid
        """
        # Validate email uniqueness
        if self.user_repo.exists_by_email(input_dto.email):
            raise DuplicateEntityError("User", "email", input_dto.email)

        # Validate password strength (basic)
        if len(input_dto.password) < 6:
            raise ValidationError("password", "Password must be at least 6 characters")

        # Create domain entity
        user = User(
            email=input_dto.email,
            display_name=input_dto.display_name,
            is_active=True,
        )

        # Hash password
        hashed = self.password_service.hash_password(input_dto.password)
        user.set_hashed_password(hashed)

        # Persist
        saved_user = self.user_repo.save(user)

        # Generate token
        token = self.token_service.create_token(saved_user.id)

        return RegisterUserOutput(
            user_id=saved_user.id,
            email=saved_user.email,
            display_name=saved_user.display_name,
            access_token=token,
        )


class LoginUserUseCase:
    """
    Use case for user authentication.

    Business rules:
    - Verify email exists
    - Verify password matches
    - Verify user is active
    - Return JWT token on success
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self.user_repo = user_repo
        self.password_service = password_service
        self.token_service = token_service

    def execute(self, input_dto: LoginInput) -> LoginOutput:
        """
        Execute the login use case.

        Args:
            input_dto: Login credentials

        Returns:
            Login result with token

        Raises:
            AuthorizationError: If credentials invalid or user inactive
        """
        # Find user
        user = self.user_repo.get_by_email(input_dto.email)
        if not user:
            raise AuthorizationError("Incorrect email or password")

        # Verify password
        if not self.password_service.verify_password(
            input_dto.password, user.hashed_password
        ):
            raise AuthorizationError("Incorrect email or password")

        # Check active
        if not user.is_active:
            raise AuthorizationError("User account is inactive")

        # Generate token
        token = self.token_service.create_token(user.id)

        return LoginOutput(
            user_id=user.id,
            access_token=token,
        )


class GetCurrentUserUseCase:
    """
    Use case for getting current authenticated user.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> User:
        """
        Get user by ID.

        Args:
            user_id: The user ID from token

        Returns:
            User entity

        Raises:
            EntityNotFoundError: If user not found
            AuthorizationError: If user inactive
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        if not user.is_active:
            raise AuthorizationError("User account is inactive")

        return user
