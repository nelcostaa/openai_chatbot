"""
Snippet generation endpoints for creating story game cards.

POST /api/snippets/{story_id} - Generate snippets for a story
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.story import Story
from backend.app.models.user import User
from backend.app.services.snippets import SnippetService

router = APIRouter()


# --- Pydantic Models ---


class SnippetItem(BaseModel):
    """Individual snippet for a game card."""

    title: str
    content: str
    phase: str
    theme: str


class SnippetsResponse(BaseModel):
    """Response from snippet generation."""

    success: bool
    snippets: List[SnippetItem]
    count: int
    model: Optional[str] = None
    error: Optional[str] = None


# --- Endpoints ---


@router.post("/{story_id}", response_model=SnippetsResponse)
def generate_snippets(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate story snippets (game cards) for a specific story.

    This endpoint fetches all messages from the story, sends them to
    Gemini for analysis, and returns 3-8 snippets (max 300 chars each)
    suitable for printing on game cards.

    Requires authentication. User must own the story.

    Args:
        story_id: ID of the story to generate snippets for
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        SnippetsResponse with generated snippets
    """
    # Verify story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found",
        )

    # Verify user owns the story
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    # Generate snippets
    service = SnippetService(db)

    try:
        result = service.generate_snippets(story_id)

        if not result["success"]:
            # Return the error in the response body, not as HTTP error
            # This allows frontend to show a friendly message
            return SnippetsResponse(
                success=False,
                snippets=[],
                count=0,
                model=result.get("model"),
                error=result.get("error", "Failed to generate snippets"),
            )

        return SnippetsResponse(
            success=True,
            snippets=[SnippetItem(**snippet) for snippet in result["snippets"]],
            count=result["count"],
            model=result.get("model"),
            error=None,
        )

    except Exception as e:
        print(f"[Snippets] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during snippet generation",
        )
