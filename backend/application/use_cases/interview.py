"""
Interview Use Cases

Application logic for the AI interview flow.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.application.interfaces.repositories import (
    MessageRepository,
    StoryRepository,
)
from backend.application.interfaces.services import AIService, ChatMessage
from backend.domain.entities.message import Message, MessageRole
from backend.domain.entities.story import Phase, Story
from backend.domain.exceptions import (
    AuthorizationError,
    EntityNotFoundError,
    PhaseTransitionError,
)
from backend.domain.services.phase_service import PhaseService


@dataclass
class ProcessChatInput:
    """Input DTO for processing a chat message."""

    story_id: int
    user_id: int
    message: str


@dataclass
class ProcessChatOutput:
    """Output DTO for chat response."""

    message_id: int
    role: str
    content: str
    phase: str
    model: str
    attempts: int


class ProcessChatUseCase:
    """
    Use case for processing a chat message in an interview.

    Business rules:
    - Story must exist and belong to user
    - User message is saved first
    - AI generates response based on current phase
    - AI response is saved
    - Returns the AI response
    """

    # Maximum messages to include in context
    MAX_HISTORY_MESSAGES = 20

    def __init__(
        self,
        story_repo: StoryRepository,
        message_repo: MessageRepository,
        ai_service: AIService,
    ):
        self.story_repo = story_repo
        self.message_repo = message_repo
        self.ai_service = ai_service

    def execute(self, input_dto: ProcessChatInput) -> ProcessChatOutput:
        """
        Process a chat message and generate AI response.

        Args:
            input_dto: Chat input data

        Returns:
            Chat response with AI message

        Raises:
            EntityNotFoundError: If story not found
            AuthorizationError: If user doesn't own story
        """
        # Get story
        story = self.story_repo.get_by_id(input_dto.story_id)
        if not story:
            raise EntityNotFoundError("Story", input_dto.story_id)

        # Verify ownership
        if story.user_id != input_dto.user_id:
            raise AuthorizationError("You don't have access to this story")

        # Get current phase
        current_phase = story.current_phase
        if isinstance(current_phase, str):
            current_phase = Phase(current_phase)

        # Save user message
        user_message = Message(
            story_id=story.id,
            role=MessageRole.USER,
            content=input_dto.message,
            phase_context=current_phase.value,
        )
        self.message_repo.save(user_message)

        # Load conversation history
        history = self.message_repo.get_by_story_id(
            story.id, limit=self.MAX_HISTORY_MESSAGES
        )

        # Convert to ChatMessage format
        chat_messages = [
            ChatMessage(
                role=m.role.value if isinstance(m.role, MessageRole) else m.role,
                content=m.content,
            )
            for m in history
        ]

        # Get phase instruction
        phase_instruction = PhaseService.get_phase_prompt(current_phase)

        # Generate AI response
        ai_response = self.ai_service.generate_response(
            messages=chat_messages,
            system_instruction=phase_instruction,
        )

        # Save AI message
        ai_message = Message(
            story_id=story.id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            phase_context=current_phase.value,
            tokens_used=ai_response.tokens_used,
        )
        saved_ai_message = self.message_repo.save(ai_message)

        return ProcessChatOutput(
            message_id=saved_ai_message.id,
            role="assistant",
            content=ai_response.content,
            phase=current_phase.value,
            model=ai_response.model,
            attempts=ai_response.attempts,
        )


@dataclass
class AdvancePhaseInput:
    """Input DTO for advancing interview phase."""

    story_id: int
    user_id: int
    target_phase: Optional[str] = None  # If None, advance to next


@dataclass
class AdvancePhaseOutput:
    """Output DTO for phase advancement."""

    previous_phase: str
    current_phase: str
    available_phases: List[str]
    phase_index: int


class AdvancePhaseUseCase:
    """
    Use case for advancing the interview phase.

    Business rules:
    - Story must exist and belong to user
    - Phase transition must be valid
    - Age must be set to advance past AGE_SELECTION
    """

    def __init__(self, story_repo: StoryRepository):
        self.story_repo = story_repo

    def execute(self, input_dto: AdvancePhaseInput) -> AdvancePhaseOutput:
        """
        Advance to next phase or specified phase.

        Args:
            input_dto: Phase advancement data

        Returns:
            Phase advancement result

        Raises:
            EntityNotFoundError: If story not found
            AuthorizationError: If user doesn't own story
            PhaseTransitionError: If transition invalid
        """
        # Get story
        story = self.story_repo.get_by_id(input_dto.story_id)
        if not story:
            raise EntityNotFoundError("Story", input_dto.story_id)

        # Verify ownership
        if story.user_id != input_dto.user_id:
            raise AuthorizationError("You don't have access to this story")

        previous_phase = story.current_phase

        # Advance phase
        if input_dto.target_phase:
            target = Phase(input_dto.target_phase)
            if not story.can_advance_to(target):
                raise PhaseTransitionError(
                    str(previous_phase),
                    input_dto.target_phase,
                    "Invalid phase transition",
                )
            story.jump_to_phase(target)
        else:
            story.advance_phase()

        # Save
        self.story_repo.save(story)

        return AdvancePhaseOutput(
            previous_phase=(
                str(previous_phase.value)
                if isinstance(previous_phase, Phase)
                else str(previous_phase)
            ),
            current_phase=(
                str(story.current_phase.value)
                if isinstance(story.current_phase, Phase)
                else str(story.current_phase)
            ),
            available_phases=[p.value for p in story.available_phases],
            phase_index=story.phase_index,
        )
