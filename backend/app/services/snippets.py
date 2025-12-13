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

    def get_story_messages(self, story_id: int) -> List[Dict[str, str]]:
        """
        Fetch all messages for a story.

        Returns list of dicts with 'role' and 'content' keys.
        """
        messages = (
            self.db.query(Message)
            .filter(Message.story_id == story_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        return [
            {"role": str(msg.role), "content": str(msg.content)} for msg in messages
        ]

    def get_existing_snippets(self, story_id: int) -> Dict:
        """
        Get existing snippets for a story from the database.

        Args:
            story_id: ID of the story

        Returns:
            Dict with keys:
                - success (bool): True
                - snippets (list): Array of snippet dicts
                - count (int): Number of snippets
                - cached (bool): True if snippets exist, False if empty
                - error (str|None): None
        """
        snippets = (
            self.db.query(Snippet)
            .filter(Snippet.story_id == story_id)
            .order_by(Snippet.created_at.asc())
            .all()
        )

        snippet_list = [s.to_dict() for s in snippets]

        return {
            "success": True,
            "snippets": snippet_list,
            "count": len(snippet_list),
            "cached": len(snippet_list) > 0,
            "error": None,
        }

    def delete_snippets(self, story_id: int) -> int:
        """
        Delete all snippets for a story.

        Args:
            story_id: ID of the story

        Returns:
            Number of snippets deleted
        """
        deleted = (
            self.db.query(Snippet)
            .filter(Snippet.story_id == story_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted

    def _save_snippets(
        self, story_id: int, user_id: int, snippets: List[Dict]
    ) -> List[Snippet]:
        """
        Save generated snippets to the database.

        Args:
            story_id: ID of the story
            user_id: ID of the user who owns the story
            snippets: List of snippet dicts with title, content, phase, theme

        Returns:
            List of created Snippet objects
        """
        created = []
        for snippet_data in snippets:
            snippet = Snippet(
                story_id=story_id,
                user_id=user_id,
                title=snippet_data["title"],
                content=snippet_data["content"],
                phase=snippet_data.get("phase"),
                theme=snippet_data.get("theme"),
            )
            self.db.add(snippet)
            created.append(snippet)

        self.db.commit()

        # Refresh to get IDs
        for s in created:
            self.db.refresh(s)

        return created

    def generate_snippets(self, story_id: int) -> Dict:
        """
        Generate story snippets for a given story and persist to database.

        This method:
        1. Deletes any existing snippets for the story
        2. Generates new snippets using AI
        3. Saves the new snippets to the database

        Args:
            story_id: ID of the story to generate snippets for

        Returns:
            Dict with keys:
                - success (bool): Whether generation succeeded
                - snippets (list): Array of snippet objects
                - count (int): Number of snippets generated
                - model (str|None): Model that succeeded
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

        # Capture user_id before any operations that might expire the session object
        user_id = story.user_id

        # Fetch messages
        messages = self.get_story_messages(story_id)
        if not messages:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": "No messages found for this story",
            }

        # Delete existing snippets before regeneration
        self.delete_snippets(story_id)

        # Build story text for context
        story_text = "\n".join(
            [f"{msg['role'].upper()}: {msg['content']}" for msg in messages]
        )

        # System instruction for structured JSON output
        system_instruction = """You are a story curator creating content for printable game cards.

Your task: Analyze the life story conversation and extract the most meaningful, emotionally resonant moments.

OUTPUT FORMAT: You MUST respond with ONLY valid JSON, no other text. Use this exact structure:
{
  "snippets": [
    {
      "title": "2-5 word catchy title",
      "content": "The snippet text, max 300 characters. Written in third person, narrative style.",
      "phase": "CHILDHOOD|ADOLESCENCE|EARLY_ADULTHOOD|MIDLIFE|PRESENT|FAMILY_HISTORY",
      "theme": "family|growth|challenge|adventure|love|legacy|identity|friendship"
    }
  ]
}

RULES:
1. Generate 3-8 snippets based on story depth (fewer for short stories, more for rich ones)
2. Each snippet content MUST be under 300 characters
3. Write in third person ("They discovered...", "Growing up, they...")
4. Focus on emotional highlights, turning points, and defining moments
5. Each snippet should stand alone as a meaningful story beat
6. Vary the themes - don't repeat the same theme consecutively
7. If the story is very short or lacks content, generate just 2-3 snippets
8. ONLY output the JSON object, nothing else"""

        # User prompt with story content
        user_prompt = f"""Analyze this life story conversation and generate snippets for game cards:

---STORY START---
{story_text}
---STORY END---

Remember: Output ONLY the JSON object with snippets array. Each snippet max 300 characters."""

        # Try models in cascade
        model_cascade = get_model_cascade()
        print(f"[Snippets] 🔄 Model cascade: {model_cascade}")
        print(f"[Snippets] 🔄 Story ID: {story_id}, User ID: {user_id}")

        for attempt_idx, model_name in enumerate(model_cascade):
            try:
                print(
                    f"[Snippets] 🔄 Attempt {attempt_idx + 1}/{len(model_cascade)}: Trying '{model_name}'..."
                )

                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=self.api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True,
                )
                print(f"[Snippets] 🔄 LLM initialized for {model_name}")

                # Call Gemini
                print(f"[Snippets] 🔄 Sending request to {model_name}...")
                response = llm.invoke(
                    [
                        SystemMessage(content=system_instruction),
                        HumanMessage(content=user_prompt),
                    ]
                )
                print(f"[Snippets] 🔄 Response received from {model_name}")

                print(f"[Snippets] ✅ SUCCESS with {model_name}!")

                # Parse JSON response - handle both string and list content
                content = response.content
                if isinstance(content, list):
                    # Join list items if response is a list
                    content = " ".join(str(item) for item in content)

                result = self._parse_response(str(content), model_name)

                # If parsing succeeded, save snippets to database
                if result["success"] and result["snippets"]:
                    saved_snippets = self._save_snippets(
                        story_id=story_id, user_id=user_id, snippets=result["snippets"]
                    )
                    # Update result with saved snippet data (includes IDs)
                    result["snippets"] = [s.to_dict() for s in saved_snippets]

                return result

            except Exception as e:
                error_message = str(e)
                print(f"[Snippets] ❌ {model_name} FAILED")
                print(f"[Snippets] ❌ Error type: {type(e).__name__}")
                print(f"[Snippets] ❌ Error message: {error_message[:200]}")

                # Check if rate limit
                is_rate_limit = any(
                    indicator in error_message.lower()
                    for indicator in [
                        "429",
                        "resource_exhausted",
                        "rate limit",
                        "quota",
                    ]
                )

                if is_rate_limit:
                    print(f"[Snippets] 🔄 Rate limit detected, trying next model...")

                if is_rate_limit and attempt_idx < len(model_cascade) - 1:
                    print(f"[Snippets] 🔄 Moving to next model...")
                    continue

                # Last model or non-rate-limit error
                if attempt_idx == len(model_cascade) - 1:
                    print(f"[Snippets] ❌ ALL MODELS EXHAUSTED")
                    return {
                        "success": False,
                        "snippets": [],
                        "count": 0,
                        "model": None,
                        "error": f"All models failed. Last error: {error_message}",
                    }

        return {
            "success": False,
            "snippets": [],
            "count": 0,
            "model": None,
            "error": "Failed to generate snippets with any model",
        }

    def _parse_response(self, response_text: str, model_name: str) -> Dict:
        """Parse and validate the JSON response from Gemini."""
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
                phase = snippet.get("phase", "PRESENT").upper()
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
                        "phase": phase,
                        "theme": theme,
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
