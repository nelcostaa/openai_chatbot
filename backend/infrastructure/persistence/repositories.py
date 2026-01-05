"""
SQLAlchemy Repository Implementations

Concrete implementations of repository interfaces using SQLAlchemy ORM.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

# ORM Models
from backend.app.models.message import Message as MessageModel
from backend.app.models.snippets import Snippet as SnippetModel
from backend.app.models.story import Story as StoryModel
from backend.app.models.user import User as UserModel
from backend.application.interfaces.repositories import (
    MessageRepository,
    SnippetRepository,
    StoryRepository,
    UserRepository,
)
from backend.domain.entities.message import Message as MessageEntity
from backend.domain.entities.snippet import Snippet as SnippetEntity
from backend.domain.entities.story import Story as StoryEntity
from backend.domain.entities.user import User as UserEntity

# Mappers
from backend.infrastructure.persistence.mappers import (
    message_entity_to_model,
    message_model_to_entity,
    snippet_entity_to_model,
    snippet_model_to_entity,
    story_entity_to_model,
    story_model_to_entity,
    user_entity_to_model,
    user_model_to_entity,
)


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            return user_model_to_entity(model)
        return None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        model = self.session.query(UserModel).filter(UserModel.email == email).first()
        if model:
            return user_model_to_entity(model)
        return None

    def save(self, user: UserEntity) -> UserEntity:
        if user.id:
            # Update existing
            model = (
                self.session.query(UserModel).filter(UserModel.id == user.id).first()
            )
            if model:
                user_entity_to_model(user, model)
            else:
                model = user_entity_to_model(user)
                self.session.add(model)
        else:
            # Create new
            model = user_entity_to_model(user)
            self.session.add(model)

        self.session.commit()
        self.session.refresh(model)
        return user_model_to_entity(model)

    def delete(self, user_id: int) -> bool:
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()
            return True
        return False

    def exists_by_email(self, email: str) -> bool:
        return (
            self.session.query(UserModel).filter(UserModel.email == email).first()
            is not None
        )


class SQLAlchemyStoryRepository(StoryRepository):
    """SQLAlchemy implementation of StoryRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, story_id: int) -> Optional[StoryEntity]:
        model = self.session.query(StoryModel).filter(StoryModel.id == story_id).first()
        if model:
            return story_model_to_entity(model)
        return None

    def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[StoryEntity]:
        models = (
            self.session.query(StoryModel)
            .filter(StoryModel.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [story_model_to_entity(m) for m in models]

    def save(self, story: StoryEntity) -> StoryEntity:
        if story.id:
            model = (
                self.session.query(StoryModel).filter(StoryModel.id == story.id).first()
            )
            if model:
                story_entity_to_model(story, model)
            else:
                model = story_entity_to_model(story)
                self.session.add(model)
        else:
            model = story_entity_to_model(story)
            self.session.add(model)

        self.session.commit()
        self.session.refresh(model)
        return story_model_to_entity(model)

    def delete(self, story_id: int) -> bool:
        model = self.session.query(StoryModel).filter(StoryModel.id == story_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()
            return True
        return False

    def count_by_user_id(self, user_id: int) -> int:
        return (
            self.session.query(StoryModel).filter(StoryModel.user_id == user_id).count()
        )


class SQLAlchemyMessageRepository(MessageRepository):
    """SQLAlchemy implementation of MessageRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, message_id: int) -> Optional[MessageEntity]:
        model = (
            self.session.query(MessageModel)
            .filter(MessageModel.id == message_id)
            .first()
        )
        if model:
            return message_model_to_entity(model)
        return None

    def get_by_story_id(
        self, story_id: int, skip: int = 0, limit: int = 100
    ) -> List[MessageEntity]:
        models = (
            self.session.query(MessageModel)
            .filter(MessageModel.story_id == story_id)
            .order_by(MessageModel.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [message_model_to_entity(m) for m in models]

    def save(self, message: MessageEntity) -> MessageEntity:
        model = message_entity_to_model(message)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return message_model_to_entity(model)

    def delete_by_story_id(self, story_id: int) -> int:
        count = (
            self.session.query(MessageModel)
            .filter(MessageModel.story_id == story_id)
            .delete()
        )
        self.session.commit()
        return count

    def count_by_story_id(self, story_id: int) -> int:
        return (
            self.session.query(MessageModel)
            .filter(MessageModel.story_id == story_id)
            .count()
        )


class SQLAlchemySnippetRepository(SnippetRepository):
    """SQLAlchemy implementation of SnippetRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, snippet_id: int) -> Optional[SnippetEntity]:
        model = (
            self.session.query(SnippetModel)
            .filter(SnippetModel.id == snippet_id)
            .first()
        )
        if model:
            return snippet_model_to_entity(model)
        return None

    def get_by_story_id(
        self, story_id: int, include_archived: bool = False
    ) -> List[SnippetEntity]:
        query = self.session.query(SnippetModel).filter(
            SnippetModel.story_id == story_id
        )
        if not include_archived:
            query = query.filter(SnippetModel.is_active == True)
        models = query.all()
        return [snippet_model_to_entity(m) for m in models]

    def get_by_user_id(
        self, user_id: int, include_archived: bool = False
    ) -> List[SnippetEntity]:
        query = self.session.query(SnippetModel).filter(SnippetModel.user_id == user_id)
        if not include_archived:
            query = query.filter(SnippetModel.is_active == True)
        models = query.all()
        return [snippet_model_to_entity(m) for m in models]

    def save(self, snippet: SnippetEntity) -> SnippetEntity:
        if snippet.id:
            model = (
                self.session.query(SnippetModel)
                .filter(SnippetModel.id == snippet.id)
                .first()
            )
            if model:
                snippet_entity_to_model(snippet, model)
            else:
                model = snippet_entity_to_model(snippet)
                self.session.add(model)
        else:
            model = snippet_entity_to_model(snippet)
            self.session.add(model)

        self.session.commit()
        self.session.refresh(model)
        return snippet_model_to_entity(model)

    def save_many(self, snippets: List[SnippetEntity]) -> List[SnippetEntity]:
        models = [snippet_entity_to_model(s) for s in snippets]
        self.session.add_all(models)
        self.session.commit()
        for m in models:
            self.session.refresh(m)
        return [snippet_model_to_entity(m) for m in models]

    def delete(self, snippet_id: int) -> bool:
        model = (
            self.session.query(SnippetModel)
            .filter(SnippetModel.id == snippet_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.commit()
            return True
        return False

    def delete_unlocked_by_story_id(self, story_id: int) -> int:
        count = (
            self.session.query(SnippetModel)
            .filter(SnippetModel.story_id == story_id)
            .filter(SnippetModel.is_locked == False)
            .delete()
        )
        self.session.commit()
        return count

    def count_locked_by_story_id(self, story_id: int) -> int:
        return (
            self.session.query(SnippetModel)
            .filter(SnippetModel.story_id == story_id)
            .filter(SnippetModel.is_locked == True)
            .count()
        )
