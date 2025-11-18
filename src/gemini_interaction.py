import os
from typing import Dict, List

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)
# Use stable Gemini 2.0 model
model = genai.GenerativeModel("gemini-2.0-flash")


def format_messages_for_gemini(messages: List[Dict[str, str]]) -> List[Dict]:
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


def get_completion(
    system_instruction: str,
    conversation_history: List[Dict[str, str]],
    user_message: str,
) -> str:
    """Generate response using Google Gemini with system instruction"""
    try:
        # Create model with system instruction
        model = genai.GenerativeModel(
            "gemini-2.0-flash", system_instruction=system_instruction
        )

        # Prepare history for chat session
        # If the last message in history is the current user_message, exclude it
        # because we will send it via chat.send_message
        history_to_process = conversation_history
        if (
            conversation_history
            and conversation_history[-1].get("content") == user_message
        ):
            history_to_process = conversation_history[:-1]

        # Convert to Gemini format
        gemini_history = format_messages_for_gemini(history_to_process)

        # Start chat with history
        chat = model.start_chat(history=gemini_history)

        # Send message
        response = chat.send_message(user_message)

        return response.text

    except Exception as e:
        print(f"\nError generating AI response: {e}")
        raise
