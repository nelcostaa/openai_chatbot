"""
Dependency Injection Container

Uses FastAPI's Depends() pattern combined with factory functions.
This is the A/C hybrid approach: manual constructor injection + FastAPI Depends().

Usage in endpoints:
    @router.post("/register")
    def register(
        input: UserRegister,
        use_case: RegisterUserUseCase = Depends(get_register_user_use_case)
    ):
        return use_case.execute(input)
"""

from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

# Database session
from backend.app.db.session import get_db

# Use cases
from backend.application.use_cases.auth import (
    GetCurrentUserUseCase,
    LoginUserUseCase,
    RegisterUserUseCase,
)
from backend.application.use_cases.interview import (
    AdvancePhaseUseCase,
    ProcessChatUseCase,
)
from backend.application.use_cases.story import (
    CreateStoryUseCase,
    DeleteStoryUseCase,
    GetStoryUseCase,
    ListStoriesUseCase,
)

# Repository implementations
from backend.infrastructure.persistence.repositories import (
    SQLAlchemyMessageRepository,
    SQLAlchemySnippetRepository,
    SQLAlchemyStoryRepository,
    SQLAlchemyUserRepository,
)

# Service implementations
from backend.infrastructure.services.ai_service import LangGraphAIService
from backend.infrastructure.services.auth_service import (
    BcryptPasswordService,
    JWTTokenService,
)

# ============================================================
# Service Singletons (cached)
# ============================================================


@lru_cache()
def get_password_service() -> BcryptPasswordService:
    """Get singleton password service."""
    return BcryptPasswordService()


@lru_cache()
def get_token_service() -> JWTTokenService:
    """Get singleton token service."""
    return JWTTokenService()


@lru_cache()
def get_ai_service() -> LangGraphAIService:
    """Get singleton AI service."""
    return LangGraphAIService()


# ============================================================
# Repository Factories (per-request, need DB session)
# ============================================================


def get_user_repository(db: Session = Depends(get_db)) -> SQLAlchemyUserRepository:
    """Get user repository for current request."""
    return SQLAlchemyUserRepository(db)


def get_story_repository(db: Session = Depends(get_db)) -> SQLAlchemyStoryRepository:
    """Get story repository for current request."""
    return SQLAlchemyStoryRepository(db)


def get_message_repository(
    db: Session = Depends(get_db),
) -> SQLAlchemyMessageRepository:
    """Get message repository for current request."""
    return SQLAlchemyMessageRepository(db)


def get_snippet_repository(
    db: Session = Depends(get_db),
) -> SQLAlchemySnippetRepository:
    """Get snippet repository for current request."""
    return SQLAlchemySnippetRepository(db)


# ============================================================
# Use Case Factories (compose repositories + services)
# ============================================================


def get_register_user_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    password_service: BcryptPasswordService = Depends(get_password_service),
    token_service: JWTTokenService = Depends(get_token_service),
) -> RegisterUserUseCase:
    """Get RegisterUserUseCase with dependencies injected."""
    return RegisterUserUseCase(
        user_repo=user_repo,
        password_service=password_service,
        token_service=token_service,
    )


def get_login_user_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    password_service: BcryptPasswordService = Depends(get_password_service),
    token_service: JWTTokenService = Depends(get_token_service),
) -> LoginUserUseCase:
    """Get LoginUserUseCase with dependencies injected."""
    return LoginUserUseCase(
        user_repo=user_repo,
        password_service=password_service,
        token_service=token_service,
    )


def get_current_user_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> GetCurrentUserUseCase:
    """Get GetCurrentUserUseCase with dependencies injected."""
    return GetCurrentUserUseCase(user_repo=user_repo)


def get_process_chat_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
    message_repo: SQLAlchemyMessageRepository = Depends(get_message_repository),
    ai_service: LangGraphAIService = Depends(get_ai_service),
) -> ProcessChatUseCase:
    """Get ProcessChatUseCase with dependencies injected."""
    return ProcessChatUseCase(
        story_repo=story_repo,
        message_repo=message_repo,
        ai_service=ai_service,
    )


def get_advance_phase_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
) -> AdvancePhaseUseCase:
    """Get AdvancePhaseUseCase with dependencies injected."""
    return AdvancePhaseUseCase(story_repo=story_repo)


def get_create_story_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
) -> CreateStoryUseCase:
    """Get CreateStoryUseCase with dependencies injected."""
    return CreateStoryUseCase(story_repo=story_repo)


def get_story_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
    message_repo: SQLAlchemyMessageRepository = Depends(get_message_repository),
) -> GetStoryUseCase:
    """Get GetStoryUseCase with dependencies injected."""
    return GetStoryUseCase(
        story_repo=story_repo,
        message_repo=message_repo,
    )


def get_list_stories_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
) -> ListStoriesUseCase:
    """Get ListStoriesUseCase with dependencies injected."""
    return ListStoriesUseCase(story_repo=story_repo)


def get_delete_story_use_case(
    story_repo: SQLAlchemyStoryRepository = Depends(get_story_repository),
    message_repo: SQLAlchemyMessageRepository = Depends(get_message_repository),
    snippet_repo: SQLAlchemySnippetRepository = Depends(get_snippet_repository),
) -> DeleteStoryUseCase:
    """Get DeleteStoryUseCase with dependencies injected."""
    return DeleteStoryUseCase(
        story_repo=story_repo,
        message_repo=message_repo,
        snippet_repo=snippet_repo,
    )
