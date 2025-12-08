import os
from typing import Annotated, List, TypedDict, Union

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

load_dotenv()


# 1. Define State
# This tracks the conversation history passing through the graph
class AgentState(TypedDict):
    messages: List[BaseMessage]
    phase_instruction: str


# 2. Model Fallback Cascade
def get_model_cascade() -> List[str]:
    """
    Get model fallback cascade from environment or return defaults.
    Ordered by rate limits and performance.
    """
    env_models = os.getenv("GEMINI_MODELS")
    if env_models:
        return [m.strip() for m in env_models.split(",") if m.strip()]

    # Default cascade - ordered by rate limits (free tier models)
    return [
        "gemini-2.0-flash-exp",  # Experimental, fastest
        "gemini-2.0-flash",  # Stable 2.0
        "gemini-2.5-flash",  # Latest stable
        "gemini-flash-latest",  # Generic alias (1.5 Flash)
        "gemini-2.0-flash-lite",  # Lite version fallback
    ]


# 3. Initialize API Key
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY is not set in .env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# 4. Define Nodes with Fallback Logic
def chatbot_node(state: AgentState):
    """
    The core node that talks to the AI with automatic model fallback.

    Tries models in cascade until one succeeds or all fail.
    """
    messages = state["messages"]
    phase_instruction = state["phase_instruction"]

    # Prepend the system instruction (Phase/Persona)
    system_msg = SystemMessage(content=phase_instruction)
    full_messages = [system_msg] + messages

    # Get model cascade
    model_cascade = get_model_cascade()

    # Try each model in cascade
    for attempt_idx, model_name in enumerate(model_cascade):
        try:
            print(
                f"[Agent] Attempt {attempt_idx + 1}/{len(model_cascade)}: {model_name}"
            )

            # Initialize model for this attempt
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=GEMINI_API_KEY,
                temperature=0.7,
                convert_system_message_to_human=True,
            )

            # Call Gemini
            response = llm.invoke(full_messages)

            # Success!
            print(f"[Agent] ✅ Success with {model_name}")
            return {"messages": [response]}

        except Exception as e:
            error_message = str(e)
            print(f"[Agent] ❌ {model_name} failed: {error_message}")

            # Check if rate limit error
            is_rate_limit = any(
                indicator in error_message.lower()
                for indicator in ["429", "resource_exhausted", "rate limit", "quota"]
            )

            if is_rate_limit:
                print(f"[Agent] 🔄 Rate limit on {model_name}, trying next model...")

                # If last model, raise error
                if attempt_idx == len(model_cascade) - 1:
                    raise Exception(
                        f"All {len(model_cascade)} models exhausted rate limits"
                    )

                # Continue to next model
                continue

            # Non-rate-limit error - fail immediately
            print(f"[Agent] ⚠️ Non-rate-limit error, aborting cascade")
            raise

    # Should never reach here
    raise Exception("Failed to generate response with any model")


# 4. Build Graph
workflow = StateGraph(AgentState)

# Add the node
workflow.add_node("chatbot", chatbot_node)

# Define flow (Start -> Chatbot -> End)
workflow.set_entry_point("chatbot")
workflow.add_edge("chatbot", END)

# 5. Compile the app
agent_app = workflow.compile()
