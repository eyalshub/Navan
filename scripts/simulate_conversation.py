from app.orchestrator.orchestrator_agent import OrchestratorAgent
from app.conversation.navigator import ConversationNavigator


def run_simulation(title: str, messages: list[str]):
    orchestrator = OrchestratorAgent()
    navigator = ConversationNavigator()

    print("\n" + "=" * 80)
    print(f"SIMULATION: {title}")
    print("=" * 80 + "\n")

    for i, msg in enumerate(messages, start=1):
        print(f"[Turn {i}] User: {msg}")

        # 1) Orchestrator decides what happens
        output = orchestrator.handle_message(msg)

        # 2) Navigator ALWAYS handles the output
        nav_response = navigator.navigate(output)

        print(f"[Turn {i}] Assistant: {nav_response.text}")

        if nav_response.next_question:
            print(f"→ {nav_response.next_question}")

        print()


if __name__ == "__main__":

    simulation_1 = [
        "Hi, I'm in Rome, Italy",
        "I'd like to learn about the Colosseum",
        "Thanks",
        "What else should I see nearby?",
    ]

    simulation_2 = [
        "Hi, I'm in London",
        "What attractions are nearby?",
        "Museums",
        "Thanks",
        "Tell me more about the British Museum",
    ]
    simulation_3 = [
        "Hello, I'm visiting Rome",
        "What can I see near the Colosseum?",
        "Food"
        "Tell me more about the Colosseum",
    ]

    run_simulation("Learn about a specific place (Rome)", simulation_1)
    run_simulation("Discover attractions (London)", simulation_2)
    run_simulation("Discovery + explanation flow (Rome)", simulation_3)
