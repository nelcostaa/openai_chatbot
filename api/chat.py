"""
Serverless chat endpoint for Life Story AI Interviewer - Modular Route System.

Vercel serverless function that handles AI chat requests with stateless
architecture. Uses new modular route system from api/routes/.

Endpoint: POST /api/chat
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import parse_qs

# Add project root to path to import route logic
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.ai_fallback import run_gemini_fallback
from api.routes import ChronologicalSteward

# Route registry - maps route identifiers to route classes
ROUTE_REGISTRY = {
    "1": ChronologicalSteward,
    "chronological": ChronologicalSteward,
}


def validate_payload(data: Dict) -> tuple[bool, str, Dict]:
    """
    Validate incoming request payload.

    Args:
        data: Parsed JSON request body

    Returns:
        Tuple of (is_valid, error_message, validated_data)
    """
    if not data:
        return False, "Empty request body", {}

    # Get messages
    messages = data.get("messages", [])
    if not isinstance(messages, list) or len(messages) == 0:
        return False, "messages must be a non-empty array", {}

    # Validate message structure
    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return False, f"Message {idx} must be an object", {}

        if "role" not in msg or "content" not in msg:
            return False, f"Message {idx} missing 'role' or 'content'", {}

        if msg["role"] not in ["user", "assistant", "system"]:
            return False, f"Message {idx} has invalid role: {msg['role']}", {}

        if not isinstance(msg["content"], str):
            return False, f"Message {idx} content must be a string", {}

    # Validate total message size (prevent abuse)
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    if total_chars > 50000:  # 50K char limit
        return False, f"Total message size ({total_chars} chars) exceeds 50K limit", {}

    # Get route (default to chronological)
    route_id = data.get("route", "1")
    if route_id not in ROUTE_REGISTRY:
        return False, f"Invalid route: {route_id}", {}

    # Get phase (optional - route will determine if not provided)
    phase = data.get("phase")

    # Get age range (for age-aware routes)
    age_range = data.get("age_range")

    return (
        True,
        "",
        {
            "messages": messages,
            "route_id": route_id,
            "phase": phase,
            "age_range": age_range,
        },
    )


def reconstruct_route_state(
    route_class, messages: list, age_range: Optional[str] = None
):
    """
    Reconstruct route state from message history.

    Since the backend is stateless, we reconstruct the route object's state
    from the client-provided message history.

    Args:
        route_class: The route class to instantiate
        messages: Message history from client
        age_range: User's age range (if already selected)

    Returns:
        Instantiated route object with reconstructed state
    """
    route = route_class()

    # Replay messages to reconstruct state
    for msg in messages:
        route.add_message(msg["role"], msg["content"])

    # Set age range if provided
    if age_range and hasattr(route, "age_range"):
        route.age_range = age_range
        if hasattr(route, "_configure_phases_for_age"):
            route._configure_phases_for_age()

    return route


def get_current_phase_from_route(route, messages: list) -> str:
    """
    Determine current phase from route state and message history.

    Args:
        route: Route object
        messages: Message history

    Returns:
        Current phase name
    """
    # If phase_order not configured yet, return initial phase
    if not route.phase_order or len(route.phase_order) <= 2:
        return route.get_initial_phase()

    # Count user messages to estimate phase
    user_message_count = sum(1 for msg in messages if msg["role"] == "user")

    # Determine phase index
    # GREETING: 0 user messages or 1 (saying "yes")
    # AGE_SELECTION: 1-2 user messages
    # Subsequent phases: 3+ user messages

    if user_message_count == 0:
        return "GREETING"
    elif user_message_count == 1:
        # Check if they said yes to greeting
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        affirmative = ["yes", "yeah", "sure", "ready", "ok", "let's go", "sim", "vamos"]
        if any(word in last_user_msg.lower() for word in affirmative):
            return "AGE_SELECTION"
        return "GREETING"
    elif user_message_count == 2:
        # Should be at AGE_SELECTION or just past it
        if not route.is_age_selected():
            return "AGE_SELECTION"
        # Age was selected, move to first interview phase
        return route.phase_order[2] if len(route.phase_order) > 2 else "CHILDHOOD"
    else:
        # Advanced phases - estimate based on message count
        # user_message 3 → phase_order[2] (CHILDHOOD)
        # user_message 4 → phase_order[3] (ADOLESCENCE), etc.
        phase_index = min(user_message_count - 1, len(route.phase_order) - 1)
        return route.phase_order[phase_index]


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler for chat endpoint.

    Expected request body:
    {
        "messages": [{"role": "user|assistant", "content": "..."}],
        "route": "1|chronological" (optional, default: "1"),
        "phase": "GREETING|AGE_SELECTION|..." (optional),
        "age_range": "under_18|18_30|..." (optional, for age-aware routes)
    }

    Returns:
    {
        "response": "AI generated response",
        "model": "model_name_used",
        "attempts": 2,
        "phase": "current_phase",
        "age_range": "under_18|..." (if applicable)
    }
    """

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for chat."""
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            # Parse JSON
            data = json.loads(body) if body else {}

            # Validate payload
            is_valid, error_msg, validated = validate_payload(data)
            if not is_valid:
                self._send_json_response(400, {"error": error_msg})
                return

            # Extract validated data
            messages = validated["messages"]
            route_id = validated["route_id"]
            provided_phase = validated["phase"]
            age_range = validated["age_range"]

            # Instantiate route and reconstruct state
            route_class = ROUTE_REGISTRY[route_id]
            route = reconstruct_route_state(route_class, messages, age_range)

            # Determine current phase
            if provided_phase:
                current_phase = provided_phase
            else:
                current_phase = get_current_phase_from_route(route, messages)

            # Get system instruction for current phase
            try:
                route.phase = current_phase
                phase_config = route.get_current_phase()
                system_instruction = phase_config["system_instruction"]
            except (ValueError, KeyError) as e:
                self._send_json_response(
                    400,
                    {
                        "error": f"Invalid phase '{current_phase}' for route '{route_id}': {str(e)}"
                    },
                )
                return

            # Generate AI response with fallback
            result = run_gemini_fallback(
                messages=messages,
                system_instruction=system_instruction,
            )

            # Check if generation succeeded
            if not result["success"]:
                self._send_json_response(
                    500,
                    {
                        "error": result["error"] or "Failed to generate AI response",
                        "attempts": result["attempts"],
                    },
                )
                return

            # Prepare response
            response_data = {
                "response": result["content"],
                "model": result["model"],
                "attempts": result["attempts"],
                "phase": current_phase,
            }

            # Include age_range in response if route has it
            if hasattr(route, "get_age_range") and route.get_age_range():
                response_data["age_range"] = route.get_age_range()

            # Return success response
            self._send_json_response(200, response_data)

        except json.JSONDecodeError as e:
            self._send_json_response(400, {"error": f"Invalid JSON: {str(e)}"})

        except Exception as e:
            print(f"[ERROR] Unhandled exception in chat handler: {e}")
            import traceback

            traceback.print_exc()
            self._send_json_response(500, {"error": f"Internal server error: {str(e)}"})

    def _send_json_response(self, status_code: int, data: dict):
        """Helper method to send JSON responses."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
