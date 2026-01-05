"""
Snippet endpoints for story game cards.

GET /api/snippets/{story_id} - Get existing snippets for a story (cached)
POST /api/snippets/{story_id} - Generate/regenerate snippets for a story
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_active_user
from backend.app.db.session import get_db
from backend.app.models.snippets import Snippet
from backend.app.models.story import Story
from backend.app.models.user import User
from backend.app.services.snippets import SnippetService

router = APIRouter()


# --- Pydantic Models ---


class SnippetItem(BaseModel):
    """Individual snippet for a game card."""

    id: Optional[int] = None
    title: str
    content: str
    phase: Optional[str] = None
    theme: Optional[str] = None
    is_locked: bool = False
    is_active: bool = True
    display_order: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SnippetsResponse(BaseModel):
    """Response from snippet operations."""

    success: bool
    snippets: List[SnippetItem]
    count: int
    cached: Optional[bool] = None  # True if from database, False if freshly generated
    locked_count: Optional[int] = None  # Number of locked snippets
    model: Optional[str] = None
    error: Optional[str] = None


class ArchivedSnippetsResponse(BaseModel):
    """Response for archived snippets."""

    success: bool
    snippets: List[SnippetItem]
    count: int
    error: Optional[str] = None


class SnippetUpdate(BaseModel):
    """Request body for updating a snippet."""

    title: Optional[str] = None
    content: Optional[str] = None
    theme: Optional[str] = None
    phase: Optional[str] = None


class ReorderRequest(BaseModel):
    """Request body for reordering snippets."""

    snippet_ids: List[int]  # Ordered list of snippet IDs


class ReorderResponse(BaseModel):
    """Response from reorder operation."""

    success: bool
    message: str


# --- Endpoints ---


@router.get("/{story_id}", response_model=SnippetsResponse)
def get_snippets(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get existing snippets for a story from the database.

    Use this endpoint to check if snippets already exist before regenerating.
    If snippets exist, they will be returned with cached=True.
    If no snippets exist, returns empty array with cached=False.

    Requires authentication. User must own the story.

    Args:
        story_id: ID of the story
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        SnippetsResponse with cached snippets
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

    # Get existing snippets
    service = SnippetService(db)
    result = service.get_existing_snippets(story_id)
    locked_count = service.get_locked_snippet_count(story_id)

    return SnippetsResponse(
        success=True,
        snippets=[SnippetItem(**s) for s in result["snippets"]],
        count=result["count"],
        cached=result["cached"],
        locked_count=locked_count,
        error=None,
    )


@router.post("/{story_id}", response_model=SnippetsResponse)
def generate_snippets(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate/regenerate story snippets (game cards) for a specific story.

    This endpoint:
    1. Deletes any existing snippets for the story
    2. Fetches all messages from the story
    3. Sends them to Gemini for analysis
    4. Saves and returns 3-8 snippets (max 300 chars each)

    Use GET /api/snippets/{story_id} to check for existing snippets first.

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
    print(
        f"[API] POST /api/snippets/{story_id} - Generating snippets for story {story_id}"
    )
    service = SnippetService(db)

    try:
        result = service.generate_snippets(story_id)
        print(
            f"[API] Service returned: success={result.get('success')}, model={result.get('model')}"
        )

        if not result["success"]:
            # Return the error in the response body, not as HTTP error
            # This allows frontend to show a friendly message
            print(f"[API] Generation failed: {result.get('error')}")
            return SnippetsResponse(
                success=False,
                snippets=[],
                count=0,
                cached=False,
                model=result.get("model"),
                error=result.get("error", "Failed to generate snippets"),
            )

        print(f"[API] ✅ Success! Generated {result['count']} snippets")
        return SnippetsResponse(
            success=True,
            snippets=[SnippetItem(**snippet) for snippet in result["snippets"]],
            count=result["count"],
            cached=False,  # Freshly generated
            model=result.get("model"),
            error=None,
        )

    except Exception as e:
        print(f"[API] ❌ Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during snippet generation",
        )


@router.put("/{snippet_id}", response_model=SnippetItem)
def update_snippet(
    snippet_id: int,
    snippet_data: SnippetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update an individual snippet's title, content, theme, or phase.

    This endpoint allows users to edit their snippet cards after generation.
    Only the owner of the snippet (via story ownership) can update it.

    Args:
        snippet_id: ID of the snippet to update
        snippet_data: Fields to update (all optional)
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        Updated SnippetItem

    Raises:
        HTTPException 404: Snippet not found
        HTTPException 403: Not authorized (not owner)
    """
    # Find the snippet
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snippet not found",
        )

    # Verify user owns the snippet (via story ownership)
    story = db.query(Story).filter(Story.id == snippet.story_id).first()
    if not story or story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this snippet",
        )

    # Update fields if provided
    if snippet_data.title is not None:
        snippet.title = snippet_data.title[:200]  # Enforce max length
    if snippet_data.content is not None:
        snippet.content = snippet_data.content[:300]  # Enforce 300 char limit
    if snippet_data.theme is not None:
        snippet.theme = snippet_data.theme
    if snippet_data.phase is not None:
        snippet.phase = snippet_data.phase

    db.commit()
    db.refresh(snippet)

    print(f"[API] ✅ Updated snippet {snippet_id}: title='{snippet.title[:30]}...'")

    return SnippetItem(
        id=snippet.id,
        title=snippet.title,
        content=snippet.content,
        phase=snippet.phase,
        theme=snippet.theme,
        is_locked=snippet.is_locked,
        is_active=snippet.is_active,
        created_at=snippet.created_at,
    )


