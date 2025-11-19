from src.conversation import STORY_ROUTES, ConversationState


def print_header():
    """Print colorful header"""
    print("\n" + "=" * 70)
    print("         LIFE STORY GAME - AI INTERVIEWER TEST")
    print("=" * 70 + "\n")


def print_route_options():
    """Print available route options in a clear format"""
    print("\n" + "=" * 70)
    print("        CHOOSE YOUR STORYTELLING APPROACH")
    print("=" * 70 + "\n")

    for route_num, route_info in STORY_ROUTES.items():
        print(f"{route_num}. {route_info['name']}")
        print(f"   {route_info['persona']}")
        print(f"   → {route_info['goal']}\n")

    print("7. Personal Route")
    print("   Define your own approach to telling your story\n")
    print("=" * 70)


def print_phase_info(state: ConversationState):
    """Print current phase information"""
    phase_config = state.get_current_phase()

    if state.phase == "GREETING":
        print(f"\n[PHASE: {state.phase}]")
    elif state.phase == "ROUTE_SELECTION":
        print(f"\n[PHASE: {state.phase}]")
        if state.selected_route == "7" and not state.custom_route_description:
            print("Awaiting custom route description...")
        else:
            print("Choose your preferred storytelling approach (1-7)")
    elif "QUESTION" in state.phase:
        print(f"\n[PHASE: {state.phase}] - Question {state.question_count} of 5")
        print(f"Focus: {phase_config['description']}")
        if state.selected_route:
            route_info = state.get_route_info()
            if route_info:
                print(f"Route: {route_info['name']}")
    elif state.phase == "SYNTHESIS":
        print(f"\n[PHASE: {state.phase}]")
        print("Generating your story structure...")

    print("-" * 70)


def print_ai_message(message: str):
    """Print AI message with formatting"""
    print(f"\nAI: {message}\n")


def get_user_input() -> str:
    """Get user input with prompt"""
    return input("You: ").strip()
