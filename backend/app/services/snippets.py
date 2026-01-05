"""
Snippet generation service for creating story game cards.

This service fetches all messages from a story and uses Gemini to generate
short, impactful snippets (max 300 characters) suitable for printing on cards.

Snippets are persisted to the database and can be retrieved later without
regeneration. Use get_existing_snippets() to check for cached snippets before
regenerating.
"""

import json
import os
from typing import Dict, List, Optional, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr
from sqlalchemy.orm import Session

from backend.app.models.message import Message
from backend.app.models.snippets import Snippet
from backend.app.models.story import Story


def get_model_cascade() -> List[str]:
    """Get model fallback cascade from environment or return defaults."""
    env_models = os.getenv("GEMINI_MODELS")
    if env_models:
        return [m.strip() for m in env_models.split(",") if m.strip()]

    return [
        "gemma-3-12b-it",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-lite",
    ]


class SnippetService:
    """
    Service for generating and persisting story snippets (game cards).

    Uses Gemini to analyze the story and create 3-8 short, impactful snippets
    suitable for printing on game cards. Snippets are saved to the database
    for later retrieval.
    """

    def __init__(self, db: Session):
        self.db = db
        api_key_str = os.getenv("GEMINI_API_KEY")
        if not api_key_str:
            raise ValueError("GEMINI_API_KEY not set in environment")
        self.api_key = SecretStr(api_key_str)

    def get_story_messages(self, story_id: int) -> List[Dict[str, Optional[str]]]:
        """
        Fetch all messages for a story.

        Returns list of dicts with 'role', 'content', and 'phase_context' keys.
        phase_context is the chapter the message was collected in.
        """
        messages = (
            self.db.query(Message)
            .filter(Message.story_id == story_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        return [
            {
                "role": str(msg.role),
                "content": str(msg.content),
                "phase_context": str(msg.phase_context) if msg.phase_context else None,
            }
            for msg in messages
        ]

    def get_existing_snippets(
        self, story_id: int, include_archived: bool = False
    ) -> Dict:
        """
        Get existing snippets for a story from the database.

        Args:
            story_id: ID of the story
            include_archived: If True, include soft-deleted snippets (is_active=False)

        Returns:
            Dict with keys:
                - success (bool): True
                - snippets (list): Array of snippet dicts
                - count (int): Number of snippets
                - cached (bool): True if snippets exist, False if empty
                - error (str|None): None
        """
        query = self.db.query(Snippet).filter(Snippet.story_id == story_id)

        # Only return active snippets by default
        if not include_archived:
            query = query.filter(Snippet.is_active == True)  # noqa: E712

        snippets = query.order_by(
            Snippet.display_order.asc(), Snippet.created_at.asc()
        ).all()

        snippet_list = [s.to_dict() for s in snippets]

        return {
            "success": True,
            "snippets": snippet_list,
            "count": len(snippet_list),
            "cached": len(snippet_list) > 0,
            "error": None,
        }

    def get_archived_snippets(self, story_id: int) -> Dict:
        """
        Get archived (soft-deleted) snippets for a story.

        Args:
            story_id: ID of the story

        Returns:
            Dict with success, snippets array, and count
        """
        snippets = (
            self.db.query(Snippet)
            .filter(Snippet.story_id == story_id)
            .filter(Snippet.is_active == False)  # noqa: E712
            .order_by(Snippet.created_at.desc())  # Most recent first for archived
            .all()
        )

        snippet_list = [s.to_dict() for s in snippets]

        return {
            "success": True,
            "snippets": snippet_list,
            "count": len(snippet_list),
            "error": None,
        }

    def delete_snippets(self, story_id: int) -> int:
        """
        Soft-delete unlocked snippets for a story (set is_active=False).

        Locked snippets are preserved during regeneration.

        Args:
            story_id: ID of the story

        Returns:
            Number of snippets soft-deleted
        """
        # Only soft-delete unlocked, active snippets
        soft_deleted = (
            self.db.query(Snippet)
            .filter(
                Snippet.story_id == story_id,
                Snippet.is_locked == False,  # noqa: E712
                Snippet.is_active == True,  # noqa: E712
            )
            .update({"is_active": False}, synchronize_session=False)
        )
        self.db.commit()
        return soft_deleted

    def permanently_delete_snippet(self, snippet_id: int) -> bool:
        """
        Permanently delete a snippet from the database.

        Args:
            snippet_id: ID of the snippet to delete

        Returns:
            True if deleted, False if not found
        """
        deleted = (
            self.db.query(Snippet)
            .filter(Snippet.id == snippet_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted > 0

    def toggle_lock(self, snippet_id: int) -> Optional[Dict]:
        """
        Toggle the lock status of a snippet.

        Args:
            snippet_id: ID of the snippet

        Returns:
            Updated snippet dict, or None if not found
        """
        snippet = self.db.query(Snippet).filter(Snippet.id == snippet_id).first()
        if not snippet:
            return None

        snippet.is_locked = not snippet.is_locked
        self.db.commit()
        self.db.refresh(snippet)
        return snippet.to_dict()

    def restore_snippet(self, snippet_id: int) -> Optional[Dict]:
        """
        Restore an archived (soft-deleted) snippet.

        Args:
            snippet_id: ID of the snippet to restore

        Returns:
            Restored snippet dict, or None if not found
        """
        snippet = self.db.query(Snippet).filter(Snippet.id == snippet_id).first()
        if not snippet:
            return None

        snippet.is_active = True
        self.db.commit()
        self.db.refresh(snippet)
        return snippet.to_dict()

    def soft_delete_snippet(self, snippet_id: int) -> Optional[Dict]:
        """
        Soft-delete a single snippet (set is_active=False).

        Args:
            snippet_id: ID of the snippet

        Returns:
            Updated snippet dict, or None if not found
        """
        snippet = self.db.query(Snippet).filter(Snippet.id == snippet_id).first()
        if not snippet:
            return None

        snippet.is_active = False
        self.db.commit()
        self.db.refresh(snippet)
        return snippet.to_dict()

    def get_locked_snippet_count(self, story_id: int) -> int:
        """
        Get count of locked snippets for a story.

        Args:
            story_id: ID of the story

        Returns:
            Number of locked snippets
        """
        return (
            self.db.query(Snippet)
            .filter(
                Snippet.story_id == story_id,
                Snippet.is_locked == True,  # noqa: E712
                Snippet.is_active == True,  # noqa: E712
            )
            .count()
        )

    def get_locked_snippets(self, story_id: int) -> List[Dict]:
        """
        Get all locked, active snippets for a story.

        Used to provide context during regeneration so the AI knows
        what topics/content to avoid duplicating.

        Args:
            story_id: ID of the story

        Returns:
            List of locked snippet dicts with title, content, theme, phase
        """
        snippets = (
            self.db.query(Snippet)
            .filter(
                Snippet.story_id == story_id,
                Snippet.is_locked == True,  # noqa: E712
                Snippet.is_active == True,  # noqa: E712
            )
            .order_by(Snippet.created_at.asc())
            .all()
        )
        return [s.to_dict() for s in snippets]

    def _save_snippets(
        self,
        story_id: int,
        user_id: int,
        snippets: List[Dict],
        hardcoded_phase: Optional[str] = None,
        start_display_order: int = 0,
    ) -> List[Snippet]:
        """
        Save generated snippets to the database.

        Args:
            story_id: ID of the story
            user_id: ID of the user who owns the story
            snippets: List of snippet dicts with title, content, theme
            hardcoded_phase: If provided, overrides any phase in snippet_data.
                            Used for per-chapter generation where we KNOW the phase.
            start_display_order: Starting index for display_order (for appending)

        Returns:
            List of created Snippet objects
        """
        created = []
        for index, snippet_data in enumerate(snippets):
            # Hardcoded phase takes precedence - ensures 100% accurate labels
            phase = hardcoded_phase if hardcoded_phase else snippet_data.get("phase")

            snippet = Snippet(
                story_id=story_id,
                user_id=user_id,
                title=snippet_data["title"],
                content=snippet_data["content"],
                phase=phase,
                theme=snippet_data.get("theme"),
                display_order=start_display_order + index,
            )
            self.db.add(snippet)
            created.append(snippet)

        self.db.commit()

        # Refresh to get IDs
        for s in created:
            self.db.refresh(s)

        return created

    # Valid phases for snippet labels (excludes GREETING and SYNTHESIS which don't generate cards)
    VALID_SNIPPET_PHASES = [
        "FAMILY_HISTORY",
        "CHILDHOOD",
        "ADOLESCENCE",
        "EARLY_ADULTHOOD",
        "MIDLIFE",
        "PRESENT",
    ]

    # Minimum user messages required per chapter to generate snippets
    MIN_MESSAGES_PER_CHAPTER = 2

    def _group_messages_by_phase(
        self, messages: List[Dict[str, Optional[str]]]
    ) -> Dict[str, List[Dict[str, Optional[str]]]]:
        """
        Group messages by their phase_context (chapter).

        Args:
            messages: List of message dicts with role, content, phase_context

        Returns:
            Dict mapping phase names to lists of messages for that phase
        """
        grouped: Dict[str, List[Dict[str, str]]] = {}

        for msg in messages:
            phase = msg.get("phase_context")
            # Skip messages without phase context or from non-content phases
            if not phase or phase not in self.VALID_SNIPPET_PHASES:
                continue

            if phase not in grouped:
                grouped[phase] = []
            grouped[phase].append(msg)

        return grouped

    def _generate_snippets_for_phase(
        self,
        phase: str,
        messages: List[Dict[str, Optional[str]]],
        locked_snippets: List[Dict],
        model_cascade: List[str],
    ) -> Dict:
        """
        Generate snippets for a single chapter/phase.

        AI generates title, content, and theme only - phase is hardcoded by caller.

        Args:
            phase: The chapter name (e.g., "CHILDHOOD")
            messages: Messages belonging to this chapter
            locked_snippets: Locked snippets to avoid duplicating
            model_cascade: List of models to try

        Returns:
            Dict with success, snippets (without phase - caller adds it), model, error
        """
        # Build chapter text for AI
        chapter_text = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
        )

        # Build locked snippets context for this phase
        phase_locked = [s for s in locked_snippets if s.get("phase") == phase]
        locked_context = ""
        if phase_locked:
            locked_topics = "\n".join(
                [
                    (
                        f"- {s['title']}: {s['content'][:100]}..."
                        if len(s["content"]) > 100
                        else f"- {s['title']}: {s['content']}"
                    )
                    for s in phase_locked
                ]
            )
            locked_context = f"""

IMPORTANT - EXISTING LOCKED CARDS FOR THIS CHAPTER (DO NOT DUPLICATE):
The following card(s) already exist for this chapter. Generate NEW content about DIFFERENT moments:

{locked_topics}"""

        # System instruction - NO phase in output, AI only generates title/content/theme
        system_instruction = f"""You are a story curator creating content for printable game cards.

Your task: Analyze this SINGLE CHAPTER of a life story and extract meaningful, emotionally resonant moments.

OUTPUT FORMAT: You MUST respond with ONLY valid JSON, no other text. Use this exact structure:
{{
  "snippets": [
    {{
      "title": "2-5 word catchy title",
      "content": "The snippet text, max 300 characters. Written in third person, narrative style.",
      "theme": "family|growth|challenge|adventure|love|legacy|identity|friendship"
    }}
  ]
}}

RULES:
1. Generate 1-3 snippets based on chapter depth (fewer for short chapters)
2. Each snippet content MUST be under 300 characters
3. Write in third person ("They discovered...", "Growing up, they...")
4. Focus on emotional highlights, turning points, and defining moments from THIS chapter
5. Each snippet should stand alone as a meaningful story beat
6. If the chapter is very short or lacks meaningful content, generate just 1 snippet
7. ONLY output the JSON object, nothing else{locked_context}"""

        # User prompt with chapter content
        user_prompt = f"""Analyze this chapter of a life story and generate snippets for game cards:

---CHAPTER: {phase}---
{chapter_text}
---END CHAPTER---

Remember: Output ONLY the JSON object with snippets array. Each snippet max 300 characters. Do NOT include a "phase" field - the chapter is already known."""

        # Try models in cascade
        for attempt_idx, model_name in enumerate(model_cascade):
            try:
                print(
                    f"[Snippets] [{phase}] Attempt {attempt_idx + 1}: Trying '{model_name}'..."
                )

                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=self.api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True,
                )

                response = llm.invoke(
                    [
                        SystemMessage(content=system_instruction),
                        HumanMessage(content=user_prompt),
                    ]
                )

                print(f"[Snippets] [{phase}] SUCCESS with {model_name}!")

                # Parse JSON response
                content = response.content
                if isinstance(content, list):
                    content = " ".join(str(item) for item in content)

                result = self._parse_response(str(content), model_name)
                return result

            except Exception as e:
                error_message = str(e)
                print(
                    f"[Snippets] [{phase}] {model_name} FAILED: {error_message[:100]}"
                )

                is_rate_limit = any(
                    indicator in error_message.lower()
                    for indicator in [
                        "429",
                        "resource_exhausted",
                        "rate limit",
                        "quota",
                    ]
                )

                if is_rate_limit and attempt_idx < len(model_cascade) - 1:
                    continue

                if attempt_idx == len(model_cascade) - 1:
                    return {
                        "success": False,
                        "snippets": [],
                        "count": 0,
                        "model": None,
                        "error": f"All models failed for {phase}. Last error: {error_message}",
                    }

        return {
            "success": False,
            "snippets": [],
            "count": 0,
            "model": None,
            "error": f"Failed to generate snippets for {phase}",
        }

    def generate_snippets(self, story_id: int) -> Dict:
        """
        Generate story snippets for a given story and persist to database.

        This method generates snippets PER CHAPTER with hardcoded phase labels:
        1. Groups messages by their phase_context (chapter)
        2. For each chapter with sufficient messages, generates snippets via AI
        3. Hardcodes the chapter name as the snippet's phase (no AI guessing)
        4. Saves all snippets to the database

        Args:
            story_id: ID of the story to generate snippets for

        Returns:
            Dict with keys:
                - success (bool): Whether generation succeeded
                - snippets (list): Array of snippet objects
                - count (int): Number of snippets generated
                - model (str|None): Last model that succeeded
                - error (str|None): Error message if failed
        """
        # Verify story exists and capture user_id immediately
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": f"Story with ID {story_id} not found",
            }

        user_id = story.user_id

        # Fetch messages with phase_context
        messages = self.get_story_messages(story_id)
        if not messages:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": "No messages found for this story",
            }

        # Group messages by chapter
        messages_by_phase = self._group_messages_by_phase(messages)
        print(
            f"[Snippets] Story {story_id}: Found chapters: {list(messages_by_phase.keys())}"
        )

        if not messages_by_phase:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": "No messages with valid phase context found",
            }

        # Get locked snippets BEFORE deleting
        locked_snippets = self.get_locked_snippets(story_id)

        # Delete existing unlocked snippets
        self.delete_snippets(story_id)

        # Get model cascade
        model_cascade = get_model_cascade()
        print(f"[Snippets] Model cascade: {model_cascade}")

        # Generate snippets for each chapter
        all_saved_snippets: List[Snippet] = []
        last_successful_model = None
        errors = []
        display_order = 0

        # Process chapters in chronological order
        for phase in self.VALID_SNIPPET_PHASES:
            if phase not in messages_by_phase:
                continue

            phase_messages = messages_by_phase[phase]

            # Count user messages (skip assistant messages for threshold check)
            user_message_count = sum(
                1 for m in phase_messages if m.get("role") == "user"
            )

            if user_message_count < self.MIN_MESSAGES_PER_CHAPTER:
                print(
                    f"[Snippets] [{phase}] Skipping - only {user_message_count} user messages (need {self.MIN_MESSAGES_PER_CHAPTER})"
                )
                continue

            print(
                f"[Snippets] [{phase}] Generating snippets from {len(phase_messages)} messages..."
            )

            result = self._generate_snippets_for_phase(
                phase=phase,
                messages=phase_messages,
                locked_snippets=locked_snippets,
                model_cascade=model_cascade,
            )

            if result["success"] and result["snippets"]:
                last_successful_model = result["model"]

                # Save snippets with HARDCODED phase - this is the key change!
                saved = self._save_snippets(
                    story_id=story_id,
                    user_id=user_id,
                    snippets=result["snippets"],
                    hardcoded_phase=phase,  # Phase is hardcoded from chapter, not AI
                    start_display_order=display_order,
                )
                all_saved_snippets.extend(saved)
                display_order += len(saved)
                print(f"[Snippets] [{phase}] Saved {len(saved)} snippets")
            else:
                errors.append(f"{phase}: {result.get('error', 'Unknown error')}")
                print(f"[Snippets] [{phase}] Failed: {result.get('error')}")

        # Return combined results
        if all_saved_snippets:
            return {
                "success": True,
                "snippets": [s.to_dict() for s in all_saved_snippets],
                "count": len(all_saved_snippets),
                "model": last_successful_model,
                "error": None if not errors else f"Partial errors: {'; '.join(errors)}",
            }
        else:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": (
                    f"Failed to generate any snippets. Errors: {'; '.join(errors)}"
                    if errors
                    else "No snippets generated"
                ),
            }

    def _parse_response(self, response_text: str, model_name: str) -> Dict:
        """
        Parse and validate the JSON response from Gemini.

        Note: Phase is NOT expected in AI output - it's hardcoded by the caller
        based on which chapter the messages came from.
        """
        try:
            text = response_text.strip()

            # Handle markdown code blocks
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            parsed = json.loads(text)
            snippets = parsed.get("snippets", [])

            # Validate and sanitize snippets
            validated_snippets = []
            for snippet in snippets:
                if not isinstance(snippet, dict):
                    continue

                title = snippet.get("title", "").strip()
                content = snippet.get("content", "").strip()
                # Theme from AI, phase will be hardcoded by caller
                theme = snippet.get("theme", "growth").lower()

                if not title or not content:
                    continue

                # Truncate content if over 300 chars
                if len(content) > 300:
                    content = content[:297] + "..."

                validated_snippets.append(
                    {
                        "title": title,
                        "content": content,
                        "theme": theme,
                        # Note: No phase here - hardcoded by caller in _save_snippets
                    }
                )

            return {
                "success": True,
                "snippets": validated_snippets,
                "count": len(validated_snippets),
                "model": model_name,
                "error": None,
            }

        except json.JSONDecodeError as e:
            print(f"[Snippets] JSON parse error: {e}")
            print(f"[Snippets] Raw response: {response_text[:500]}")
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": model_name,
                "error": f"Failed to parse AI response as JSON: {str(e)}",
            }