@router.patch("/{snippet_id}/lock", response_model=SnippetItem)
def toggle_snippet_lock(
    snippet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Toggle the lock status of a snippet.

    Locked snippets are protected during regeneration - they won't be
    deleted when new snippets are generated.

    Args:
        snippet_id: ID of the snippet to lock/unlock
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        Updated SnippetItem with new lock status

    Raises:
        HTTPException 404: Snippet not found
        HTTPException 403: Not authorized (not owner)
    """
    # Find the snippet
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snippet not found",
        )

    # Verify user owns the snippet (via story ownership)
    story = db.query(Story).filter(Story.id == snippet.story_id).first()
    if not story or story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this snippet",
        )

    # Toggle lock
    service = SnippetService(db)
    result = service.toggle_lock(snippet_id)

    action = "locked" if result["is_locked"] else "unlocked"
    print(f"[API] ✅ {action.capitalize()} snippet {snippet_id}")

    return SnippetItem(**result)


@router.get("/{story_id}/archived", response_model=ArchivedSnippetsResponse)
def get_archived_snippets(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get archived (soft-deleted) snippets for a story.

    Archived snippets can be restored using POST /api/snippets/{snippet_id}/restore.

    Args:
        story_id: ID of the story
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        ArchivedSnippetsResponse with archived snippets
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

    service = SnippetService(db)
    result = service.get_archived_snippets(story_id)

    return ArchivedSnippetsResponse(
        success=True,
        snippets=[SnippetItem(**s) for s in result["snippets"]],
        count=result["count"],
        error=None,
    )


@router.post("/{snippet_id}/restore", response_model=SnippetItem)
def restore_snippet(
    snippet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Restore an archived (soft-deleted) snippet.

    Args:
        snippet_id: ID of the snippet to restore
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        Restored SnippetItem

    Raises:
        HTTPException 404: Snippet not found
        HTTPException 403: Not authorized (not owner)
    """
    # Find the snippet
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snippet not found",
        )

    # Verify user owns the snippet (via story ownership)
    story = db.query(Story).filter(Story.id == snippet.story_id).first()
    if not story or story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to restore this snippet",
        )

    service = SnippetService(db)
    result = service.restore_snippet(snippet_id)

    print(f"[API] ✅ Restored snippet {snippet_id}")

    return SnippetItem(**result)


@router.delete("/{snippet_id}", response_model=SnippetItem)
def delete_snippet(
    snippet_id: int,
    permanent: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a snippet (soft-delete by default, or permanent with ?permanent=true).

    Soft-deleted snippets can be restored from the archived view.
    Permanent deletion cannot be undone.

    Args:
        snippet_id: ID of the snippet to delete
        permanent: If True, permanently delete instead of soft-delete
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        Deleted SnippetItem (for soft-delete) or success message

    Raises:
        HTTPException 404: Snippet not found
        HTTPException 403: Not authorized (not owner)
    """
    # Find the snippet
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id).first()
    if not snippet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snippet not found",
        )

    # Verify user owns the snippet (via story ownership)
    story = db.query(Story).filter(Story.id == snippet.story_id).first()
    if not story or story.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this snippet",
        )

    service = SnippetService(db)

    if permanent:
        # Return snippet data before permanent deletion
        snippet_data = snippet.to_dict()
        service.permanently_delete_snippet(snippet_id)
        print(f"[API] ✅ Permanently deleted snippet {snippet_id}")
        return SnippetItem(**snippet_data)
    else:
        result = service.soft_delete_snippet(snippet_id)
        print(f"[API] ✅ Soft-deleted (archived) snippet {snippet_id}")
        return SnippetItem(**result)


@router.put("/{story_id}/reorder", response_model=ReorderResponse)
def reorder_snippets(
    story_id: int,
    reorder_data: ReorderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Reorder snippets for a story.

    Accepts an ordered list of snippet IDs and updates their display_order
    to match the new order.

    Args:
        story_id: ID of the story
        reorder_data: List of snippet IDs in desired order
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        ReorderResponse with success status
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
            detail="Not authorized to modify this story",
        )

    # Update display_order for each snippet
    for order, snippet_id in enumerate(reorder_data.snippet_ids):
        snippet = (
            db.query(Snippet)
            .filter(
                Snippet.id == snippet_id,
                Snippet.story_id == story_id,
                Snippet.is_active == True,
            )
            .first()
        )
        if snippet:
            snippet.display_order = order

    db.commit()
    print(
        f"[API] ✅ Reordered {len(reorder_data.snippet_ids)} snippets for story {story_id}"
    )

    return ReorderResponse(
        success=True,
        message=f"Reordered {len(reorder_data.snippet_ids)} snippets",
    )
