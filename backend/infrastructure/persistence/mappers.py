"""
Entity <-> ORM Model Mappers

Functions to convert between domain entities and SQLAlchemy ORM models.
This keeps the domain layer pure and free of ORM dependencies.
"""

from datetime import datetime
from typing import Optional

# Import ORM models (these are in the existing app/models)
from backend.app.models.message import Message as MessageModel
from backend.app.models.snippets import Snippet as SnippetModel
from backend.app.models.story import Story as StoryModel
from backend.app.models.user import User as UserModel
from backend.domain.entities.message import Message as MessageEntity
from backend.domain.entities.message import MessageRole
from backend.domain.entities.snippet import Snippet as SnippetEntity
from backend.domain.entities.story import AgeRange, Phase
from backend.domain.entities.story import Story as StoryEntity
from backend.domain.entities.story import StoryStatus
from backend.domain.entities.user import User as UserEntity

# ============================================================
# User Mappers
# ============================================================


def user_model_to_entity(model: UserModel) -> UserEntity:
    """Convert SQLAlchemy User model to domain entity."""
    entity = UserEntity(
        id=model.id,
        email=model.email,
        display_name=model.display_name,
        full_name=model.full_name,
        role=model.role or "user",
        preferences=model.preferences or {},
        is_active=model.is_active,
        is_superuser=model.is_superuser,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
    entity.set_hashed_password(model.hashed_password)
    return entity


def user_entity_to_model(
    entity: UserEntity, model: Optional[UserModel] = None
) -> UserModel:
    """Convert domain User entity to SQLAlchemy model."""
    if model is None:
        model = UserModel()

    if entity.id:
        model.id = entity.id
    model.email = entity.email
    model.display_name = entity.display_name
    model.full_name = entity.full_name
    model.role = entity.role
    model.preferences = entity.preferences
    model.is_active = entity.is_active
    model.is_superuser = entity.is_superuser

    if entity.hashed_password:
        model.hashed_password = entity.hashed_password

    return model


# ============================================================
# Story Mappers
# ============================================================


def story_model_to_entity(model: StoryModel) -> StoryEntity:
    """Convert SQLAlchemy Story model to domain entity."""
    # Convert phase string to enum
    try:
        phase = Phase(model.current_phase) if model.current_phase else Phase.GREETING
    except ValueError:
        phase = Phase.GREETING

    # Convert age_range string to enum
    age_range = None
    if model.age_range:
        try:
            age_range = AgeRange(model.age_range)
        except ValueError:
            pass

    # Convert status string to enum
    try:
        status = StoryStatus(model.status) if model.status else StoryStatus.DRAFT
    except ValueError:
        status = StoryStatus.DRAFT

    return StoryEntity(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        route_type=model.route_type or "chronological",
        current_phase=phase,
        age_range=age_range,
        status=status,
        created_at=model.created_at,
    )


def story_entity_to_model(
    entity: StoryEntity, model: Optional[StoryModel] = None
) -> StoryModel:
    """Convert domain Story entity to SQLAlchemy model."""
    if model is None:
        model = StoryModel()

    if entity.id:
        model.id = entity.id
    model.user_id = entity.user_id
    model.title = entity.title
    model.route_type = entity.route_type

    # Convert enum to string
    if isinstance(entity.current_phase, Phase):
        model.current_phase = entity.current_phase.value
    else:
        model.current_phase = entity.current_phase

    if entity.age_range:
        if isinstance(entity.age_range, AgeRange):
            model.age_range = entity.age_range.value
        else:
            model.age_range = entity.age_range

    if isinstance(entity.status, StoryStatus):
        model.status = entity.status.value
    else:
        model.status = entity.status

    return model


# ============================================================
# Message Mappers
# ============================================================


def message_model_to_entity(model: MessageModel) -> MessageEntity:
    """Convert SQLAlchemy Message model to domain entity."""
    try:
        role = MessageRole(model.role)
    except ValueError:
        role = MessageRole.USER

    return MessageEntity(
        id=model.id,
        story_id=model.story_id,
        role=role,
        content=model.content,
        phase_context=model.phase_context,
        tokens_used=model.tokens_used,
        created_at=model.created_at,
    )


def message_entity_to_model(
    entity: MessageEntity, model: Optional[MessageModel] = None
) -> MessageModel:
    """Convert domain Message entity to SQLAlchemy model."""
    if model is None:
        model = MessageModel()

    if entity.id:
        model.id = entity.id
    model.story_id = entity.story_id

    if isinstance(entity.role, MessageRole):
        model.role = entity.role.value
    else:
        model.role = entity.role

    model.content = entity.content
    model.phase_context = entity.phase_context
    model.tokens_used = entity.tokens_used

    return model


# ============================================================
# Snippet Mappers
# ============================================================


def snippet_model_to_entity(model: SnippetModel) -> SnippetEntity:
    """Convert SQLAlchemy Snippet model to domain entity."""
    return SnippetEntity(
        id=model.id,
        story_id=model.story_id,
        user_id=model.user_id,
        title=model.title,
        content=model.content,
        theme=model.theme,
        phase=model.phase,
        is_locked=model.is_locked,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def snippet_entity_to_model(
    entity: SnippetEntity, model: Optional[SnippetModel] = None
) -> SnippetModel:
    """Convert domain Snippet entity to SQLAlchemy model."""
    if model is None:
        model = SnippetModel()

    if entity.id:
        model.id = entity.id
    model.story_id = entity.story_id
    model.user_id = entity.user_id
    model.title = entity.title
    model.content = entity.content
    model.theme = entity.theme
    model.phase = entity.phase
    model.is_locked = entity.is_locked
    model.is_active = entity.is_active

    return model
