"""
Snippet generation service for creating story game cards.

This service fetches all messages from a story and uses Gemini to generate
short, impactful snippets (max 300 characters) suitable for printing on cards.
"""

import json
import os
from typing import Dict, List, Optional, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr
from sqlalchemy.orm import Session

from backend.app.models.message import Message
from backend.app.models.story import Story


def get_model_cascade() -> List[str]:
    """Get model fallback cascade from environment or return defaults."""
    env_models = os.getenv("GEMINI_MODELS")
    if env_models:
        return [m.strip() for m in env_models.split(",") if m.strip()]

    return [
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-lite",
    ]


class SnippetService:
    """
    Service for generating story snippets (game cards) from conversation history.

    Uses Gemini to analyze the story and create 3-8 short, impactful snippets
    suitable for printing on game cards.
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

    def generate_snippets(self, story_id: int) -> Dict:
        """
        Generate story snippets for a given story.

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
        # Verify story exists
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return {
                "success": False,
                "snippets": [],
                "count": 0,
                "model": None,
                "error": f"Story with ID {story_id} not found",
            }

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

        for attempt_idx, model_name in enumerate(model_cascade):
            try:
                print(
                    f"[Snippets] Attempt {attempt_idx + 1}/{len(model_cascade)}: {model_name}"
                )

                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    api_key=self.api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True,
                )

                # Call Gemini
                response = llm.invoke(
                    [
                        SystemMessage(content=system_instruction),
                        HumanMessage(content=user_prompt),
                    ]
                )

                print(f"[Snippets] ✅ Success with {model_name}")

                # Parse JSON response - handle both string and list content
                content = response.content
                if isinstance(content, list):
                    # Join list items if response is a list
                    content = " ".join(str(item) for item in content)
                return self._parse_response(str(content), model_name)

            except Exception as e:
                error_message = str(e)
                print(f"[Snippets] ❌ {model_name} failed: {error_message}")

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

                if is_rate_limit and attempt_idx < len(model_cascade) - 1:
                    print(f"[Snippets] 🔄 Rate limit, trying next model...")
                    continue

                # Last model or non-rate-limit error
                if attempt_idx == len(model_cascade) - 1:
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
