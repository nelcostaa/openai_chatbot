"""
Phase Service - Domain service for interview phase management.

Contains business rules for phase transitions and prompts.
This is a pure domain service with no infrastructure dependencies.
"""

from typing import Dict, List, Optional

from backend.domain.entities.story import AgeRange, Phase

# Phase configuration with prompts (domain knowledge)
PHASE_PROMPTS: Dict[Phase, Dict[str, str]] = {
    Phase.GREETING: {
        "description": "Welcome and age selection",
        "prompt": """You are a warm, empathetic interviewer documenting a life story.

Your role: Guide the user through telling their life story chronologically.

Current phase: GREETING + AGE SELECTION (combined for efficiency)
- Welcome the user warmly (1 sentence)
- Explain briefly: "I'm here to help you capture your life story, chapter by chapter."
- Then ask for their age range to customize the journey:

"Before we begin, please select your age range:
1. Under 18
2. 18-30  
3. 31-45
4. 46-60
5. 61 and above"

Keep response SHORT (3-4 sentences max). Be warm and inviting.""",
    },
    Phase.FAMILY_HISTORY: {
        "description": "Family origins and ancestors",
        "prompt": """You are conducting a chronological life story interview. Phase: FAMILY HISTORY

Your goal: Explore family history - parents, grandparents, ancestors, and those who shaped the world the user was born into.

If this is the FIRST message in this phase:
- Acknowledge the transition warmly: "Wonderful! Let's start with your roots."
- Ask about their family background: "Tell me about your parents - where did they come from and what were they like?"

If they've already shared family history:
- Ask follow-up questions to explore deeper
- Topics: family stories, traditions, immigration, cultural heritage, how parents met

Keep it conversational (1-2 sentences). Be genuinely curious.""",
    },
    Phase.CHILDHOOD: {
        "description": "Ages 0-12",
        "prompt": """You are conducting a chronological life story interview. Phase: CHILDHOOD (Ages 0-12)

Your goal: Explore earliest memories and foundational years.

Topics to cover:
- Earliest memories
- Home and neighborhood
- School experiences
- Friends and play
- Family dynamics
- Formative events

Ask one thoughtful question at a time. Be warm and curious.
Keep responses to 1-2 sentences.""",
    },
    Phase.ADOLESCENCE: {
        "description": "Ages 13-17",
        "prompt": """You are conducting a chronological life story interview. Phase: ADOLESCENCE (Ages 13-17)

Your goal: Explore teenage years and identity formation.

Topics to cover:
- High school experiences
- Friendships and relationships
- Discovering interests/passions
- Family relationships during teen years
- Challenges and growth
- Dreams for the future

Ask one thoughtful question at a time. Be understanding of this complex period.
Keep responses to 1-2 sentences.""",
    },
    Phase.EARLY_ADULTHOOD: {
        "description": "Ages 18-30",
        "prompt": """You are conducting a chronological life story interview. Phase: EARLY ADULTHOOD (Ages 18-30)

Your goal: Explore the transition to independence and early career/education.

Topics to cover:
- Leaving home
- Education and career beginnings
- Romantic relationships
- Finding identity as an adult
- Major decisions and turning points
- Lessons learned

Ask one thoughtful question at a time. Acknowledge the challenges of this transition.
Keep responses to 1-2 sentences.""",
    },
    Phase.MIDLIFE: {
        "description": "Ages 31-60",
        "prompt": """You are conducting a chronological life story interview. Phase: MIDLIFE (Ages 31-60)

Your goal: Explore the rich middle years of life.

Topics to cover:
- Career development and changes
- Family life (if applicable)
- Major achievements
- Challenges overcome
- Values and priorities evolution
- Mentoring others

Ask one thoughtful question at a time. Honor the complexity of this life stage.
Keep responses to 1-2 sentences.""",
    },
    Phase.PRESENT: {
        "description": "Current life",
        "prompt": """You are conducting a chronological life story interview. Phase: PRESENT

Your goal: Explore current life and reflections.

Topics to cover:
- Current daily life
- What brings joy now
- Current challenges
- Relationships today
- Looking back - what are you most proud of?
- What wisdom would you share?

Ask one thoughtful question at a time. Help them appreciate their journey.
Keep responses to 1-2 sentences.""",
    },
    Phase.SYNTHESIS: {
        "description": "Final reflection and summary",
        "prompt": """You are conducting a chronological life story interview. Phase: SYNTHESIS

Your goal: Help synthesize their story into meaningful themes.

This is the final phase:
- Thank them for sharing their story
- Reflect back 2-3 major themes you noticed
- Ask: "If your life story had a title, what would it be?"
- Help them see the narrative arc of their journey

Be warm, appreciative, and insightful.
Keep responses to 2-3 sentences.""",
    },
}


