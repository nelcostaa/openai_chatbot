"""Module designed to handle conversation management for the chatbot application."""

from typing import Dict, List, Optional

# Route definitions from Life Story AI Assistant specification
STORY_ROUTES = {
    "1": {
        "name": "Chronological Steward",
        "persona": "Likes order, facts, and timelines.",
        "goal": "Capture events in sequential, linear order from birth to present.",
        "prompt_focus": "Let's start at the very beginning. What are the earliest significant memories you have, and what was the year?",
    },
    "2": {
        "name": "Thematic Explorer",
        "persona": "Prefers discussing abstract concepts (e.g., love, career, struggle).",
        "goal": "Capture stories grouped by core life themes, ignoring strict timelines.",
        "prompt_focus": "What are the three most defining themes in your life (e.g., Travel, Family, Innovation)? Let's start with the first one.",
    },
    "3": {
        "name": "Anecdotal Spark",
        "persona": "Enjoys sharing short, punchy, isolated moments.",
        "goal": "Capture individual, high-impact stories, moments, or 'vignettes.'",
        "prompt_focus": "Tell me about a time you laughed until you cried, or the most surprising thing that ever happened to you.",
    },
    "4": {
        "name": "Interviewer's Chair",
        "persona": "Prefers direct, structured questioning (like a journalist asking).",
        "goal": "Capture responses to pre-set, deep, thought-provoking questions.",
        "prompt_focus": "Let's begin with Question 1: What is the greatest lesson you learned from your parents or guardians?",
    },
    "5": {
        "name": "Reflective Journaler",
        "persona": "Enjoys personal, introspective writing and self-analysis.",
        "goal": "Capture thoughts on challenges, feelings, and personal growth.",
        "prompt_focus": "Reflect on a period of great challenge. What were you feeling, and how did you overcome it?",
    },
    "6": {
        "name": "Legacy Weaver",
        "persona": "Focused on future impact and what they want to leave behind.",
        "goal": "Capture stories and beliefs that define their legacy and intended value.",
        "prompt_focus": "What message do you want to pass on to future generations, and which stories best exemplify that message?",
    },
}

