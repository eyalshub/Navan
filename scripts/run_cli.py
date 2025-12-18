from app.orchestrator.orchestrator_agent import OrchestratorAgent


def run_cli():
    print("🧭 Travel Assistant CLI")
    print("Type 'exit' to quit\n")

    orchestrator = OrchestratorAgent()

    # Initial assistant message
    initial_message = orchestrator.get_initial_message()
    if initial_message:
        print(f"Assistant: {initial_message}\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("👋 Bye!")
            break

        try:
            response = orchestrator.handle_message(user_input)
            print(f"Assistant: {response}\n")
        except Exception as e:
            print("⚠️ Something went wrong. Please try again.\n")


if __name__ == "__main__":
    run_cli()
