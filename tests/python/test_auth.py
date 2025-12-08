"""
Tests for authentication endpoints and security utilities.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from backend.app.main import app
from backend.app.models.user import User

client = TestClient(app)


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Should hash a plain password."""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Should verify correct password."""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Should reject incorrect password."""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_token(self):
        """Should create a valid JWT token."""
        data = {"sub": 123}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Should decode a valid token."""
        user_id = "123"
        token = create_access_token({"sub": user_id})
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_decode_invalid_token(self):
        """Should return None for invalid token."""
        invalid_token = "invalid.jwt.token"

        payload = decode_access_token(invalid_token)

        assert payload is None


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_register_new_user(self, mock_db_session):
        """Should register a new user and return token."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        # Override dependency
        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "securepass123",
                    "display_name": "New User",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

            # Verify user was created in database
            user = (
                mock_db_session.query(User)
                .filter(User.email == "newuser@example.com")
                .first()
            )
            assert user is not None
            assert user.display_name == "New User"
            assert user.is_active is True
        finally:
            app.dependency_overrides = {}

    def test_register_duplicate_email(self, mock_db_session, sample_user):
        """Should reject duplicate email registration."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": sample_user.email,
                    "password": "password123",
                    "display_name": "Duplicate User",
                },
            )

            assert response.status_code == 400
            assert "already registered" in response.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_login_with_correct_credentials(self, mock_db_session):
        """Should login with correct credentials."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        # Create user with known password
        hashed_password = get_password_hash("testpass123")
        user = User(
            email="login@example.com",
            hashed_password=hashed_password,
            display_name="Login User",
            is_active=True,
        )
        mock_db_session.add(user)
        mock_db_session.commit()

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/auth/login",
                json={"email": "login@example.com", "password": "testpass123"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides = {}

    def test_login_with_incorrect_password(self, mock_db_session):
        """Should reject incorrect password."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        hashed_password = get_password_hash("correctpass")
        user = User(
            email="user@example.com",
            hashed_password=hashed_password,
            display_name="Test User",
            is_active=True,
        )
        mock_db_session.add(user)
        mock_db_session.commit()

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "wrongpass"},
            )

            assert response.status_code == 401
            assert "Incorrect email or password" in response.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_login_with_nonexistent_email(self, mock_db_session):
        """Should reject login with nonexistent email."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.post(
                "/api/auth/login",
                json={"email": "nonexistent@example.com", "password": "anypassword"},
            )

            assert response.status_code == 401
        finally:
            app.dependency_overrides = {}

    def test_get_current_user_with_valid_token(self, mock_db_session, sample_user):
        """Should return user profile with valid token."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app
        
        token = create_access_token({"sub": str(sample_user.id)})
        
        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.get(
                "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_user.id
            assert data["email"] == sample_user.email
            assert data["display_name"] == sample_user.display_name
        finally:
            app.dependency_overrides = {}

    def test_get_current_user_without_token(self):
        """Should reject request without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 403  # FastAPI returns 403 for missing auth

    def test_get_current_user_with_invalid_token(self, mock_db_session):
        """Should reject invalid token."""
        from backend.app.api.endpoints.auth import get_db
        from backend.app.main import app

        def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.get(
                "/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
            )

            assert response.status_code == 401
        finally:
            app.dependency_overrides = {}

    def test_logout_endpoint(self):
        """Should return success message for logout."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
