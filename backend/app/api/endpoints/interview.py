from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.story import Story
from backend.app.models.user import User
from backend.app.services.interview import InterviewService

router = APIRouter()


# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    id: int
    role: str
    content: str
    phase: str


# --- Endpoints ---


@router.post("/{story_id}", response_model=ChatResponse)
def chat_with_agent(
    story_id: int,
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI interviewer for a specific story.

    Requires authentication. User must own the story.
    """
    # Verify story exists and user owns it
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
        )

    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    service = InterviewService(db)
    try:
        # Process the chat (Save User -> Think -> Save AI)
        ai_message = service.process_chat(story_id, request.message)

        return {
            "id": ai_message.id,
            "role": ai_message.role,
            "content": ai_message.content,
            "phase": ai_message.phase_context or "UNKNOWN",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
