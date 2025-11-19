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
model = genai.GenerativeModel("gemini-2.5-flash")

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
    """Generate response using Google Gemini AI with system instruction"""
    try:
        # Initialize model WITHOUT system_instruction parameter
        # The parameter doesn't exist in google-generativeai 0.8.3
        model_with_instruction = genai.GenerativeModel("gemini-2.5-flash")

        # Convert messages to Gemini format
        gemini_messages = format_messages_for_gemini(messages)

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

        # Get the last user message
        last_message = messages[-1].get("content", "")

        # For subsequent messages, include system instruction as context
        if len(gemini_messages) > 1:
            message_with_context = f"[Remember: {system_instruction}]\n\n{last_message}"
        else:
            message_with_context = last_message

        # Generate response
        response = chat.send_message(message_with_context)

        return response.text

    except Exception as e:
        print(f"Error generating AI response: {e}")
        import traceback

        traceback.print_exc()
        raise


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


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("🚀 Flask server running at http://localhost:5000")
    print("📡 Available endpoints:")
    print("   - POST /api/chat   (Chat with AI)")
    print("   - GET  /health     (Health check)")
    app.run(debug=True, port=5000, host="0.0.0.0")
