# Backend Clean Architecture Guide

This document explains the backend architecture following Clean Architecture principles, with clear layer separation and dependency injection.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTERFACE LAYER                                    │
│                    backend/app/ (FastAPI Framework)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Endpoints     │  │    Schemas      │  │   Middleware    │              │
│  │   (Controllers) │  │   (Pydantic)    │  │   (CORS, Auth)  │              │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘              │
├───────────┼─────────────────────────────────────────────────────────────────┤
│           ▼                                                                  │
│                          APPLICATION LAYER                                   │
│                        backend/application/                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │    Use Cases    │  │   Interfaces    │  │      DTOs       │              │
│  │  (Business Ops) │  │  (Abstractions) │  │  (Data Transfer)│              │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘              │
├───────────┼────────────────────┼────────────────────────────────────────────┤
│           ▼                    │                                             │
│                           DOMAIN LAYER                                       │
│                          backend/domain/                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │    Entities     │  │   Exceptions    │  │Domain Services  │              │
│  │ (Business Rules)│  │ (Domain Errors) │  │ (Phase Logic)   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                    ▲                                         │
│                       INFRASTRUCTURE LAYER                                   │
│                       backend/infrastructure/                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Repositories   │  │ External APIs   │  │  DI Container   │              │
│  │  (SQLAlchemy)   │  │ (AI, JWT, etc)  │  │  (Factories)    │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
backend/
├── app/                          # Interface Layer (FastAPI)
│   ├── main.py                   # Application entry point
│   ├── api/
│   │   └── endpoints/            # Route handlers (thin controllers)
│   │       ├── auth.py           # Auth endpoints
│   │       ├── stories.py        # Story CRUD endpoints
│   │       ├── interview.py      # Chat/interview endpoints
│   │       └── snippets.py       # Snippet endpoints
│   ├── core/
│   │   ├── agent.py              # LangGraph agent configuration
│   │   ├── auth.py               # FastAPI auth dependencies
│   │   └── security.py           # Security utilities
│   ├── db/
│   │   ├── base.py               # SQLAlchemy base imports
│   │   └── session.py            # Database session management
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── story.py
│   │   ├── message.py
│   │   └── snippets.py
│   └── services/
│       └── interview.py          # Interview service orchestration
│
├── domain/                       # Domain Layer (Pure Business Logic)
│   ├── __init__.py
│   ├── entities/                 # Domain entities
│   │   ├── __init__.py
│   │   ├── user.py               # User entity with business rules
│   │   ├── story.py              # Story entity with phase logic
│   │   ├── message.py            # Message entity
│   │   └── snippet.py            # Snippet entity
│   ├── exceptions.py             # Domain-specific exceptions
│   └── services/
│       ├── __init__.py
│       └── phase_service.py      # Interview phase management
│
├── application/                  # Application Layer (Use Cases)
│   ├── __init__.py
│   ├── interfaces/               # Abstract interfaces
│   │   ├── __init__.py
│   │   ├── repositories.py       # Repository abstractions
│   │   └── services.py           # Service abstractions
│   └── use_cases/                # Business operations
│       ├── __init__.py
│       ├── auth.py               # RegisterUser, LoginUser, GetCurrentUser
│       ├── interview.py          # ProcessChat, AdvancePhase
│       └── story.py              # CreateStory, GetStory, ListStories, DeleteStory
│
└── infrastructure/               # Infrastructure Layer (Implementations)
    ├── __init__.py
    ├── container.py              # Dependency injection container
    ├── persistence/
    │   ├── __init__.py
    │   ├── mappers.py            # Entity <-> ORM mappers
    │   └── repositories.py       # SQLAlchemy repository implementations
    └── services/
        ├── __init__.py
        ├── ai_service.py         # LangGraph AI service wrapper
        └── auth_service.py       # Password hashing & JWT services
```

---

## Layer Responsibilities

### Domain Layer (`backend/domain/`)

The innermost layer containing pure business logic with **zero external dependencies**.

#### Entities (`domain/entities/`)

Domain entities encapsulate business rules and validation:

```python
# domain/entities/user.py
@dataclass
class User:
    id: Optional[int]
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self._is_valid_email(self.email):
            raise ValidationError(f"Invalid email: {self.email}")
    
    def can_access_story(self, story: 'Story') -> bool:
        """Business rule: users can only access their own stories (unless admin)"""
        return self.is_admin or story.user_id == self.id
```

```python
# domain/entities/story.py
@dataclass
class Story:
    id: Optional[int]
    user_id: int
    title: str
    current_phase: Phase = Phase.GREETING
    age_range: Optional[AgeRange] = None
    
    def can_advance_to_phase(self, target_phase: Phase) -> bool:
        """Business rule: phases must progress in order"""
        return target_phase.value == self.current_phase.value + 1
    
    def advance_phase(self) -> None:
        """Advance to next phase with validation"""
        next_phase = Phase(self.current_phase.value + 1)
        if not self.can_advance_to_phase(next_phase):
            raise PhaseTransitionError(...)
        self.current_phase = next_phase
