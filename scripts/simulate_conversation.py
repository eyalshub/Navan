# scripts/simulate_conversation.py
from app.orchestrator.orchestrator_agent import OrchestratorAgent


def run_simulation(title: str, messages: list[str]):
    agent = OrchestratorAgent()

    print("\n" + "=" * 80)
    print(f"SIMULATION: {title}")
    print("=" * 80 + "\n")

    for i, msg in enumerate(messages, start=1):
        print(f"[Turn {i}] User: {msg}")
        response = agent.handle_message(msg)
        print(f"[Turn {i}] Assistant: {response}\n")


if __name__ == "__main__":

    # -------------------------------------------------
    # Simulation 1: Learn about a specific place (Rome)
    # -------------------------------------------------
    simulation_1 = [
        "Hi, I'm in Rome, Italy",
        "I'd like to learn about the Colosseum",
        "Yes",
        "Thanks",
        "What else should I see nearby?"
    ]

    # -------------------------------------------------
    # Simulation 2: Discover attractions + choose one (London)
    # -------------------------------------------------
    simulation_2 = [
        "Hi, I'm in London",
        "What attractions are nearby?",
        "Yes",
        "The British Museum",
        "Thanks"
    ]

    # -------------------------------------------------
    # Simulation 3: Simple discovery + navigation context
    # -------------------------------------------------
    simulation_3 = [
        "Hello, I'm visiting Rome",
        "What can I see near the Colosseum?",
        "Yes",
        "Tell me more about the Colosseum",
        "Sure"
    ]

    run_simulation("Learn about a specific place (Rome)", simulation_1)
    run_simulation("Discover attractions and choose one (London)", simulation_2)
    run_simulation("Discovery + explanation flow (Rome)", simulation_3)
