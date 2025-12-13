from typing import List, Optional

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
    advance_phase: Optional[bool] = False


class ChatResponse(BaseModel):
    id: int
    role: str
    content: str
    phase: str
    phase_order: List[str]
    phase_index: int
    age_range: Optional[str]
    phase_description: str


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

    Response includes phase metadata for frontend phase tracking:
    - phase: Current phase name
    - phase_order: List of phases for this user's age range
    - phase_index: Current position in phase_order
    - age_range: User's selected age range (if set)
    - phase_description: Human-readable phase description
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
        ai_message, phase_metadata = service.process_chat(
            story_id, request.message, advance_phase=request.advance_phase or False
        )

        return {
            "id": ai_message.id,
            "role": ai_message.role,
            "content": ai_message.content,
            "phase": phase_metadata["phase"],
            "phase_order": phase_metadata["phase_order"],
            "phase_index": phase_metadata["phase_index"],
            "age_range": phase_metadata["age_range"],
            "phase_description": phase_metadata["phase_description"],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
        raise HTTPException(status_code=500, detail="Internal Server Error")
