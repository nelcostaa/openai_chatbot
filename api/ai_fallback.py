"""
Pure function module for Google Gemini AI model fallback cascade.

This module provides stateless, testable AI interaction logic extracted from
the original Flask backend. It implements automatic retry with model fallback
when rate limits (429) are encountered.

Key features:
- No Flask dependencies (pure Python)
- Automatic model fallback on rate limit errors
- Configurable timeout per model attempt
- Comprehensive error logging
- Returns structured response with metadata
"""

import os
from typing import Dict, List, Optional

import google.generativeai as genai


def configure_gemini(api_key: Optional[str] = None) -> None:
    """
    Configure Google Gemini API with provided or environment API key.

    Args:
        api_key: Optional API key. If None, reads from GEMINI_API_KEY env var.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not found. Set environment variable or pass as argument."
        )
    genai.configure(api_key=key)


def get_model_cascade() -> List[str]:
    """
    Get model fallback cascade from environment or return defaults.

    Returns:
        List of model names in fallback order.
    """
    env_models = os.getenv("GEMINI_MODELS")
    if env_models:
        return [m.strip() for m in env_models.split(",") if m.strip()]

    # Default cascade: ordered by rate limits and performance
    return [
        "gemini-2.5-flash",  # 10 RPM, 250K TPM, 250 RPD
        "gemini-2.5-flash-lite",  # 15 RPM, 250K TPM, 1K RPD
        "gemini-2.0-flash",  # 15 RPM, 1M TPM, 200 RPD
        "gemini-2.0-flash-lite",  # 30 RPM, 1M TPM, 200 RPD
        "gemini-2.5-flash-preview",  # 10 RPM, 250K TPM, 250 RPD
        "gemini-2.5-flash-lite-preview",  # 15 RPM, 250K TPM, 1K RPD
    ]


def format_messages_for_gemini(messages: List[Dict[str, str]]) -> List[Dict]:
    """
    Convert standard message format to Gemini API format.

    Args:
        messages: List of dicts with 'role' and 'content' keys.
                 Roles: 'user', 'assistant', 'system' (system is handled separately).

    Returns:
        List of Gemini-formatted messages with 'role' and 'parts'.
    """
    gemini_messages = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")

        # Skip system messages (handled via system_instruction parameter)
        if role == "system":
            continue

        # Map roles: assistant -> model, user -> user
        if role == "assistant":
            gemini_messages.append({"role": "model", "parts": [{"text": content}]})
        elif role == "user":
            gemini_messages.append({"role": "user", "parts": [{"text": content}]})

    return gemini_messages


def run_gemini_fallback(
    messages: List[Dict[str, str]],
    system_instruction: str,
    models: Optional[List[str]] = None,
    timeout_per_model: int = 10,
    api_key: Optional[str] = None,
) -> Dict:
    """
    Generate AI response with automatic model fallback on rate limits.

    Attempts each model in sequence until one succeeds or all fail. Context is
    preserved across attempts since conversation history is client-side.

    Args:
        messages: Full conversation history [{'role': 'user|assistant', 'content': '...'}]
        system_instruction: System prompt defining AI persona and behavior
        models: Optional list of models to try. If None, uses get_model_cascade()
        timeout_per_model: Timeout in seconds for each model attempt
        api_key: Optional API key. If None, uses environment variable

    Returns:
        Dict with keys:
            - success (bool): Whether response was generated
            - content (str): AI response text (empty string on failure)
            - model (str|None): Model that succeeded (None on failure)
            - attempts (int): Number of models tried
            - error (str|None): Error message if all failed

    Raises:
        ValueError: If messages list is empty or API key not configured
    """
    if not messages:
        raise ValueError("Messages list cannot be empty")

    # Configure API
    configure_gemini(api_key)

    # Get model cascade
    model_cascade = models or get_model_cascade()

    if not model_cascade:
        raise ValueError("No models available in cascade")

    # Convert messages to Gemini format
    gemini_messages = format_messages_for_gemini(messages)

    # Extract last user message content
    last_user_message = messages[-1].get("content", "")

    # Try each model in cascade
    for attempt_idx, model_name in enumerate(model_cascade):
        try:
            print(f"[AI] Attempt {attempt_idx + 1}/{len(model_cascade)}: {model_name}")

            # Initialize model
            model = genai.GenerativeModel(model_name)

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
                # Use existing conversation history (exclude last message)
                api_history = gemini_messages[:-1]

            # Start chat with history
            chat = model.start_chat(history=api_history)

            # For subsequent messages, include system instruction as reminder
            if len(gemini_messages) > 1:
                message_with_context = (
                    f"[Remember: {system_instruction}]\n\n{last_user_message}"
                )
            else:
                message_with_context = last_user_message

            # Generate response
            response = chat.send_message(message_with_context)

            # Success!
            print(f"[AI] ✅ Success with {model_name}")
            return {
                "success": True,
                "content": response.text,
                "model": model_name,
                "attempts": attempt_idx + 1,
                "error": None,
            }

        except Exception as e:
            error_message = str(e)
            print(f"[AI] ❌ {model_name} failed: {error_message}")

            # Check if rate limit error
            is_rate_limit = any(
                indicator in error_message.lower()
                for indicator in ["429", "resource_exhausted", "rate limit", "quota"]
            )

            if is_rate_limit:
                print(f"[AI] 🔄 Rate limit on {model_name}, trying next model...")

                # If last model, return failure
                if attempt_idx == len(model_cascade) - 1:
                    return {
                        "success": False,
                        "content": "",
                        "model": None,
                        "attempts": len(model_cascade),
                        "error": f"All {len(model_cascade)} models exhausted rate limits",
                    }

                # Continue to next model
                continue

            # Non-rate-limit error - fail immediately
            print(f"[AI] ⚠️ Non-rate-limit error, aborting cascade")
            return {
                "success": False,
                "content": "",
                "model": None,
                "attempts": attempt_idx + 1,
                "error": f"Error with {model_name}: {error_message}",
            }

    # Should never reach here, but just in case
    return {
        "success": False,
        "content": "",
        "model": None,
        "attempts": len(model_cascade),
        "error": "Failed to generate response with any model",
    }
