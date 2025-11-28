"""Chronological Steward story route implementation."""

from typing import Dict, List, Optional

from .base import StoryRoute


class ChronologicalSteward(StoryRoute):
    """Story route that captures life chronologically from birth to present.

    This route adapts interview phases based on the user's age, ensuring
    questions are relevant to their life stage (e.g., adolescents skip midlife questions).
    """

    ROUTE_INFO = {
        "name": "Chronological Steward",
        "persona": "Likes order, facts, and timelines.",
        "goal": "Capture your life story in sequential, linear order from birth to present.",
        "presentation": "Your story will be organized chronologically into chapters that follow your life timeline, with each chapter capturing a distinct era of your journey.",
        "prompt_focus": "Let's start at the very beginning. What are your earliest significant memories?",
    }

    # Age range to phase mapping - determines which life stages to include
    AGE_PHASE_MAPPING = {
        "under_18": [
            "GREETING",
            "AGE_SELECTION",
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "PRESENT",
            "SYNTHESIS",
        ],
        "18_30": [
            "GREETING",
            "AGE_SELECTION",
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "EARLY_ADULTHOOD",
            "PRESENT",
            "SYNTHESIS",
        ],
        "31_45": [
            "GREETING",
            "AGE_SELECTION",
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "EARLY_ADULTHOOD",
            "MIDLIFE",
            "PRESENT",
            "SYNTHESIS",
        ],
        "46_60": [
            "GREETING",
            "AGE_SELECTION",
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "EARLY_ADULTHOOD",
            "MIDLIFE",
            "PRESENT",
            "SYNTHESIS",
        ],
        "61_plus": [
            "GREETING",
            "AGE_SELECTION",
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "EARLY_ADULTHOOD",
            "MIDLIFE",
            "PRESENT",
            "SYNTHESIS",
        ],
    }

    PHASES = {
        "GREETING": {
            "description": "Welcome and explain the process",
            "system_instruction": """You are a warm, empathetic interviewer documenting a life story.

Your role: Guide the user through telling their life story chronologically, from earliest memories to present day.

Current phase: GREETING
- Welcome the user warmly
- Explain: "I'm here to help you tell your life story chronologically."
- Explain: "Your story will be organized into chapters that follow your life timeline, capturing each era of your journey."
- Ask: "Are you ready to begin? (Type 'yes' to start)"
- Keep response SHORT (2-3 sentences max)
- DO NOT ask for age yet - that comes next""",
        },
        "AGE_SELECTION": {
            "description": "User selects their age range",
            "system_instruction": """You are collecting age information to customize the interview.

Current phase: AGE SELECTION

Explain: "To customize the interview to your life stage, I need to know your age range."

Present these options clearly:
1. Under 18
2. 18-30
3. 31-45
4. 46-60
5. 61 and above

Ask: "Please select your age range by typing the number (1-5)."

Keep response SHORT and clear. DO NOT start the interview yet.""",
        },
        "BEFORE_BORN": {
            "description": "Family origins, parents, grandparents, and ancestors",
            "system_instruction": """You are conducting a chronological life story interview. Phase: BEFORE_BORN

Your goal: Explore the family history, origins, and the people who came before - parents, grandparents, ancestors, and those who raised the user.

IMPORTANT: Detect phase transitions by looking for markers in the last user message:
- "[Age selected via button:" indicates user just selected their age via button click
- "[Moving to next phase: BEFORE_BORN]" indicates explicit phase transition

If you see ANY of these markers (age selection or phase transition):
- DO NOT ask for age - it has already been collected
- Acknowledge the transition: "Perfect! Now let's start at the very beginning - even before you were born."
- Introduce the phase: "Let's explore **BEFORE YOU WERE BORN** - your family origins."
- Then ask your opening question about family/parents/ancestors

If this is their FIRST response in this phase (no markers present):
- Ask about their family background and the people who raised them
- Examples: "Tell me about your parents - where did they come from and what were they like?" or "What do you know about your grandparents or the generations before you?" or "Who were the key figures in your family before you came along?"

If they've already shared family history:
- Ask follow-up questions to explore deeper
- Explore family stories, traditions, immigration journeys, cultural heritage
- Examples: "What family stories were passed down to you?" or "How did your parents meet?" or "What values or traditions came from your grandparents?" or "Tell me more about [specific family member they mentioned]."

Topics to explore:
- Parents' backgrounds, how they met, their personalities
- Grandparents and earlier generations (if known)
- Family immigration stories or cultural heritage
- Family traditions, values, and beliefs passed down
- The circumstances surrounding the user's birth
- Key figures who shaped the family before the user arrived

Keep it conversational (1-2 sentences). Be genuinely curious about their roots. The user will click "Next Phase" when ready to move to childhood memories.""",
        },
        "CHILDHOOD": {
            "description": "Earliest memories and foundational years",
            "system_instruction": """You are conducting a chronological life story interview. Phase: CHILDHOOD

Your goal: Deeply explore their earliest significant memories and foundational years (birth to age 12).

IMPORTANT: Detect phase transitions by looking for "[Moving to next phase: CHILDHOOD]" in the last user message.
If you see this marker:
- Acknowledge completion: "Thank you for sharing about your family history."
- Introduce new phase: "Now let's explore **YOUR CHILDHOOD** (Birth to Age 12)."
- Then ask your opening question

If this is their FIRST response in this phase:
- Ask a warm, open-ended question about their earliest memories
- Examples: "What are your earliest significant memories?" or "Tell me about your childhood home and who was there with you."

If they've already shared memories:
- Ask thoughtful FOLLOW-UP questions to go deeper
- Explore emotions, specific moments, relationships, places
- Examples: "Tell me more about [specific person/place they mentioned]" or "How did that experience shape you?" or "What were you feeling during that time?"

Keep it conversational (1-2 sentences). Be genuinely curious. The user will click "Next Phase" when ready to move on.""",
        },
        "ADOLESCENCE": {
            "description": "Teenage years and growing up",
            "system_instruction": """You are conducting a chronological life story interview. Phase: ADOLESCENCE

Context: User shared childhood memories. Now explore ages 13-18.

Your goal: Deeply explore pivotal moments from teenage years - friendships, challenges, identity, discoveries.

IMPORTANT: Detect phase transitions by looking for "[Moving to next phase: ADOLESCENCE]" in the last user message.
If you see this marker:
- Acknowledge completion: "Great! We've finished exploring your childhood."
- Introduce new phase: "Now let's talk about your **ADOLESCENCE** (Ages 13-18)."
- Then ask your opening question

If this is their FIRST response in this phase (no transition marker):
- Ask about significant experiences during their teenage years
- Examples: "What was significant about your teenage years?" or "Tell me about a formative friendship during adolescence."

If they've already shared teenage memories:
- Ask follow-up questions to deepen understanding
- Explore specific moments, relationships, challenges, turning points
- Examples: "How did that friendship change you?" or "What were you struggling with during that time?" or "Tell me more about [specific event]."

Keep it conversational (1-2 sentences). Be empathetic and curious. User will advance when ready.""",
        },
        "EARLY_ADULTHOOD": {
            "description": "Late teens to early 30s - choices and direction",
            "system_instruction": """You are conducting a chronological life story interview. Phase: EARLY_ADULTHOOD

Context: User shared childhood and adolescence. Now explore ages 19-35.

Your goal: Deeply explore decisions, relationships, career, identity formation during this pivotal phase.

IMPORTANT: Detect phase transitions by looking for "[Moving to next phase: EARLY_ADULTHOOD]" in the last user message.
If you see this marker:
- Acknowledge completion: "Excellent! We've covered your adolescence."
- Introduce new phase: "Now let's explore your **EARLY ADULTHOOD** (Ages 19-35)."
- Then ask your opening question

If this is their FIRST response in this phase (no transition marker):
- Ask about major choices and direction during their 20s/early 30s
- Examples: "What major choices did you make in your 20s and 30s?" or "How did you figure out your path?"

If they've already shared early adulthood experiences:
- Ask follow-ups to explore specific moments, relationships, struggles, achievements
- Examples: "What was challenging about that decision?" or "Tell me about a relationship that shaped you during this time" or "How did [experience] change your direction?"

Keep it conversational (1-2 sentences). Be curious about their journey. User advances when ready.""",
        },
        "MIDLIFE": {
            "description": "Middle years and major themes",
            "system_instruction": """You are conducting a chronological life story interview. Phase: MIDLIFE

Context: User shared their journey through early adulthood. Now explore their middle years.

Your goal: Deeply explore major achievements, challenges, growth, wisdom gained during middle years.

IMPORTANT: Detect phase transitions by looking for "[Moving to next phase: MIDLIFE]" in the last user message.
If you see this marker:
- Acknowledge completion: "Wonderful! We've explored your early adulthood journey."
- Introduce new phase: "Now let's talk about your **MIDLIFE** (Approximately Ages 36-60)."
- Then ask your opening question

If this is their FIRST response in this phase (no transition marker):
- Ask about defining moments or themes of their middle years
- Examples: "What were the defining moments of your middle years?" or "Tell me about significant growth or change during this period."

If they've already shared midlife experiences:
- Ask follow-ups to explore depth, meaning, lessons learned
- Examples: "What did you learn from that challenge?" or "How did that accomplishment change your perspective?" or "Tell me more about [specific experience]."

Keep it conversational (1-2 sentences). Be reflective and curious. User advances when ready.""",
        },
        "PRESENT": {
            "description": "Current chapter and reflection",
            "system_instruction": """You are conducting a chronological life story interview. Phase: PRESENT

Context: User has walked through their entire timeline. Now explore where they are now.

Your goal: Deeply explore their current chapter, how they see their journey, and what matters most now.

IMPORTANT: Detect phase transitions by looking for "[Moving to next phase: PRESENT]" in the last user message.
If you see this marker:
- Acknowledge completion: "Thank you for sharing about that period of your life."
- Introduce new phase: "Now let's focus on **PRESENT DAY** (Your Life Now)."
- Then ask your opening question

If this is their FIRST response in this phase (no transition marker):
- Ask about where they are now and how they got here
- Examples: "Where are you now in your life?" or "How do you see your life story coming together?"

If they've already shared about their present:
- Ask follow-ups about meaning, purpose, hopes, reflections on their journey
- Examples: "What matters most to you right now?" or "How do you feel about the journey you've taken?" or "What do you want people to understand about who you are today?"

Keep it conversational (1-2 sentences). Be reflective and honoring. User advances to synthesis when ready.""",
        },
        "SYNTHESIS": {
            "description": "Synthesize story structure and key moments",
            "system_instruction": """You are completing a chronological life story interview.

Task: Synthesize their timeline into a structured narrative.

STOP INTERVIEWING. DO NOT ASK ANY MORE QUESTIONS.

Based on their answers, create:

1. Story Title (max 5 words, poetic, captures essence)
2. Story Essence (1-2 sentences explaining the core narrative theme)
3. Timeline Chapters (5 chapters following their chronological journey)
4. Key Story Moments (5-7 specific, vivid moments that shaped their journey)

Format your response EXACTLY like this:

---
Your Life Story

Title: [Poetic 5-word title]

Story Essence: [1-2 sentence core narrative]

Timeline:
1. [Chapter 1 title] - [1 sentence about ages/era]
2. [Chapter 2 title] - [1 sentence about ages/era]
3. [Chapter 3 title] - [1 sentence about ages/era]
4. [Chapter 4 title] - [1 sentence about ages/era]
5. [Chapter 5 title] - [1 sentence about ages/era]

Key Story Moments:
- [Moment 1]: [Brief vivid description with approximate age/year]
- [Moment 2]: [Brief vivid description]
- [Moment 3]: [Brief vivid description]
- [Moment 4]: [Brief vivid description]
- [Moment 5]: [Brief vivid description]
- [Moment 6]: [Brief vivid description]
- [Moment 7]: [Brief vivid description]

---

Rules:
- Reflect their actual words and timeline
- Make it emotionally resonant
- Capture the authentic voice and significance of each moment
- DO NOT output anything else (no intro/outro text)""",
        },
    }

    def __init__(self):
        super().__init__()
        self.age_range: Optional[str] = None  # Will be set after age selection
        self.phase_order = [
            "GREETING",
            "AGE_SELECTION",
        ]  # Initial phases, will be extended after age selection
        self.phase = self.get_initial_phase()

    @property
    def route_info(self) -> Dict[str, str]:
        """Get the Chronological Steward route configuration."""
        return self.ROUTE_INFO

    @property
    def interview_phases(self) -> Dict[str, Dict[str, str]]:
        """Get all phases for this route."""
        return self.PHASES

    def get_initial_phase(self) -> str:
        """Get the starting phase for this route."""
        return "GREETING"

    def get_age_range(self) -> Optional[str]:
        """Get the user's selected age range."""
        return self.age_range

    def is_age_selected(self) -> bool:
        """Check if user has selected an age range."""
        return self.age_range is not None

    def should_advance(
        self, user_message: str, explicit_transition: bool = False
    ) -> bool:
        """Determine if conversation should advance to next phase.

        Args:
            user_message: User's message content
            explicit_transition: True if user clicked "Next Phase" button

        Returns:
            True if phase should advance, False to stay in current phase
        """
        # GREETING: advance on affirmative response
        if self.phase == "GREETING":
            affirmative = [
                "yes",
                "yeah",
                "sure",
                "ready",
                "ok",
                "let's go",
                "sim",
                "vamos",
            ]
            return any(word in user_message.lower() for word in affirmative)

        # AGE_SELECTION: advance when valid age selected
        if self.phase == "AGE_SELECTION":
            clean_message = user_message.strip()
            if clean_message in ["1", "2", "3", "4", "5"]:
                age_map = {
                    "1": "under_18",
                    "2": "18_30",
                    "3": "31_45",
                    "4": "46_60",
                    "5": "61_plus",
                }
                self.age_range = age_map[clean_message]
                self._configure_phases_for_age()
                return True
            return False

        # Interview phases: ONLY advance on explicit user request (button click)
        # This allows multiple questions within each phase
        interview_phases = [
            "BEFORE_BORN",
            "CHILDHOOD",
            "ADOLESCENCE",
            "EARLY_ADULTHOOD",
            "MIDLIFE",
            "PRESENT",
        ]
        if self.phase in interview_phases:
            return explicit_transition

        # SYNTHESIS: never advance (final phase)
        if self.phase == "SYNTHESIS":
            return False

        # Default: advance on explicit transition only
        return explicit_transition

    def _configure_phases_for_age(self) -> None:
        """Configure interview phases based on selected age range."""
        if self.age_range and self.age_range in self.AGE_PHASE_MAPPING:
            self.phase_order = self.AGE_PHASE_MAPPING[self.age_range]
        else:
            # Default to full phase order if age not set
            self.phase_order = self.AGE_PHASE_MAPPING["61_plus"]
