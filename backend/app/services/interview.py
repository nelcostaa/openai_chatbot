from typing import Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from backend.app.core.agent import agent_app
from backend.app.db.base import Base  # Ensure all models are registered
from backend.app.models.message import Message
from backend.app.models.story import Story


# Age range to phase mapping - determines which life stages to include
AGE_PHASE_MAPPING: Dict[str, List[str]] = {
    "under_18": [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "PRESENT",
        "SYNTHESIS",
    ],
    "18_30": [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "EARLY_ADULTHOOD",
        "PRESENT",
        "SYNTHESIS",
    ],
    "31_45": [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "EARLY_ADULTHOOD",
        "MIDLIFE",
        "PRESENT",
        "SYNTHESIS",
    ],
    "46_60": [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "EARLY_ADULTHOOD",
        "MIDLIFE",
        "PRESENT",
        "SYNTHESIS",
    ],
    "61_plus": [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "EARLY_ADULTHOOD",
        "MIDLIFE",
        "PRESENT",
        "SYNTHESIS",
    ],
}

# Full phase prompts with descriptions
PHASE_CONFIG: Dict[str, Dict[str, str]] = {
    "GREETING": {
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
    "FAMILY_HISTORY": {
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
    "CHILDHOOD": {
        "description": "Ages 0-12",
        "prompt": """You are conducting a chronological life story interview. Phase: CHILDHOOD (Ages 0-12)

Your goal: Explore earliest memories and foundational years.

If this is the FIRST message in this phase:
- Acknowledge transition: "Thank you for sharing about your family. Now let's explore YOUR CHILDHOOD."
- Ask about early memories: "What are your earliest significant memories?"

If they've shared childhood memories:
- Ask follow-ups: specific moments, relationships, places, emotions
- Examples: "Tell me more about [specific thing they mentioned]" or "How did that shape you?"

Keep it conversational (1-2 sentences).""",
    },
    "ADOLESCENCE": {
        "description": "Ages 13-18",
        "prompt": """You are conducting a chronological life story interview. Phase: ADOLESCENCE (Ages 13-18)

Your goal: Explore teenage years - friendships, challenges, identity formation.

If this is the FIRST message in this phase:
- Acknowledge: "Great! We've explored your childhood. Now let's talk about your ADOLESCENCE."
- Ask about teenage years: "What was significant about your teenage years?"

If they've shared adolescent memories:
- Ask follow-ups about friendships, school, identity, struggles, discoveries

Keep it conversational (1-2 sentences).""",
    },
    "EARLY_ADULTHOOD": {
        "description": "Ages 19-35",
        "prompt": """You are conducting a chronological life story interview. Phase: EARLY ADULTHOOD (Ages 19-35)

Your goal: Explore decisions, relationships, career, identity formation during this pivotal phase.

If this is the FIRST message in this phase:
- Acknowledge: "Excellent! Now let's explore your EARLY ADULTHOOD."
- Ask: "What major choices did you make in your 20s and 30s?"

If they've shared early adulthood experiences:
- Ask follow-ups about career, relationships, challenges, achievements

Keep it conversational (1-2 sentences).""",
    },
    "MIDLIFE": {
        "description": "Ages 36-60",
        "prompt": """You are conducting a chronological life story interview. Phase: MIDLIFE (Ages 36-60)

Your goal: Explore middle years - achievements, challenges, growth, wisdom gained.

If this is the FIRST message in this phase:
- Acknowledge: "Wonderful! Now let's talk about your MIDLIFE years."
- Ask: "What were the defining moments of your middle years?"

If they've shared midlife experiences:
- Ask follow-ups about growth, lessons learned, significant changes

Keep it conversational (1-2 sentences).""",
    },
    "PRESENT": {
        "description": "Current life",
        "prompt": """You are conducting a chronological life story interview. Phase: PRESENT DAY

Your goal: Explore where they are now and how they see their journey.

If this is the FIRST message in this phase:
- Acknowledge: "Thank you for sharing that. Now let's focus on PRESENT DAY."
- Ask: "Where are you now in your life? How do you feel about the journey you've taken?"

If they've shared about present:
- Ask about meaning, purpose, hopes, reflections

Keep it conversational (1-2 sentences).""",
    },
    "SYNTHESIS": {
        "description": "Story summary",
        "prompt": """You are completing a chronological life story interview.

STOP INTERVIEWING. Create a synthesis of their story:

1. Story Title (max 5 words, poetic)
2. Story Essence (1-2 sentences capturing core narrative)
3. Timeline Chapters (5 chapters following their journey)
4. Key Story Moments (5-7 specific, vivid moments)

Format exactly like this:
---
Your Life Story

Title: [Poetic 5-word title]

Story Essence: [1-2 sentence core narrative]

Timeline:
1. [Chapter title] - [Brief description]
2. [Chapter title] - [Brief description]
...

Key Moments:
- [Moment]: [Brief vivid description]
...
---

Make it emotionally resonant. Capture their authentic voice.""",
    },
}


class InterviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_phase_order(self, age_range: Optional[str]) -> List[str]:
        """Get the phase order for a given age range."""
        if age_range and age_range in AGE_PHASE_MAPPING:
            return AGE_PHASE_MAPPING[age_range]
        # Default to full phases if age not set
        return AGE_PHASE_MAPPING["61_plus"]

    def get_phase_index(self, phase: str, phase_order: List[str]) -> int:
        """Get the index of a phase in the phase order."""
        try:
            return phase_order.index(phase)
        except ValueError:
            return 0

    def detect_age_selection(self, message: str) -> Optional[str]:
        """Detect if user selected an age range via button or message."""
        # Check for button marker
        if "[Age selected via button:" in message:
            # Extract age range from marker like "[Age selected via button: 31_45]"
            import re
            match = re.search(r'\[Age selected via button: ([^\]]+)\]', message)
            if match:
                return match.group(1)
        
        # Check for direct number input (1-5)
        clean = message.strip()
        age_map = {
            "1": "under_18",
            "2": "18_30",
            "3": "31_45",
            "4": "46_60",
            "5": "61_plus",
        }
        if clean in age_map:
            return age_map[clean]
        
        return None

    def detect_phase_advance(self, message: str) -> Optional[str]:
        """Detect if user wants to advance to next phase."""
        # Check for explicit marker
        if "[Moving to next phase:" in message:
            import re
            match = re.search(r'\[Moving to next phase: ([^\]]+)\]', message)
            if match:
                return match.group(1)
        return None

    def advance_to_next_phase(self, story: Story) -> str:
        """Advance story to next phase and return new phase name."""
        phase_order = self.get_phase_order(story.age_range)
        current_idx = self.get_phase_index(story.current_phase, phase_order)
        
        if current_idx < len(phase_order) - 1:
            new_phase = phase_order[current_idx + 1]
            story.current_phase = new_phase
            self.db.commit()
            return new_phase
        
        return story.current_phase

    def process_chat(
        self, 
        story_id: int, 
        user_content: str,
        advance_phase: bool = False
    ) -> Tuple[Message, Dict]:
        """
        Orchestrates the chat flow:
        1. Load Story & History
        2. Handle phase transitions (age selection, next chapter)
        3. Save User Message
        4. Run AI Agent
        5. Save AI Response
        6. Return response with phase metadata
        """
        # 1. Fetch Story Context
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        # 2. Handle age selection
        detected_age = self.detect_age_selection(user_content)
        if detected_age and not story.age_range:
            story.age_range = detected_age
            # Move from GREETING to first interview phase (FAMILY_HISTORY)
            phase_order = self.get_phase_order(detected_age)
            story.current_phase = phase_order[0]  # FAMILY_HISTORY
            self.db.commit()

        # 3. Handle explicit phase advance
        target_phase = self.detect_phase_advance(user_content)
        if target_phase or advance_phase:
            self.advance_to_next_phase(story)

        # 4. Save User Message to DB
        user_msg_db = Message(
            story_id=story.id,
            role="user",
            content=user_content,
            phase_context=story.current_phase,
        )
        self.db.add(user_msg_db)
        self.db.commit()

        # 5. Load History for Context
        history_records = (
            self.db.query(Message)
            .filter(Message.story_id == story.id)
            .order_by(Message.created_at.asc())
            .limit(20)
            .all()
        )

        # Convert DB models to LangChain message format
        lc_messages = []
        for msg in history_records:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        # 6. Determine System Prompt based on Story Phase
        phase_config = PHASE_CONFIG.get(story.current_phase, PHASE_CONFIG["GREETING"])
        current_instruction = phase_config["prompt"]

        # 7. Invoke LangGraph Agent
        result = agent_app.invoke(
            {"messages": lc_messages, "phase_instruction": current_instruction}
        )

        # Extract the AI's response content
        ai_response_content = result["messages"][-1].content

        # 8. Save AI Response to DB
        ai_msg_db = Message(
            story_id=story.id,
            role="assistant",
            content=ai_response_content,
            phase_context=story.current_phase,
        )
        self.db.add(ai_msg_db)
        self.db.commit()
        self.db.refresh(ai_msg_db)

        # 9. Build phase metadata for frontend
        phase_order = self.get_phase_order(story.age_range)
        phase_index = self.get_phase_index(story.current_phase, phase_order)
        
        phase_metadata = {
            "phase": story.current_phase,
            "phase_order": phase_order,
            "phase_index": phase_index,
            "age_range": story.age_range,
            "phase_description": phase_config.get("description", ""),
        }

        return ai_msg_db, phase_metadata
