# scripts/simulate_conversation.py

from app.orchestrator.orchestrator_agent import OrchestratorAgent
from app.models.agent_response import AgentResponse


def run_simulation(title: str, messages: list[str]):
    agent = OrchestratorAgent()

    print("\n" + "=" * 80)
    print(f"SIMULATION: {title}")
    print("=" * 80 + "\n")

    for i, msg in enumerate(messages, start=1):
        print(f"[Turn {i}] User: {msg}")
        response: AgentResponse = agent.handle_message(msg)
        print(f"[Turn {i}] Assistant: {response.text}\n")

        # Optional extras (cards, suggestions)
        if hasattr(response, "cards") and response.cards:
            print("[Cards]")
            for card in response.cards:
                print(f"- {card}")
            print()

        if hasattr(response, "suggestions") and response.suggestions:
            print("[Suggestions]")
            for s in response.suggestions:
                print(f"- {s}")
            print()


if __name__ == "__main__":
    simulations = [
        (
            "Learn about a specific place (Rome)",
            [
                "Hi, I'm in Rome, Italy",
                "I'd like to learn about the Colosseum",
                "Thanks",
                "What else should I see nearby?"
            ]
        ),
        (
            "Learn about a specific place (Paris)",
            [
                "Hi, I'm in Paris",
                "I love history and architecture",
                "Can you tell me about the Eiffel Tower?",
                "What else should I see nearby?",
                "Thanks!"
            ]
        ),
        (
            "Museum explorer (London)",
            [
                "Hey, I'm visiting London",
                "I'm interested in museums",
                "Tell me about the British Museum",
                "What other museums are nearby?"
            ]
        ),
        (
            "Art and Architecture (Barcelona)",
            [
                "Just landed in Barcelona!",
                "I'm into art and cool architecture",
                "Can you explain Sagrada Familia?",
                "Anything else interesting around there?"
            ]
        )
    ]

    for title, messages in simulations:
        run_simulation(title, messages)
