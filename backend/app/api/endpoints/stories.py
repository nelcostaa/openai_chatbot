"""
Story management endpoints for creating and managing user stories.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.message import Message
from backend.app.models.story import Story
from backend.app.models.user import User

router = APIRouter()


# --- Pydantic Models ---


class StoryCreate(BaseModel):
    """Story creation request."""

    title: Optional[str] = "My Life Story"
    route_type: str = "1"  # Default to Chronological Steward
    age_range: Optional[str] = None


class StoryUpdate(BaseModel):
    """Story update request."""

    title: Optional[str] = None
    current_phase: Optional[str] = None
    age_range: Optional[str] = None
    status: Optional[str] = None
    chapter_names: Optional[Dict[str, str]] = None


class ChapterNamesUpdate(BaseModel):
    """Chapter names update request (visual only)."""

    chapter_names: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom display names for chapters. Keys are phase IDs (e.g., 'CHILDHOOD'), values are custom labels."
    )


class StoryResponse(BaseModel):
    """Story response."""

    id: int
    user_id: int
    title: str
    route_type: str
    current_phase: str
    age_range: Optional[str]
    status: str
    chapter_names: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message response."""

    id: int
    story_id: int
    role: str
    content: str
    phase_context: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Endpoints ---


@router.post("/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(
    story_data: StoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new story for the authenticated user.

    Args:
        story_data: Story creation data
        current_user: Authenticated user
        db: Database session

    Returns:
        Newly created story
    """
    new_story = Story(
        user_id=current_user.id,
        title=story_data.title,
        route_type=story_data.route_type,
        current_phase="GREETING",  # Start at greeting phase
        age_range=story_data.age_range,
        status="active",
    )

    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    return new_story


@router.get("/", response_model=List[StoryResponse])
def list_stories(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    List all stories for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List of user's stories
    """
    stories = db.query(Story).filter(Story.user_id == current_user.id).all()
    return stories


@router.get("/{story_id}", response_model=StoryResponse)
def get_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific story by ID.

    Args:
        story_id: Story ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Story details

    Raises:
        HTTPException: If story not found or not owned by user
    """
    story = db.query(Story).filter(Story.id == story_id).first()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
        )

    # Ensure user owns the story
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    return story


@router.put("/{story_id}", response_model=StoryResponse)
def update_story(
    story_id: int,
    story_data: StoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update a story's metadata.

    Args:
        story_id: Story ID
        story_data: Story update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated story

    Raises:
        HTTPException: If story not found or not owned by user
    """
    story = db.query(Story).filter(Story.id == story_id).first()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
        )

    # Ensure user owns the story
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    # Update fields
    if story_data.title is not None:
        story.title = story_data.title
    if story_data.current_phase is not None:
        story.current_phase = story_data.current_phase
    if story_data.age_range is not None:
        story.age_range = story_data.age_range
    if story_data.status is not None:
        story.status = story_data.status
    if story_data.chapter_names is not None:
        story.chapter_names = story_data.chapter_names

    db.commit()
    db.refresh(story)

    return story


@router.put("/{story_id}/chapter-names", response_model=StoryResponse)
def update_chapter_names(
    story_id: int,
    data: ChapterNamesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update custom chapter display names for a story.

    This is a visual-only change - the underlying AI prompts remain unchanged.
    Chapter names are stored as a JSON object mapping phase IDs to custom labels.

    Args:
        story_id: Story ID
        data: Chapter names update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated story with new chapter names

    Raises:
        HTTPException: If story not found or not owned by user
    """
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

    story.chapter_names = data.chapter_names
    db.commit()
    db.refresh(story)

    return story


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a story.

    Args:
        story_id: Story ID
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If story not found or not owned by user
    """
    story = db.query(Story).filter(Story.id == story_id).first()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
        )

    # Ensure user owns the story
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    db.delete(story)
    db.commit()

    return None


@router.get("/{story_id}/messages", response_model=List[MessageResponse])
def get_story_messages(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all messages for a story.

    Args:
        story_id: Story ID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of messages for the story

    Raises:
        HTTPException: If story not found or not owned by user
    """
    story = db.query(Story).filter(Story.id == story_id).first()

    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
        )

    # Ensure user owns the story
    if story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this story",
        )

    # Fetch messages for this story, ordered by creation time
    messages = (
        db.query(Message)
        .filter(Message.story_id == story_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return messages