```

#### Domain Services (`domain/services/`)

Pure business logic that doesn't belong to a single entity:

```python
# domain/services/phase_service.py
class PhaseService:
    """Manages interview phase prompts and transitions"""
    
    def get_phase_prompt(self, phase: Phase, age_range: Optional[AgeRange]) -> str:
        """Get the AI system prompt for a specific phase"""
        base_prompt = self.PHASE_PROMPTS.get(phase, "")
        if age_range:
            base_prompt += f"\nUser is in age range: {age_range.value}"
        return base_prompt
    
    def get_phases_for_age(self, age_range: AgeRange) -> List[Phase]:
        """Get applicable phases based on user's age"""
        # Younger users skip certain phases
        ...
```

#### Domain Exceptions (`domain/exceptions.py`)

```python
class DomainError(Exception):
    """Base exception for domain errors"""

class EntityNotFoundError(DomainError):
    """Entity not found in repository"""

class AuthorizationError(DomainError):
    """User not authorized for this action"""

class PhaseTransitionError(DomainError):
    """Invalid phase transition attempted"""

class ValidationError(DomainError):
    """Business rule validation failed"""
```

---

### Application Layer (`backend/application/`)

Orchestrates use cases by combining domain entities with infrastructure through interfaces.

#### Interfaces (`application/interfaces/`)

Abstract contracts that infrastructure must implement:

```python
# application/interfaces/repositories.py
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        pass

class StoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, story_id: int) -> Optional[Story]:
        pass
    
    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Story]:
        pass
    
    @abstractmethod
    def save(self, story: Story) -> Story:
        pass
```

```python
# application/interfaces/services.py
class AIService(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: str,
        phase: Phase,
    ) -> AIResponse:
        pass

class PasswordService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass
    
    @abstractmethod
    def verify_password(self, password: str, hashed: str) -> bool:
        pass
```

#### Use Cases (`application/use_cases/`)

Single-purpose classes that implement business operations:

```python
# application/use_cases/auth.py
@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_service: PasswordService
    
    def execute(self, email: str, password: str) -> User:
        # Check if user exists
        existing = self.user_repository.get_by_email(email)
        if existing:
            raise DuplicateEntityError(f"User with email {email} already exists")
        
        # Create user with hashed password
        user = User(
            id=None,
            email=email,
            hashed_password=self.password_service.hash_password(password),
        )
        
        return self.user_repository.save(user)
```

```python
# application/use_cases/interview.py
@dataclass
class ProcessChatUseCase:
    story_repository: StoryRepository
    message_repository: MessageRepository
    ai_service: AIService
    phase_service: PhaseService
    
    async def execute(
        self,
        story_id: int,
        user_id: int,
        content: str,
    ) -> ProcessChatResponse:
        # Get story and verify access
        story = self.story_repository.get_by_id(story_id)
        if not story:
            raise EntityNotFoundError(f"Story {story_id} not found")
        if story.user_id != user_id:
            raise AuthorizationError("Cannot access this story")
        
        # Save user message
        user_message = Message(
            story_id=story_id,
            role=MessageRole.USER,
            content=content,
        )
        self.message_repository.save(user_message)
        
        # Get conversation history
        messages = self.message_repository.list_by_story(story_id)
        
        # Generate AI response
        system_prompt = self.phase_service.get_phase_prompt(
            story.current_phase,
            story.age_range,
        )
        ai_response = await self.ai_service.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            phase=story.current_phase,
        )
        
        # Save assistant message
        assistant_message = Message(
            story_id=story_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
        )
        self.message_repository.save(assistant_message)
        
        return ProcessChatResponse(
            message=assistant_message,
            phase=story.current_phase,
            model_used=ai_response.model_used,
        )
```

---

### Infrastructure Layer (`backend/infrastructure/`)

Implements interfaces with concrete technologies (SQLAlchemy, LangGraph, etc.).

#### Repository Implementations (`infrastructure/persistence/`)

```python
# infrastructure/persistence/repositories.py
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self._session.query(UserModel).filter_by(id=user_id).first()
        return UserMapper.to_entity(model) if model else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        model = self._session.query(UserModel).filter_by(email=email).first()
        return UserMapper.to_entity(model) if model else None
    
    def save(self, user: User) -> User:
        model = UserMapper.to_model(user)
        if user.id:
            existing = self._session.query(UserModel).filter_by(id=user.id).first()
            if existing:
                for key, value in model.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                model = existing
        else:
            self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return UserMapper.to_entity(model)
```

#### Entity Mappers (`infrastructure/persistence/mappers.py`)

Convert between domain entities and ORM models:

```python
# infrastructure/persistence/mappers.py
class UserMapper:
    @staticmethod
    def to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_admin=model.is_admin,
            created_at=model.created_at,
        )
    
    @staticmethod
    def to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=entity.email,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            is_admin=entity.is_admin,
            created_at=entity.created_at,
        )
