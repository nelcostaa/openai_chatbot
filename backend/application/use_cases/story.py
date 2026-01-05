"""
Story Use Cases

Application logic for story management.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.application.interfaces.repositories import (
    MessageRepository,
    SnippetRepository,
    StoryRepository,
)
from backend.domain.entities.story import AgeRange, Phase, Story, StoryStatus
from backend.domain.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
)


@dataclass
class CreateStoryInput:
    """Input DTO for story creation."""

    user_id: int
    title: str = "Untitled Story"
    route_type: str = "chronological"
    age_range: Optional[str] = None


@dataclass
class CreateStoryOutput:
    """Output DTO for story creation."""

    id: int
    title: str
    route_type: str
    current_phase: str
    age_range: Optional[str]
    status: str


class CreateStoryUseCase:
    """
    Use case for creating a new story.

    Business rules:
    - Story belongs to the authenticated user
    - Initial phase is GREETING
    - Age range can be set on creation or later
    """

    def __init__(self, story_repo: StoryRepository):
        self.story_repo = story_repo

    def execute(self, input_dto: CreateStoryInput) -> CreateStoryOutput:
        """
        Create a new story.

        Args:
            input_dto: Story creation data

        Returns:
            Created story details
        """
        # Create domain entity
        story = Story(
            user_id=input_dto.user_id,
            title=input_dto.title,
            route_type=input_dto.route_type,
            current_phase=Phase.GREETING,
            status=StoryStatus.DRAFT,
        )

        # Set age range if provided
        if input_dto.age_range:
            try:
                story.set_age_range(AgeRange(input_dto.age_range))
            except ValueError:
                raise ValidationError(
                    "age_range", f"Invalid age range: {input_dto.age_range}"
                )

        # Persist
        saved = self.story_repo.save(story)

        return CreateStoryOutput(
            id=saved.id,
            title=saved.title,
            route_type=saved.route_type,
            current_phase=(
                saved.current_phase.value
                if isinstance(saved.current_phase, Phase)
                else saved.current_phase
            ),
            age_range=saved.age_range.value if saved.age_range else None,
            status=(
                saved.status.value
                if isinstance(saved.status, StoryStatus)
                else saved.status
            ),
        )


@dataclass
class GetStoryInput:
    """Input DTO for getting a story."""

    story_id: int
    user_id: int


@dataclass
class StoryDetailOutput:
    """Output DTO for story details."""

    id: int
    title: str
    route_type: str
    current_phase: str
    age_range: Optional[str]
    status: str
    available_phases: List[str]
    phase_index: int
    progress_percentage: float
    message_count: int


class GetStoryUseCase:
    """Use case for getting story details."""

    def __init__(self, story_repo: StoryRepository, message_repo: MessageRepository):
        self.story_repo = story_repo
        self.message_repo = message_repo

    def execute(self, input_dto: GetStoryInput) -> StoryDetailOutput:
        """
        Get story details.

        Args:
            input_dto: Story ID and user ID

        Returns:
            Story details

        Raises:
            EntityNotFoundError: If story not found
            AuthorizationError: If user doesn't own story
        """
        story = self.story_repo.get_by_id(input_dto.story_id)
        if not story:
            raise EntityNotFoundError("Story", input_dto.story_id)

        if story.user_id != input_dto.user_id:
            raise AuthorizationError("You don't have access to this story")

        message_count = self.message_repo.count_by_story_id(story.id)

        return StoryDetailOutput(
            id=story.id,
            title=story.title,
            route_type=story.route_type,
            current_phase=(
                story.current_phase.value
                if isinstance(story.current_phase, Phase)
                else story.current_phase
            ),
            age_range=story.age_range.value if story.age_range else None,
            status=(
                story.status.value
                if isinstance(story.status, StoryStatus)
                else story.status
            ),
            available_phases=[p.value for p in story.available_phases],
            phase_index=story.phase_index,
            progress_percentage=story.progress_percentage,
            message_count=message_count,
        )


@dataclass
class ListStoriesInput:
    """Input DTO for listing stories."""

    user_id: int
    skip: int = 0
    limit: int = 100


@dataclass
class StoryListItemOutput:
    """Output DTO for story list item."""

    id: int
    title: str
    current_phase: str
    status: str
    progress_percentage: float


class ListStoriesUseCase:
    """Use case for listing user's stories."""

    def __init__(self, story_repo: StoryRepository):
        self.story_repo = story_repo

    def execute(self, input_dto: ListStoriesInput) -> List[StoryListItemOutput]:
        """
        List user's stories.

        Args:
            input_dto: List parameters

        Returns:
            List of story summaries
        """
        stories = self.story_repo.get_by_user_id(
            input_dto.user_id,
            skip=input_dto.skip,
            limit=input_dto.limit,
        )

        return [
            StoryListItemOutput(
                id=s.id,
                title=s.title,
                current_phase=(
                    s.current_phase.value
                    if isinstance(s.current_phase, Phase)
                    else s.current_phase
                ),
                status=(
                    s.status.value if isinstance(s.status, StoryStatus) else s.status
                ),
                progress_percentage=s.progress_percentage,
            )
            for s in stories
        ]


class DeleteStoryUseCase:
    """Use case for deleting a story."""

    def __init__(
        self,
        story_repo: StoryRepository,
        message_repo: MessageRepository,
        snippet_repo: SnippetRepository,
    ):
        self.story_repo = story_repo
        self.message_repo = message_repo
        self.snippet_repo = snippet_repo

    def execute(self, story_id: int, user_id: int) -> bool:
        """
        Delete a story and all related data.

        Args:
            story_id: Story to delete
            user_id: User requesting deletion

        Returns:
            True if deleted

        Raises:
            EntityNotFoundError: If story not found
            AuthorizationError: If user doesn't own story
        """
        story = self.story_repo.get_by_id(story_id)
        if not story:
            raise EntityNotFoundError("Story", story_id)

        if story.user_id != user_id:
            raise AuthorizationError("You don't have access to this story")

        # Delete related data (cascade should handle this, but explicit is safer)
        self.message_repo.delete_by_story_id(story_id)
        self.snippet_repo.delete_unlocked_by_story_id(story_id)

        # Delete story
        return self.story_repo.delete(story_id)
