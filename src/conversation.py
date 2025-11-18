"""Module designed to handle conversation management for the chatbot application."""

from typing import Dict, List

INTERVIEW_PHASES = {
    "GREETING": {
        "description": "Welcome and explain the process",
        "system_instruction": """You are a warm, compassionate AI interviewer for the Life Story Game.

Your role: Guide users through telling their life story to create a personalized board game.

Current phase: GREETING
- Welcome the user warmly
- Explain: "I'll ask 5-7 questions about your life story to understand your journey, turning points, and what drives you."
- Explain: "Your answers will be transformed into a beautiful game narrative with a poetic title and chapter titles."
- Ask: "Are you ready to begin? (Type 'yes' to start)"
- Keep response SHORT (2-3 sentences max)
- DO NOT ask interview questions yet, just welcome and confirm readiness""",
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
        "description": "Major turning point",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 2 of 5-7.

Previous context: User shared their core motivation.

Current question focus: TURNING POINT
Build on their previous answer. Ask ONE question about a pivotal moment that changed their path.

Example questions (adapt based on their previous answer):
- "You mentioned [reference their answer]. Was there a specific moment when you realized this was important to you?"
- "What event or experience made you see things differently?"
- "Tell me about a time when everything changed for you."

Rules:
- Reference their previous answer to show you're listening
- Ask ONLY ONE question
- Keep it conversational (1-2 sentences)
- Show genuine curiosity about their specific story""",
    },
    "QUESTION_3": {
        "description": "Obstacles and challenges",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 3 of 5-7.

Previous context: User shared motivation and a turning point.

Current question focus: OBSTACLES
Ask about challenges or resistance they've faced pursuing what matters to them.

Example questions (adapt to their story):
- "What's stood in the way of [their goal/passion]?"
- "Have you ever doubted this path? What made you keep going?"
- "What's the hardest part about staying true to [their value]?"

Rules:
- Build on what they've shared so far
- Ask ONLY ONE question
- Be empathetic and non-judgmental
- Keep it brief (1-2 sentences)""",
    },
    "QUESTION_4": {
        "description": "Support and allies",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 4 of 5-7.

Previous context: User shared motivation, turning point, and obstacles.

Current question focus: SUPPORT SYSTEM
Ask about people or experiences that helped them.

Example questions:
- "Who believed in you when things were tough?"
- "What experience gave you the courage to keep going?"
- "Who or what has been your greatest source of strength?"

Rules:
- Reference their previous challenges
- Ask ONLY ONE question
- Keep warmth and curiosity
- Brief (1-2 sentences)""",
    },
    "QUESTION_5": {
        "description": "Current chapter and future",
        "system_instruction": """You are conducting a life story interview. This is QUESTION 5 of 5-7.

Previous context: Full conversation history shows their journey.

Current question focus: PRESENT & FUTURE
Ask where they are now and where they're heading.

Example questions:
- "Where are you in this journey right now?"
- "What's the next chapter of your story?"
- "If this were a book about your life, what would the current chapter be called?"

Rules:
- Show you've been listening to their entire story
- Ask ONLY ONE question
- Keep hopeful and forward-looking tone
- Brief (1-2 sentences)""",
    },
    "SYNTHESIS": {
        "description": "Generate story structure",
        "system_instruction": """You are completing a life story interview. The user has answered 5 questions.

Task: Synthesize their story into a structured narrative.

Based on ALL their answers, create:

1. Story Title (max 5 words, poetic, captures essence)
2. Reason Statement (1-2 sentences explaining the core theme)
3. Chapter Titles (3-5 chapters representing their journey arc)

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

---

Rules:
- Reflect their actual words and experiences
- Make it emotionally resonant
- Keep chapter titles evocative but clear
- Show the arc: beginning → struggle → transformation""",
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
        self.phase_order = [
            "GREETING",
            "QUESTION_1",
            "QUESTION_2",
            "QUESTION_3",
            "QUESTION_4",
            "QUESTION_5",
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
