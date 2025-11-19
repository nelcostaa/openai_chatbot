from src.conversation import ConversationState
from src.gemini_interaction import get_completion as generate_ai_response
from src.terminal_ui import (
    get_user_input,
    print_ai_message,
    print_header,
    print_phase_info,
    print_route_options,
)


def run_interview():
    """Run the complete interview flow in terminal"""
    print_header()

    # Initialize conversation state
    state = ConversationState()
    # Start with greeting - automatically send first message
    print_phase_info(state)

    phase_config = state.get_current_phase()
    system_instruction = phase_config["system_instruction"]

    # Generate initial greeting
    greeting = generate_ai_response(system_instruction, [], "Hello")
    state.add_message("assistant", greeting)
    print_ai_message(greeting)

    # Main conversation loop
    while state.phase != "SYNTHESIS" or state.question_count < 6:
        # Get user input
        user_message = get_user_input()

        if not user_message:
            print("\nPlease provide a response.\n")
            continue

        # Handle exit command
        if user_message.lower() in ["exit", "quit", "stop"]:
            print("\nThank you for sharing your story. Goodbye!\n")
            break

        # Add user message to history
        state.add_message("user", user_message)

        # Check if should advance phase
        if state.should_advance(user_message):
            previous_phase = state.phase
            state.advance_phase()

            if previous_phase != state.phase:
                # Show route options when entering route selection phase
                if state.phase == "ROUTE_SELECTION":
                    print_route_options()
                print_phase_info(state)

        # Get current phase configuration
        phase_config = state.get_current_phase()

        # Get system instruction for current phase
        system_instruction = phase_config["system_instruction"]

        # Adapt instruction based on selected route (for question phases)
        if "QUESTION" in state.phase and state.selected_route:
            system_instruction = state.get_route_adapted_instruction(system_instruction)

        # Generate AI response
        ai_response = generate_ai_response(
            system_instruction, state.messages, user_message
        )

        # Add AI response to history
        state.add_message("assistant", ai_response)

        # Print AI response
        print_ai_message(ai_response)

        # If we just completed synthesis, end interview
        if state.phase == "SYNTHESIS" and state.question_count >= 5:
            print("\n" + "=" * 70)
            print("         INTERVIEW COMPLETE")
            print("=" * 70 + "\n")
            break

    # Print conversation summary
    print("\nConversation Summary:")
    print(f"Total messages: {len(state.messages)}")
    print(f"Questions answered: {state.question_count}")
    print(f"Final phase: {state.phase}\n")


if __name__ == "__main__":
    try:
        run_interview()
    except KeyboardInterrupt:
        print("\n\nInterview interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n\nError running interview: {e}\n")
