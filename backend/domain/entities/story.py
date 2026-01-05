"""
Story Entity - Core domain representation of a life story interview.

This is a pure Python class with no framework dependencies.
It contains business rules for story management and phase transitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class StoryStatus(str, Enum):
    """Story lifecycle status."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Phase(str, Enum):
    """Interview phases in chronological order."""

    GREETING = "GREETING"
    AGE_SELECTION = "AGE_SELECTION"
    FAMILY_HISTORY = "FAMILY_HISTORY"
    CHILDHOOD = "CHILDHOOD"
    ADOLESCENCE = "ADOLESCENCE"
    EARLY_ADULTHOOD = "EARLY_ADULTHOOD"
    MIDLIFE = "MIDLIFE"
    PRESENT = "PRESENT"
    SYNTHESIS = "SYNTHESIS"


class AgeRange(str, Enum):
    """User age ranges for phase filtering."""

    UNDER_18 = "under_18"
    AGE_18_30 = "18_30"
    AGE_31_45 = "31_45"
    AGE_46_60 = "46_60"
    AGE_61_PLUS = "61_plus"


# Age-to-phases mapping (domain business rule)
AGE_PHASE_MAPPING = {
    AgeRange.UNDER_18: [
        Phase.GREETING,
        Phase.AGE_SELECTION,
        Phase.FAMILY_HISTORY,
        Phase.CHILDHOOD,
        Phase.ADOLESCENCE,
        Phase.PRESENT,
        Phase.SYNTHESIS,
    ],
    AgeRange.AGE_18_30: [
        Phase.GREETING,
        Phase.AGE_SELECTION,
        Phase.FAMILY_HISTORY,
        Phase.CHILDHOOD,
        Phase.ADOLESCENCE,
        Phase.EARLY_ADULTHOOD,
        Phase.PRESENT,
        Phase.SYNTHESIS,
    ],
    AgeRange.AGE_31_45: [
        Phase.GREETING,
        Phase.AGE_SELECTION,
        Phase.FAMILY_HISTORY,
        Phase.CHILDHOOD,
        Phase.ADOLESCENCE,
        Phase.EARLY_ADULTHOOD,
        Phase.MIDLIFE,
        Phase.PRESENT,
        Phase.SYNTHESIS,
    ],
    AgeRange.AGE_46_60: [
        Phase.GREETING,
        Phase.AGE_SELECTION,
        Phase.FAMILY_HISTORY,
        Phase.CHILDHOOD,
        Phase.ADOLESCENCE,
        Phase.EARLY_ADULTHOOD,
        Phase.MIDLIFE,
        Phase.PRESENT,
        Phase.SYNTHESIS,
    ],
    AgeRange.AGE_61_PLUS: [
        Phase.GREETING,
        Phase.AGE_SELECTION,
        Phase.FAMILY_HISTORY,
        Phase.CHILDHOOD,
        Phase.ADOLESCENCE,
        Phase.EARLY_ADULTHOOD,
        Phase.MIDLIFE,
        Phase.PRESENT,
        Phase.SYNTHESIS,
    ],
}


@dataclass
class Story:
    """
    Domain entity representing a life story interview.

    A story tracks the progression through interview phases,
    contains all messages, and belongs to a user.
    """

    id: Optional[int] = None
    user_id: Optional[int] = None
    title: str = "Untitled Story"
    route_type: str = "chronological"
    current_phase: Phase = Phase.GREETING
    age_range: Optional[AgeRange] = None
    status: StoryStatus = StoryStatus.DRAFT
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize entity after initialization."""
        # Convert string phase to enum if needed
        if isinstance(self.current_phase, str):
            self.current_phase = Phase(self.current_phase)

        # Convert string status to enum if needed
        if isinstance(self.status, str):
            self.status = StoryStatus(self.status)

        # Convert string age_range to enum if needed
        if isinstance(self.age_range, str):
            self.age_range = AgeRange(self.age_range)

    @property
    def available_phases(self) -> List[Phase]:
        """Get phases available for this story based on age range."""
        if self.age_range is None:
            # Default to full phase list if age not selected
            return list(Phase)
        return AGE_PHASE_MAPPING.get(self.age_range, list(Phase))

    @property
    def phase_index(self) -> int:
        """Get current phase index in available phases."""
        phases = self.available_phases
        if self.current_phase in phases:
            return phases.index(self.current_phase)
        return 0

    @property
    def is_complete(self) -> bool:
        """Check if interview has reached synthesis phase."""
        return self.current_phase == Phase.SYNTHESIS

    @property
    def progress_percentage(self) -> float:
        """Calculate interview progress as percentage."""
        phases = self.available_phases
        if not phases:
            return 0.0
        return (self.phase_index / (len(phases) - 1)) * 100

    def set_age_range(self, age_range: AgeRange) -> None:
        """
        Set user's age range and configure available phases.

        Args:
            age_range: The user's selected age range

        Raises:
            ValueError: If age range is invalid or already set
        """
        if self.age_range is not None:
            raise ValueError("Age range already set for this story")

        if isinstance(age_range, str):
            age_range = AgeRange(age_range)

        self.age_range = age_range

    def can_advance_to(self, target_phase: Phase) -> bool:
        """
        Check if story can transition to target phase.

        Business rules:
        - Can only advance to phases in available_phases
        - Can only advance forward (not backward)
        - Must have age_range set to advance past AGE_SELECTION
        """
        available = self.available_phases

        if target_phase not in available:
            return False

        current_idx = self.phase_index
        target_idx = available.index(target_phase)

        # Can't go backward
        if target_idx < current_idx:
            return False

        # Must have age set to advance past AGE_SELECTION
        if target_idx > 1 and self.age_range is None:
            return False

        return True

    def advance_phase(self) -> Phase:
        """
        Advance to the next phase.

        Returns:
            The new current phase

        Raises:
            ValueError: If cannot advance (already at last phase)
        """
        phases = self.available_phases
        current_idx = self.phase_index

        if current_idx >= len(phases) - 1:
            raise ValueError("Already at final phase")

        next_phase = phases[current_idx + 1]

        if not self.can_advance_to(next_phase):
            raise ValueError(f"Cannot advance to {next_phase}")

        self.current_phase = next_phase

        # Update status when advancing past greeting
        if self.status == StoryStatus.DRAFT and current_idx > 0:
            self.status = StoryStatus.IN_PROGRESS

        # Mark complete when reaching synthesis
        if next_phase == Phase.SYNTHESIS:
            self.status = StoryStatus.COMPLETED

        return self.current_phase

    def jump_to_phase(self, target_phase: Phase) -> Phase:
        """
        Jump directly to a specific phase (for navigation).

        Args:
            target_phase: The phase to jump to

        Returns:
            The new current phase

        Raises:
            ValueError: If target phase is not available
        """
        if isinstance(target_phase, str):
            target_phase = Phase(target_phase)

        if target_phase not in self.available_phases:
            raise ValueError(f"Phase {target_phase} not available for this story")

        self.current_phase = target_phase
        return self.current_phase

    def complete(self) -> None:
        """Mark story as completed."""
        self.status = StoryStatus.COMPLETED

    def archive(self) -> None:
        """Archive the story."""
        self.status = StoryStatus.ARCHIVED
