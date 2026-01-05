"""
Domain Exceptions

Custom exceptions for domain-specific errors.
These exceptions are framework-agnostic and represent business rule violations.
"""


class DomainError(Exception):
    """Base exception for all domain errors."""

    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity cannot be found."""

    def __init__(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class AuthorizationError(DomainError):
    """Raised when a user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message)


class ValidationError(DomainError):
    """Raised when validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error on {field}: {message}")


class PhaseTransitionError(DomainError):
    """Raised when an invalid phase transition is attempted."""

    def __init__(self, current_phase: str, target_phase: str, reason: str = ""):
        self.current_phase = current_phase
        self.target_phase = target_phase
        msg = f"Cannot transition from {current_phase} to {target_phase}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class StoryCompletedError(DomainError):
    """Raised when trying to modify a completed story."""

    def __init__(self, story_id: int):
        self.story_id = story_id
        super().__init__(
            f"Story {story_id} is already completed and cannot be modified"
        )


class DuplicateEntityError(DomainError):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field}={value} already exists")


class AIServiceError(DomainError):
    """Raised when AI service encounters an error."""

    def __init__(self, message: str, model: str = None, attempts: int = 0):
        self.model = model
        self.attempts = attempts
        super().__init__(message)


class RateLimitError(AIServiceError):
    """Raised when AI service rate limit is exceeded."""

    def __init__(self, model: str, attempts: int):
        super().__init__(
            f"Rate limit exceeded after {attempts} attempts on model {model}",
            model=model,
            attempts=attempts,
        )
