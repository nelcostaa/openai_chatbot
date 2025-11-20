import os
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to Python path to import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.conversation import INTERVIEW_PHASES, STORY_ROUTES

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)

# Model fallback cascade - ordered by preference and rate limits
# When 429 error occurs, we'll try the next model in the list
# Context is preserved since conversation history is client-side!
MODEL_FALLBACK_CASCADE = [
    # Primary: Best price-performance
    "gemini-2.5-flash",  # 10 RPM, 250K TPM, 250 RPD
    # Fallback tier 1: Higher RPM models
    "gemini-2.5-flash-lite",  # 15 RPM, 250K TPM, 1K RPD (more daily quota)
    "gemini-2.0-flash",  # 15 RPM, 1M TPM, 200 RPD (huge context window)
    # Fallback tier 2: Highest RPM
    "gemini-2.0-flash-lite",  # 30 RPM, 1M TPM, 200 RPD (fastest RPM)
    # Fallback tier 3: Preview models
    "gemini-2.5-flash-preview",  # 10 RPM, 250K TPM, 250 RPD
    "gemini-2.5-flash-lite-preview",  # 15 RPM, 250K TPM, 1K RPD
]

# Track which model is currently active (global state)
current_model_index = 0

# In-memory session storage (replace with database in production)
# Key: session_id, Value: {phase, selected_route, custom_route_description, question_count}
sessions = {}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def format_messages_for_gemini(messages):
    """Convert message history to Gemini API format"""
    gemini_messages = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        # Map roles: assistant -> model, user -> user
        if role == "assistant":
            gemini_messages.append({"role": "model", "parts": [{"text": content}]})
        elif role == "user":
            gemini_messages.append({"role": "user", "parts": [{"text": content}]})

    return gemini_messages


def get_system_instruction(phase, selected_route=None, custom_description=None):
    """Get system instruction based on phase and selected route"""
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


def generate_ai_response(messages, system_instruction):
    """
    Generate response using Google Gemini AI with automatic model fallback.

    If a model returns 429 (rate limit exceeded), automatically tries the next
    model in the cascade. Context is preserved since conversation history is
    maintained client-side.
    """
    global current_model_index

    # Convert messages to Gemini format once
    gemini_messages = format_messages_for_gemini(messages)
    last_message = messages[-1].get("content", "")

    # Try each model in the fallback cascade
    for attempt_index in range(len(MODEL_FALLBACK_CASCADE)):
        # Use current model or try next one
        model_to_try_index = (current_model_index + attempt_index) % len(
            MODEL_FALLBACK_CASCADE
        )
        model_name = MODEL_FALLBACK_CASCADE[model_to_try_index]

        try:
            print(
                f"[API] Attempting with model: {model_name} (attempt {attempt_index + 1}/{len(MODEL_FALLBACK_CASCADE)})"
            )

            # Initialize model
            model_with_instruction = genai.GenerativeModel(model_name)

            # Build conversation history with system instruction embedded
            api_history = []

            # If first message, establish system context
            if len(gemini_messages) == 1:
                api_history = [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"System Instructions: {system_instruction}\n\nPlease acknowledge you understand these instructions."
                            }
                        ],
                    },
                    {
                        "role": "model",
                        "parts": [
                            {"text": "I understand and will follow these instructions."}
                        ],
                    },
                ]
            else:
                # Use existing conversation history
                api_history = gemini_messages[:-1]

            # Start chat with history
            chat = model_with_instruction.start_chat(history=api_history)

            # For subsequent messages, include system instruction as context
            if len(gemini_messages) > 1:
                message_with_context = (
                    f"[Remember: {system_instruction}]\n\n{last_message}"
                )
            else:
                message_with_context = last_message

            # Generate response
            response = chat.send_message(message_with_context)

            # Success! Update current model if we switched
            if model_to_try_index != current_model_index:
                old_model = MODEL_FALLBACK_CASCADE[current_model_index]
                current_model_index = model_to_try_index
                print(
                    f"[API] ✅ Successfully switched from {old_model} to {model_name}"
                )
            else:
                print(f"[API] ✅ Success with {model_name}")

            return response.text

        except Exception as e:
            error_message = str(e)
            print(f"[API] ❌ Error with {model_name}: {error_message}")

            # Check if it's a 429 rate limit error
            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "rate limit" in error_message.lower()
            ):
                print(f"[API] 🔄 Rate limit hit on {model_name}, trying next model...")

                # If this was our last attempt, raise the error
                if attempt_index == len(MODEL_FALLBACK_CASCADE) - 1:
                    print(
                        f"[API] ⚠️ All models exhausted! All {len(MODEL_FALLBACK_CASCADE)} models hit rate limits."
                    )
                    raise Exception(
                        "All available models have exceeded their rate limits. Please try again later."
                    )

                # Otherwise, continue to next model
                continue

            # For non-429 errors, log and re-raise immediately
            print(f"[API] ⚠️ Non-rate-limit error: {error_message}")
            import traceback

            traceback.print_exc()
            raise

    # Should never reach here, but just in case
    raise Exception("Failed to generate response with any available model")


