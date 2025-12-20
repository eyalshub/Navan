# scripts/run_cli.py

from app.orchestrator.orchestrator_agent import OrchestratorAgent
from app.conversation.navigator import ConversationNavigator


def run_cli():
    print("🧭 Travel Assistant CLI")
    print("Type 'exit' to quit\n")

    orchestrator = OrchestratorAgent()
    navigator = ConversationNavigator()

    # ✅ Static greeting
    print(
        "Assistant: Hi! 👋 I'm your travel assistant.\n"
        "You can tell me where you are, ask about places,\n"
        "or explore attractions nearby.\n"
    )

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("👋 Bye!")
            break

        try:
            # 1️⃣ Orchestrator decides
            output = orchestrator.handle_message(user_input)

            # 2️⃣ Navigator renders UX
            nav_response = navigator.navigate(output)

            # Print assistant response
            print(f"\nAssistant: {nav_response.text}")
            if nav_response.next_question:
                print(f"→ {nav_response.next_question}")
            print()

        except Exception as e:
            print("⚠️ Something went wrong. Please try again.\n")
            raise e


if __name__ == "__main__":
    run_cli()
