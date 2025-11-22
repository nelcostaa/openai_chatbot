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
        current_phase = validated_data.get("current_phase")
        age_range = validated_data.get("age_range")

        # Get route class
        route_class = ROUTE_REGISTRY.get(route_id)
        if not route_class:
            return jsonify({"error": f"Unknown route: {route_id}"}), 400

        # Reconstruct route state
        route = reconstruct_route_state(route_class, messages, age_range)

        # Get current phase if not provided
        if not current_phase:
            current_phase = get_current_phase_from_route(route, messages)

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