# ==============================================================================
# API ENDPOINTS
# ==============================================================================


@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint for AI conversation with phase management"""
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get session ID (default to 'default' for now, should be user-specific)
        session_id = data.get("session_id", "default")

        # Initialize session if doesn't exist
        if session_id not in sessions:
            sessions[session_id] = {
                "phase": "GREETING",
                "selected_route": None,
                "custom_route_description": None,
                "question_count": 0,
            }

        session = sessions[session_id]

        # Support both 'messages' (full history) and 'message' (legacy single message)
        messages = data.get("messages", [])

        if not messages:
            # Fallback to legacy format
            if "message" in data:
                user_message = data["message"].strip()
                if not user_message:
                    return jsonify({"error": "Empty message"}), 400
                messages = [{"role": "user", "content": user_message}]
            else:
                return jsonify({"error": "No messages provided"}), 400

        # Validate messages
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({"error": "Messages must be a non-empty array"}), 400

        # Get last user message for phase transition logic
        last_user_message = messages[-1].get("content", "").strip()

        # Handle phase transitions
        should_advance = False

        if session["phase"] == "GREETING":
            affirmative = [
                "yes",
                "yeah",
                "sure",
                "ready",
                "ok",
                "let's go",
                "sim",
                "vamos",
            ]
            should_advance = any(
                word in last_user_message.lower() for word in affirmative
            )

        elif session["phase"] == "ROUTE_SELECTION":
            # Check if user entered a route number
            if last_user_message in ["1", "2", "3", "4", "5", "6"]:
                session["selected_route"] = last_user_message
                should_advance = True
            elif last_user_message == "7":
                if session["selected_route"] is None:
                    session["selected_route"] = "7"
                    # Don't advance yet, need description
            elif session["selected_route"] == "7" and len(last_user_message) > 10:
                session["custom_route_description"] = last_user_message
                should_advance = True

        elif "QUESTION" in session["phase"]:
            # Advance after any non-empty answer
            should_advance = len(last_user_message) > 0

        # Advance phase if needed
        if should_advance:
            phase_order = [
                "GREETING",
                "ROUTE_SELECTION",
                "QUESTION_1",
                "QUESTION_2",
                "QUESTION_3",
                "QUESTION_4",
                "QUESTION_5",
                "QUESTION_6",
                "SYNTHESIS",
            ]
            current_index = phase_order.index(session["phase"])
            if current_index < len(phase_order) - 1:
                session["phase"] = phase_order[current_index + 1]
                if "QUESTION" in session["phase"]:
                    session["question_count"] += 1

        # Get system instruction for current phase
        system_instruction = get_system_instruction(
            session["phase"],
            session["selected_route"],
            session["custom_route_description"],
        )

        # Generate AI response
        response_text = generate_ai_response(messages, system_instruction)

        # Return response with phase info
        return (
            jsonify(
                {
                    "response": response_text,
                    "phase": session["phase"],
                    "selected_route": session["selected_route"],
                    "question_count": session["question_count"],
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error processing message: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"Error processing message: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "AI Chatbot"}), 200


@app.route("/api/model-status", methods=["GET"])
def model_status():
    """Get current active model and fallback cascade info"""
    return (
        jsonify(
            {
                "current_model": MODEL_FALLBACK_CASCADE[current_model_index],
                "current_model_index": current_model_index,
                "available_models": MODEL_FALLBACK_CASCADE,
                "total_models": len(MODEL_FALLBACK_CASCADE),
                "fallback_enabled": True,
            }
        ),
        200,
    )


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("🚀 Flask server running at http://localhost:5000")
    print("📡 Available endpoints:")
    print("   - POST /api/chat         (Chat with AI)")
    print("   - GET  /health           (Health check)")
    print("   - GET  /api/model-status (Current model info)")
    print("\n🤖 Model Fallback Cascade Enabled:")
    for idx, model in enumerate(MODEL_FALLBACK_CASCADE):
        prefix = "  ➤" if idx == current_model_index else "   "
        print(f"{prefix} {idx + 1}. {model}")
    print("\n💡 If rate limit (429) is hit, will automatically fallback to next model")
    print("   Context is preserved - conversation history maintained client-side!\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
