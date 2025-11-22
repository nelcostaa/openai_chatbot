"""
Serverless chat endpoint for Life Story Game AI Interviewer.

Vercel serverless function that handles AI chat requests with stateless
architecture. All conversation state is managed client-side.

Endpoint: POST /api/chat
"""

import json
import sys
from pathlib import Path
from typing import Dict

# Add project root to path to import conversation logic
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.ai_fallback import run_gemini_fallback
from api.conversation import INTERVIEW_PHASES, STORY_ROUTES


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

    # Get phase (default to GREETING if not provided)
    phase = data.get("phase", "GREETING")
    if phase not in INTERVIEW_PHASES:
        return False, f"Invalid phase: {phase}", {}

    # Get optional route info
    selected_route = data.get("selected_route")
    custom_route_description = data.get("custom_route_description")

    # Validate route if provided
    if selected_route and selected_route not in ["1", "2", "3", "4", "5", "6", "7"]:
        return False, f"Invalid route: {selected_route}", {}

    return (
        True,
        "",
        {
            "messages": messages,
            "phase": phase,
            "selected_route": selected_route,
            "custom_route_description": custom_route_description,
        },
    )


def get_system_instruction(
    phase: str, selected_route: str = None, custom_description: str = None
) -> str:
    """
    Get system instruction based on phase and selected route.

    Args:
        phase: Current interview phase
        selected_route: Selected storytelling route (1-7)
        custom_description: Custom route description (if route 7)

    Returns:
        System instruction string
    """
    phase_config = INTERVIEW_PHASES.get(phase, INTERVIEW_PHASES["GREETING"])
    system_instruction = phase_config["system_instruction"]

    # Adapt instruction based on selected route for question phases
    if "QUESTION" in phase and selected_route:
        if selected_route in STORY_ROUTES:
            route_info = STORY_ROUTES[selected_route]
        elif selected_route == "7":
            route_info = {
                "name": "Personal Route",
                "persona": "Custom approach",
                "goal": "Follow user's preferred method",
                "prompt_focus": custom_description or "Custom storytelling approach",
            }
        else:
            return system_instruction

        route_context = f"""
SELECTED ROUTE: {route_info['name']}
Route Focus: {route_info['goal']}
User Persona: {route_info['persona']}

Adapt your questioning style to match this route's approach while maintaining the core question objective.
"""
        system_instruction = route_context + "\n" + system_instruction

    return system_instruction


def handler(event, context):
    """
    Vercel serverless function handler for chat endpoint.

    Expected request body:
    {
        "messages": [{"role": "user|assistant", "content": "..."}],
        "phase": "GREETING|ROUTE_SELECTION|QUESTION_N|SYNTHESIS",
        "selected_route": "1-7" (optional),
        "custom_route_description": "..." (optional, for route 7)
    }

    Returns:
    {
        "response": "AI generated response",
        "model": "model_name_used",
        "attempts": 2,
        "phase": "current_phase"
    }
    """
    # Get HTTP method
    method = event.get("httpMethod") or event.get("method", "")
    
    # Handle CORS preflight
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": "",
        }

    # Only accept POST
    if method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed. Use POST."}),
        }

    try:
        # Parse request body
        body = event.get("body", "")
        if isinstance(body, str):
            data = json.loads(body) if body else {}
        else:
            data = body

        # Validate payload
        is_valid, error_msg, validated = validate_payload(data)
        if not is_valid:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": error_msg}),
            }

        # Extract validated data
        messages = validated["messages"]
        phase = validated["phase"]
        selected_route = validated["selected_route"]
        custom_route_description = validated["custom_route_description"]

        # Get system instruction for current phase
        system_instruction = get_system_instruction(
            phase, selected_route, custom_route_description
        )

        # Generate AI response with fallback
        result = run_gemini_fallback(
            messages=messages,
            system_instruction=system_instruction,
        )

        # Check if generation succeeded
        if not result["success"]:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {
                        "error": result["error"] or "Failed to generate AI response",
                        "attempts": result["attempts"],
                    }
                ),
            }

        # Return success response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "response": result["content"],
                    "model": result["model"],
                    "attempts": result["attempts"],
                    "phase": phase,
                }
            ),
        }

    except json.JSONDecodeError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Invalid JSON: {str(e)}"}),
        }

    except Exception as e:
        print(f"[ERROR] Unhandled exception in chat handler: {e}")
        import traceback

        traceback.print_exc()

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