class PhaseService:
    """
    Domain service for managing interview phases.

    This service contains business logic for:
    - Phase transitions
    - Phase prompts
    - Age-based phase filtering
    """

    @staticmethod
    def get_phases_for_age(age_range: Optional[AgeRange]) -> List[Phase]:
        """
        Get available phases based on user's age range.

        Args:
            age_range: User's age range (None returns all phases)

        Returns:
            List of phases available for this age range
        """
        from backend.domain.entities.story import AGE_PHASE_MAPPING

        if age_range is None:
            return list(Phase)

        return AGE_PHASE_MAPPING.get(age_range, list(Phase))

    @staticmethod
    def get_phase_prompt(phase: Phase) -> str:
        """
        Get the AI prompt for a specific phase.

        Args:
            phase: The interview phase

        Returns:
            The prompt string for the AI
        """
        config = PHASE_PROMPTS.get(phase)
        if config:
            return config.get("prompt", "")
        return PHASE_PROMPTS[Phase.GREETING]["prompt"]

    @staticmethod
    def get_phase_description(phase: Phase) -> str:
        """
        Get human-readable description of a phase.

        Args:
            phase: The interview phase

        Returns:
            Description string
        """
        config = PHASE_PROMPTS.get(phase)
        if config:
            return config.get("description", phase.value)
        return phase.value

    @staticmethod
    def parse_age_selection(input_value: str) -> Optional[AgeRange]:
        """
        Parse user's age selection input to AgeRange.

        Args:
            input_value: User input (1-5 or age range string)

        Returns:
            AgeRange enum or None if invalid
        """
        # Map numeric inputs to age ranges
        numeric_map = {
            "1": AgeRange.UNDER_18,
            "2": AgeRange.AGE_18_30,
            "3": AgeRange.AGE_31_45,
            "4": AgeRange.AGE_46_60,
            "5": AgeRange.AGE_61_PLUS,
        }

        # Try numeric first
        if input_value in numeric_map:
            return numeric_map[input_value]

        # Try direct enum value
        try:
            return AgeRange(input_value)
        except ValueError:
            return None

    @staticmethod
    def get_next_phase(
        current_phase: Phase, available_phases: List[Phase]
    ) -> Optional[Phase]:
        """
        Get the next phase in sequence.

        Args:
            current_phase: Current interview phase
            available_phases: List of phases available for this story

        Returns:
            Next phase or None if at end
        """
        if current_phase not in available_phases:
            return None

        idx = available_phases.index(current_phase)
        if idx >= len(available_phases) - 1:
            return None

        return available_phases[idx + 1]

    @staticmethod
    def can_transition(
        from_phase: Phase,
        to_phase: Phase,
        available_phases: List[Phase],
        age_range: Optional[AgeRange] = None,
    ) -> bool:
        """
        Check if a phase transition is valid.

        Args:
            from_phase: Current phase
            to_phase: Target phase
            available_phases: Phases available for this story
            age_range: User's age range (required to advance past AGE_SELECTION)

        Returns:
            True if transition is valid
        """
        # Both phases must be in available phases
        if from_phase not in available_phases or to_phase not in available_phases:
            return False

        from_idx = available_phases.index(from_phase)
        to_idx = available_phases.index(to_phase)

        # Can't go backward
        if to_idx < from_idx:
            return False

        # Must have age set to advance past AGE_SELECTION
        if to_idx > 1 and age_range is None:
            return False

        return True