INTERVIEW_PHASES = {
    "GREETING": {
        "description": "Welcome and explain the process",
        "system_instruction": """You are a warm, compassionate AI interviewer for the Life Story Game.

Your role: Guide users through telling their life story to create a personalized board game.

Current phase: GREETING
- Welcome the user warmly
- Explain: "I'll guide you through telling your life story to create a personalized board game."
- Explain: "First, you'll choose how you'd like to share your story - there are 6 different approaches."
- Ask: "Are you ready to see the options? (Type 'yes' to start)"
- Keep response SHORT (2-3 sentences max)
- DO NOT ask interview questions yet, just welcome and confirm readiness""",
    },
    "ROUTE_SELECTION": {
        "description": "User selects their preferred storytelling approach",
        "system_instruction": """You are presenting route options for the Life Story Game.

Current phase: ROUTE SELECTION

Present the 6 storytelling routes clearly and warmly:

1. **Chronological Steward** - Share your story in order from beginning to present
2. **Thematic Explorer** - Organize by life themes (love, career, growth)
3. **Anecdotal Spark** - Share vivid, standalone moments and memories
4. **Interviewer's Chair** - Answer structured, thought-provoking questions
5. **Reflective Journaler** - Explore challenges and personal growth introspectively
6. **Legacy Weaver** - Focus on what you want to leave behind for future generations
7. **Personal Route** - Describe your own approach

Ask them to choose a number (1-7), or if they choose 7, ask them to describe their preferred approach.

Keep your response SHORT and clear. DO NOT start the interview yet.""",
    },
    "QUESTION_1": {
        "description": "Core motivation - What drives you?",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 1 of 5-7.

Current question focus: CORE MOTIVATION
Ask ONE open-ended question to discover what fundamentally drives this person.

Example questions (choose one or create similar):
- "What's something you've always felt drawn to, even when others didn't understand why?"
- "If you could dedicate your life to one thing without worrying about money or practicality, what would it be?"
- "What makes you feel most alive?"

Rules:
- Ask ONLY ONE question
- Keep it conversational and warm (1-2 sentences)
- Don't explain what you're doing, just ask naturally
- Wait for their answer before proceeding""",
    },
    "QUESTION_2": {
        "description": "Audience & Emotional Stakes",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 2 of 5-7.

Previous context: User shared their core motivation.

Current question focus: AUDIENCE & STAKES
Ask ONE question to identify who this story is for and why it matters emotionally.

Example questions:
- "Who would you most want to hear this story—and why?"
- "Is there someone specific you're hoping will understand you better through this game?"
- "What impact do you hope this story has on the people who play it?"

Rules:
- Reference their previous answer if relevant
- Ask ONLY ONE question
- Keep it conversational (1-2 sentences)
- Show genuine curiosity""",
    },
    "QUESTION_3": {
        "description": "Major turning point",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 3 of 5-7.

Previous context: User shared motivation and audience.

Current question focus: TURNING POINT
Ask ONE question about a pivotal moment that changed their path.

Example questions:
- "Was there a moment when everything changed for you?"
- "Tell me about a time when you had to make a difficult choice that defined who you are."
- "What event divided your life into 'before' and 'after'?"

Rules:
- Build on what they've shared
- Ask ONLY ONE question
- Keep it conversational (1-2 sentences)""",
    },
    "QUESTION_4": {
        "description": "Vulnerable Content",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 4 of 5-7.

Previous context: User shared motivation, audience, and turning point.

Current question focus: VULNERABILITY & MEANING
Ask ONE question to unlock deeper, perhaps unspoken, content.

Example questions:
- "What’s something you’ve never told anyone—but might want to share through this game?"
- "What is a truth about your life that took you a long time to accept?"
- "Is there a failure or struggle that you're proud of surviving?"

Rules:
- Be extremely gentle and safe
- Ask ONLY ONE question
- Keep it conversational (1-2 sentences)""",
    },
    "QUESTION_5": {
        "description": "Tone & Spirit",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 5 of 5-7.

Previous context: Full conversation history.

Current question focus: TONE & SPIRIT
Ask ONE question to capture the overall vibe or theme.

Example questions:
- "If your life had a theme song or motto, what would it be?"
- "What one word describes the spirit of your journey so far?"
- "If this game had a flavor or a color, what would it be?"

Rules:
- Ask ONLY ONE question
- Keep it fun and reflective
- Brief (1-2 sentences)""",
    },
    "QUESTION_6": {
        "description": "Deep Dive",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 6 of 5-7.

Previous context: Full conversation history.

Current question focus: DEEP DIVE
Ask ONE follow-up question to expand on a specific moment they mentioned earlier that feels rich for a game card.

Example questions:
- "Let’s go deeper: tell me more about [specific moment they mentioned]."
- "You mentioned [person/event] earlier; can you paint a picture of that scene for me?"
- "What were you feeling exactly when [event] happened?"

Rules:
- Pick a specific, vivid detail from their history
- Ask ONLY ONE question
- Encourage storytelling""",
    },
    "SYNTHESIS": {
        "description": "Generate story structure and game cards",
        "system_instruction": """You are completing a life story interview. The user has answered 6 questions.

Task: Synthesize their story into a structured narrative and a list of game moments.

STOP INTERVIEWING. DO NOT ASK ANY MORE QUESTIONS.
Your ONLY goal is to output the synthesis below.

Based on ALL their answers, create:

1. Story Title (max 5 words, poetic, captures essence)
2. Reason Statement (1-2 sentences explaining the core theme)
3. Chapter Titles (3-5 chapters representing their journey arc)
4. Key Moments for Game Cards (5-7 specific, vivid moments)

Format your response EXACTLY like this:

---
Your Life Story Game

Title: [Poetic 5-word title]

Story Essence: [1-2 sentence reason statement]

Chapters:
1. [First chapter title] - [1 sentence description]
2. [Second chapter title] - [1 sentence description]
3. [Third chapter title] - [1 sentence description]
[4-5 if needed]

Key Moments for Game Cards:
- [Moment 1]: [Brief description of the scene/event]
- [Moment 2]: [Brief description]
- [Moment 3]: [Brief description]
- [Moment 4]: [Brief description]
- [Moment 5]: [Brief description]
[6-7 if available]

---

Rules:
- Reflect their actual words and experiences
- Make it emotionally resonant
- Ensure "Key Moments" are specific enough to be illustrated on a card
- DO NOT output anything else (no intro/outro text)""",
    },
}


