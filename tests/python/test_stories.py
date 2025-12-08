"""
Tests for story management endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.story import Story

client = TestClient(app)


class TestStoryEndpoints:
    """Tests for story CRUD operations."""

    def test_create_story_authenticated(self, mock_db_session, sample_user):
        """Should create a new story for authenticated user."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.post(
                "/api/stories/",
                json={
                    "title": "My Life Journey",
                    "route_type": "1",
                    "age_range": "31_45",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "My Life Journey"
            assert data["route_type"] == "1"
            assert data["age_range"] == "31_45"
            assert data["current_phase"] == "GREETING"
            assert data["user_id"] == sample_user.id
        finally:
            app.dependency_overrides = {}

    def test_create_story_unauthenticated(self):
        """Should reject story creation without authentication."""
        response = client.post("/api/stories/", json={"title": "My Story"})

        assert response.status_code == 403  # No auth header

    def test_list_user_stories(self, mock_db_session, sample_user):
        """Should list only authenticated user's stories."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        # Create stories for user
        story1 = Story(
            user_id=sample_user.id,
            title="Story 1",
            route_type="1",
            current_phase="GREETING",
        )
        story2 = Story(
            user_id=sample_user.id,
            title="Story 2",
            route_type="2",
            current_phase="CHILDHOOD",
        )
        mock_db_session.add(story1)
        mock_db_session.add(story2)
        mock_db_session.commit()

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(
                "/api/stories/", headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["title"] == "Story 1"
            assert data[1]["title"] == "Story 2"
        finally:
            app.dependency_overrides = {}

    def test_get_story_by_id(self, mock_db_session, sample_user, sample_story):
        """Should get story details by ID."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(
                f"/api/stories/{sample_story.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_story.id
            assert data["title"] == sample_story.title
        finally:
            app.dependency_overrides = {}

    def test_get_story_not_owned(self, mock_db_session, sample_user):
        """Should reject access to story not owned by user."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app
        from backend.app.models.user import User

        # Create another user
        other_user = User(
            email="other@example.com", hashed_password="hash", display_name="Other User"
        )
        mock_db_session.add(other_user)
        mock_db_session.commit()
        mock_db_session.refresh(other_user)

        # Create story for other user
        other_story = Story(
            user_id=other_user.id,
            title="Other's Story",
            route_type="1",
            current_phase="GREETING",
        )
        mock_db_session.add(other_story)
        mock_db_session.commit()
        mock_db_session.refresh(other_story)

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.get(
                f"/api/stories/{other_story.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 403
            assert "Not authorized" in response.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_update_story(self, mock_db_session, sample_user, sample_story):
        """Should update story metadata."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.put(
                f"/api/stories/{sample_story.id}",
                json={"title": "Updated Title", "current_phase": "CHILDHOOD"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Title"
            assert data["current_phase"] == "CHILDHOOD"
        finally:
            app.dependency_overrides = {}

    def test_delete_story(self, mock_db_session, sample_user, sample_story):
        """Should delete a story."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.delete(
                f"/api/stories/{sample_story.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 204

            # Verify deletion
            deleted_story = (
                mock_db_session.query(Story).filter(Story.id == sample_story.id).first()
            )
            assert deleted_story is None
        finally:
            app.dependency_overrides = {}

    def test_delete_story_not_found(self, mock_db_session, sample_user):
        """Should return 404 for non-existent story."""
        from backend.app.api.endpoints.stories import get_current_active_user, get_db
        from backend.app.main import app

        token = create_access_token({"sub": str(sample_user.id)})

        def override_get_db():
            yield mock_db_session

        def override_get_current_user():
            return sample_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_active_user] = override_get_current_user

        try:
            response = client.delete(
                "/api/stories/9999", headers={"Authorization": f"Bearer {token}"}
            )

            assert response.status_code == 404
        finally:
            app.dependency_overrides = {}