```

#### Service Implementations (`infrastructure/services/`)

```python
# infrastructure/services/ai_service.py
class LangGraphAIService(AIService):
    def __init__(self, agent):
        self._agent = agent
    
    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: str,
        phase: Phase,
    ) -> AIResponse:
        # Convert domain messages to LangGraph format
        langchain_messages = [
            SystemMessage(content=system_prompt),
            *[self._to_langchain_message(m) for m in messages],
        ]
        
        # Invoke agent
        result = await self._agent.ainvoke({
            "messages": langchain_messages,
            "phase": phase.name,
        })
        
        return AIResponse(
            content=result["messages"][-1].content,
            model_used=result.get("model", "gemini"),
        )
```

#### Dependency Injection Container (`infrastructure/container.py`)

```python
# infrastructure/container.py
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db

# Repository factories
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db)

def get_story_repository(db: Session = Depends(get_db)) -> StoryRepository:
    return SQLAlchemyStoryRepository(db)

# Service factories
def get_password_service() -> PasswordService:
    return BcryptPasswordService()

def get_token_service() -> TokenService:
    return JWTTokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

# Use case factories
def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_repository=user_repo,
        password_service=password_service,
    )
```

---

### Interface Layer (`backend/app/`)

Thin controllers that delegate to use cases.

#### Endpoints (Controllers)

```python
# app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from backend.infrastructure.container import (
    get_register_user_use_case,
    get_login_user_use_case,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(
    request: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
):
    """Register a new user - delegates to use case"""
    try:
        user = use_case.execute(
            email=request.email,
            password=request.password,
        )
        return UserResponse.from_entity(user)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Request Flow Example

Here's how a chat request flows through all layers:

```
1. HTTP Request arrives at endpoint
   POST /api/stories/123/chat {"content": "Hello"}
   
2. Interface Layer (Controller)
   - Validates request with Pydantic schema
   - Extracts current_user from JWT
   - Calls use case via DI
   
3. Application Layer (Use Case)
   - ProcessChatUseCase.execute(story_id=123, user_id=1, content="Hello")
   - Calls story_repository.get_by_id(123)
   - Validates user authorization
   - Calls message_repository.save(user_message)
   - Calls ai_service.generate_response(...)
   - Calls message_repository.save(ai_message)
   - Returns ProcessChatResponse
   
4. Domain Layer (Business Rules)
   - Story entity validates phase transitions
   - Message entity validates role and content
   - PhaseService provides system prompts
   
5. Infrastructure Layer (Implementations)
   - SQLAlchemyStoryRepository queries PostgreSQL
   - SQLAlchemyMessageRepository persists messages
   - LangGraphAIService calls Gemini model
   - Mappers convert entities <-> ORM models
   
6. Response flows back through layers
   - Use case returns domain response
   - Controller converts to Pydantic response
   - FastAPI serializes to JSON
```

---

## Testing Strategy

### Unit Tests (Domain Layer)

Test business logic in isolation:

```python
def test_story_can_advance_phase():
    story = Story(id=1, user_id=1, title="Test", current_phase=Phase.GREETING)
    assert story.can_advance_to_phase(Phase.AGE_SELECTION) is True
    assert story.can_advance_to_phase(Phase.CHILDHOOD) is False

def test_user_cannot_access_other_users_story():
    user = User(id=1, email="test@test.com", hashed_password="...")
    story = Story(id=1, user_id=2, title="Other's Story")
    assert user.can_access_story(story) is False
```

### Integration Tests (Use Cases)

Test use cases with mock repositories:

```python
def test_register_user_creates_user():
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_email.return_value = None
    mock_repo.save.return_value = User(id=1, email="test@test.com", ...)
    
    use_case = RegisterUserUseCase(
        user_repository=mock_repo,
        password_service=BcryptPasswordService(),
    )
    
    user = use_case.execute("test@test.com", "password123")
    
    assert user.email == "test@test.com"
    mock_repo.save.assert_called_once()
```

### E2E Tests (Full Stack)

Test complete request/response cycle:

```python
def test_chat_endpoint_returns_ai_response(client, auth_headers):
    # Create story
    response = client.post("/api/stories", json={"title": "Test"}, headers=auth_headers)
    story_id = response.json()["id"]
    
    # Send chat message
    response = client.post(
        f"/api/stories/{story_id}/chat",
        json={"content": "Hello"},
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert "response" in response.json()
```

---

## Key Principles

1. **Dependency Rule**: Inner layers never import from outer layers
2. **Dependency Inversion**: High-level modules depend on abstractions
3. **Single Responsibility**: Each class has one reason to change
4. **Interface Segregation**: Small, focused interfaces
5. **Open/Closed**: Open for extension, closed for modification

## Common Patterns

- **Repository Pattern**: Abstract data access
- **Use Case Pattern**: Encapsulate business operations
- **Factory Pattern**: Create complex objects (DI container)
- **Mapper Pattern**: Convert between layer representations
- **Strategy Pattern**: Interchangeable algorithms (AI services)

---

## Running the Backend

```bash
# Development
uvicorn backend.app.main:app --reload --port 8000

# Production
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Tests
pytest tests/python/ -v
pytest tests/python/test_domain_entities.py -v  # Domain tests only
```
