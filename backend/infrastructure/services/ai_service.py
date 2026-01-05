"""
AI Service Implementation

Concrete implementation using LangGraph agent with Gemini fallback cascade.
"""

from typing import List

from backend.application.interfaces.services import AIResponse, AIService, ChatMessage
from backend.domain.exceptions import AIServiceError


class LangGraphAIService(AIService):
    """
    AI service implementation using LangGraph agent.

    This wraps the existing agent.py implementation and provides
    a clean interface for the application layer.
    """

    def generate_response(
        self, messages: List[ChatMessage], system_instruction: str
    ) -> AIResponse:
        """
        Generate AI response using LangGraph agent.

        Args:
            messages: Conversation history
            system_instruction: System prompt

        Returns:
            AIResponse with generated content

        Raises:
            AIServiceError: If all models fail
        """
        from langchain_core.messages import AIMessage, HumanMessage

        # Import the compiled agent
        from backend.app.core.agent import agent_app

        # Convert ChatMessage to LangChain messages
        lc_messages = []
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        try:
            # Invoke the agent
            result = agent_app.invoke(
                {
                    "messages": lc_messages,
                    "phase_instruction": system_instruction,
                }
            )

            # Extract response
            response_messages = result.get("messages", [])
            if not response_messages:
                raise AIServiceError("No response from AI agent")

            last_message = response_messages[-1]
            content = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

            return AIResponse(
                content=content,
                model="gemini",  # Agent handles model selection internally
                attempts=1,
            )

        except Exception as e:
            raise AIServiceError(f"AI generation failed: {str(e)}")

    def generate_snippets(self, messages: List[ChatMessage], count: int = 12) -> str:
        """
        Generate story snippets from conversation.

        This delegates to the existing snippet service for now.
        TODO: Refactor snippet generation to use this interface.

        Args:
            messages: Conversation history
            count: Number of snippets to generate

        Returns:
            JSON string with snippet data
        """
        # For now, raise not implemented
        # The existing snippet service handles this differently
        raise NotImplementedError(
            "Snippet generation not yet implemented in clean architecture. "
            "Use backend.app.services.snippets.SnippetService directly for now."
        )