class ConversationState:
    """Class to manage the state of a conversation in the chatbot application.

    Attributes:
        messages (list): A list to store the messages exchanged in the conversation.

    """

    def __init__(self):
        self.phase = "GREETING"
        self.question_count = 0
        self.messages: List[Dict[str, str]] = []
        self.selected_route: Optional[str] = None  # Stores route number (1-7)
        self.custom_route_description: Optional[str] = None  # For route 7
        self.phase_order = [
            "GREETING",
            "ROUTE_SELECTION",
            "QUESTION_1",
            "QUESTION_2",
            "QUESTION_3",
            "QUESTION_4",
            "QUESTION_5",
            "QUESTION_6",
            "SYNTHESIS",
        ]

    def get_current_phase(self):
        """Returns the current phase of the conversation."""
        return INTERVIEW_PHASES[self.phase]

    def should_advance(self, user_message: str) -> bool:
        """
        Decide whether the conversation state machine should advance to the next phase based on the user's message.
        Behavior:
        - When self.phase == "GREETING": treat short affirmative responses as intent to proceed.
            - Checks for presence of common affirmative tokens (e.g. "yes", "yeah", "sure", "ready", "ok", "let's go", "sim", "vamos")
            - Comparison is case-insensitive and uses substring membership, so tokens may match as substrings of the input.
        - When self.phase == "ROUTE_SELECTION": validate and store route selection (1-7)
            - For routes 1-6: store route and advance
            - For route 7: if route not yet set, store route but don't advance (need description)
            - For route 7: if route already set to "7", store description and advance
        - When "QUESTION" is in self.phase: consider the user to have given a substantial answer when the trimmed message length exceeds 20 characters.
        - For any other phase values, the function returns False (no advancement).
        Parameters:
        - user_message (str): The raw message text provided by the user.
        Returns:
        - bool: True if the conversation should advance to the next phase according to the above rules; otherwise False.
        Notes:
        - The checks are intentionally simple heuristics and may be refined to use more robust NLP or pattern matching if needed.
        - Leading/trailing whitespace is ignored for the length check in QUESTION phases.
        """

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

        # Route selection logic
        if self.phase == "ROUTE_SELECTION":
            message_clean = user_message.strip()

            # Check if user entered a route number
            if message_clean in ["1", "2", "3", "4", "5", "6"]:
                self.selected_route = message_clean
                return True

            # Handle route 7 (custom route)
            if message_clean == "7":
                if self.selected_route is None:
                    self.selected_route = "7"
                    return False  # Don't advance yet, need description
                return False

            # If route 7 already selected, next message is the description
            if self.selected_route == "7" and len(message_clean) > 10:
                self.custom_route_description = message_clean
                return True

            return False

        # After each question, advance when user provides any non-empty answer
        if "QUESTION" in self.phase:
            return len(user_message.strip()) > 0

        return False

    def advance_phase(self):
        """Move to next phase"""
        current_index = self.phase_order.index(self.phase)

        if current_index < len(self.phase_order) - 1:
            self.phase = self.phase_order[current_index + 1]
            if "QUESTION" in self.phase:
                self.question_count += 1

        return self.phase

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        self.messages.append({"role": role, "content": content})

    def get_route_info(self) -> Optional[Dict[str, str]]:
        """Get information about the selected route"""
        if self.selected_route and self.selected_route in STORY_ROUTES:
            return STORY_ROUTES[self.selected_route]
        elif self.selected_route == "7":
            return {
                "name": "Personal Route",
                "persona": "Custom approach",
                "goal": "Follow user's preferred method",
                "prompt_focus": self.custom_route_description
                or "Custom storytelling approach",
            }
        return None

    def get_route_adapted_instruction(self, base_instruction: str) -> str:
        """Adapt question instructions based on selected route"""
        route_info = self.get_route_info()
        if not route_info:
            return base_instruction

        # Add route context to instruction
        route_context = f"""
SELECTED ROUTE: {route_info['name']}
Route Focus: {route_info['goal']}
User Persona: {route_info['persona']}

Adapt your questioning style to match this route's approach while maintaining the core question objective.
"""
        return route_context + "\n" + base_instruction
