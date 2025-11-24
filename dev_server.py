#!/usr/bin/env python3
"""
Local development server that simulates Vercel serverless functions.
Run this alongside 'npm run dev' in the frontend directory.
"""

import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    """Health check endpoint."""
    if request.method == "OPTIONS":
        return "", 200

    return (
        jsonify(
            {
                "status": "healthy",
                "service": "Life Story AI Interviewer",
                "version": "1.0.0",
            }
        ),
        200,
    )


@app.route("/api/model-status", methods=["GET", "OPTIONS"])
def model_status():
    """Model status endpoint."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        from api.ai_fallback import GEMINI_MODELS

        return (
            jsonify({"available_models": GEMINI_MODELS, "status": "operational"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    """Handle chat endpoint with direct Flask integration."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        # Import the chat processing logic directly
        from api.ai_fallback import run_gemini_fallback
        from api.chat import (
            ROUTE_REGISTRY,
            get_current_phase_from_route,
            reconstruct_route_state,
            validate_payload,
        )

        # Get JSON data
        data = request.get_json()

        # Validate payload
        is_valid, error_msg, validated_data = validate_payload(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        messages = validated_data["messages"]
        route_id = validated_data["route_id"]
        current_phase = validated_data.get("phase")
        age_range = validated_data.get("age_range")
        advance_phase = validated_data.get("advance_phase", False)
        age_selection_input = validated_data.get("age_selection_input")
        selected_tags = validated_data.get("selected_tags", [])

        # Get route class
        route_class = ROUTE_REGISTRY.get(route_id)
        if not route_class:
            return jsonify({"error": f"Unknown route: {route_id}"}), 400

        # Reconstruct route state
        route = reconstruct_route_state(route_class, messages, age_range)

        # If age selection input provided, validate and advance phase
        if age_selection_input and current_phase == "AGE_SELECTION":
            # Set route phase to AGE_SELECTION so should_advance works correctly
            route.phase = "AGE_SELECTION"
            if route.should_advance(age_selection_input, explicit_transition=False):
                current_phase = route.advance_phase()
                print(f"[AGE] Selected: {age_selection_input} -> {route.age_range}")
                print(f"[PHASE] Advanced to: {current_phase}")

                # Return immediately without generating AI response
                # Age selection is a silent operation - no chat message needed
                response_data = {
                    "response": "",  # Empty response - no AI message
                    "model": "none",
                    "attempts": 0,
                    "phase": current_phase,
                    "age_range": (
                        route.get_age_range()
                        if hasattr(route, "get_age_range")
                        else None
                    ),
                }
                return jsonify(response_data), 200

        # Get current phase if not provided
        if not current_phase:
            current_phase = get_current_phase_from_route(route, messages)

        # Handle explicit phase advancement if requested
        if advance_phase:
            old_phase = current_phase
            route.phase = current_phase
            # Get last user message for validation
            last_user_msg = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
            )
            # Check if should advance (with explicit_transition=True)
            if route.should_advance(last_user_msg, explicit_transition=True):
                current_phase = route.advance_phase()
                print(f"[PHASE] Advanced from {old_phase} to: {current_phase}")

                # Add transition marker to messages so AI knows to acknowledge the phase change
                # This allows the system instruction's "If user just clicked 'Next Phase'" logic to trigger
                messages = messages + [
                    {
                        "role": "user",
                        "content": f"[Moving to next phase: {current_phase}]",
                    }
                ]

        # Get system instruction for current phase
        try:
            route.phase = current_phase
            phase_config = route.get_current_phase()
            system_instruction = phase_config["system_instruction"]
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": f"Invalid phase '{current_phase}' for route '{route_id}': {str(e)}"
                    }
                ),
                400,
            )

        # Inject selected tags into system instruction if present
        if selected_tags:
            tag_context = f"\n\nUSER'S SELECTED FOCUS AREAS: {', '.join(selected_tags)}\n\nThe user has indicated interest in exploring these themes. When appropriate, gently guide the conversation to touch on these topics, but don't force them. Let the natural flow of their story reveal connections to these themes."
            system_instruction = system_instruction + tag_context
            print(f"[TAGS] Active themes: {', '.join(selected_tags)}")

        # Generate AI response
        result = run_gemini_fallback(
            messages=messages, system_instruction=system_instruction
        )

        if not result["success"]:
            return (
                jsonify(
                    {
                        "error": result["error"] or "Failed to generate AI response",
                        "attempts": result["attempts"],
                    }
                ),
                500,
            )

        # Prepare response
        response_data = {
            "response": result["content"],
            "model": result["model"],
            "attempts": result["attempts"],
            "phase": current_phase,
        }

        # Include age_range if available
        if hasattr(route, "get_age_range") and route.get_age_range():
            response_data["age_range"] = route.get_age_range()

        return jsonify(response_data), 200

    except Exception as e:
        print(f"[ERROR] Unhandled exception in chat handler: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Local Development Server Running")
    print("=" * 60)
    print(f"\n📡 API Server: http://localhost:5000")
    print(f"🎨 Frontend:   cd frontend && npm run dev")
    print(f"\n✅ Endpoints:")
    print(f"   GET  http://localhost:5000/api/health")
    print(f"   GET  http://localhost:5000/api/model-status")
    print(f"   POST http://localhost:5000/api/chat")
    print(f"\n💡 Configure frontend to proxy /api/* to http://localhost:5000\n")

    app.run(debug=True, port=5000, host="0.0.0.0")
