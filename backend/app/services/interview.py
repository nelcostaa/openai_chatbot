from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from backend.app.core.agent import agent_app
from backend.app.db.base import Base  # Ensure all models are registered
from backend.app.models.message import Message
from backend.app.models.story import Story

# Hardcoded phases for now - eventually this comes from a Config or DB
PHASE_PROMPTS = {
    "GREETING": "You are a warm, empathetic interviewer. Welcome the user to their life story journey. Keep it short and ask if they are ready to begin.",
    "CHILDHOOD": "You are asking about childhood memories. Ask one specific, evocative question about their early home life, parents, or favorite toys.",
    "ADOLESCENCE": "You are exploring the teenage years. Ask about school, friends, or early identity formation.",
}


class InterviewService:
    def __init__(self, db: Session):
        self.db = db

    def process_chat(self, story_id: int, user_content: str):
        """
        Orchestrates the chat flow:
        1. Load Story & History
        2. Save User Message
        3. Run AI Agent
        4. Save AI Response
        """
        # 1. Fetch Story Context
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story with ID {story_id} not found")

        # 2. Save User Message to DB
        user_msg_db = Message(
            story_id=story.id,
            role="user",
            content=user_content,
            phase_context=story.current_phase,
        )
        self.db.add(user_msg_db)
        self.db.commit()  # Commit immediately to ensure persistence

        # 3. Load History for Context
        # Fetch last 10 messages to keep context window manageable
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

        # 4. Determine System Prompt based on Story Phase
        current_instruction = PHASE_PROMPTS.get(
            story.current_phase, PHASE_PROMPTS["GREETING"]
        )

        # 5. Invoke LangGraph Agent
        # Note: We are using .invoke() (synchronous) for this step.
        # In the next optimization slice, we can switch to .astream() for typing effects.
        result = agent_app.invoke(
            {"messages": lc_messages, "phase_instruction": current_instruction}
        )

        # Extract the AI's response content
        ai_response_content = result["messages"][-1].content

        # 6. Save AI Response to DB
        ai_msg_db = Message(
            story_id=story.id,
            role="assistant",
            content=ai_response_content,
            phase_context=story.current_phase,
        )
        self.db.add(ai_msg_db)
        self.db.commit()
        self.db.refresh(ai_msg_db)

        return ai_msg_db
