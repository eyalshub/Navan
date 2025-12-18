# scripts/test_attractions_agent.py
from app.agents.attractions_agent import (
    AttractionsAgent,
    AttractionsAgentInput,
)


def run_without_preferences():
    print("\n=== Attractions Agent – Test: No Preferences ===\n")

    agent = AttractionsAgent()

    input_data = AttractionsAgentInput(
        city="Barcelona",
        lat=41.4036,   # Sagrada Família
        lon=2.1744,
        preferences=None,
        radius_km=2,
    )

    result = agent.run(input_data)

    print("Needs clarification:", result.needs_clarification)
    print("Clarification question:")
    print(result.clarification_question)
    print("\n--- End Test ---\n")


def run_with_preferences():
    print("\n=== Attractions Agent – Test: With Preferences ===\n")

    agent = AttractionsAgent()

    input_data = AttractionsAgentInput(
        city="Barcelona",
        lat=41.4036,
        lon=2.1744,
        preferences=["culture", "food"],
        radius_km=2,
    )

    result = agent.run(input_data)

    print("Needs clarification:", result.needs_clarification)

    if result.attractions:
        print("\nRecommended Attractions:\n")
        for i, place in enumerate(result.attractions, 1):
            print(f"{i}. {place.name}")
            print(f"   Category: {place.category}")
            print(f"   Reason: {place.reason}")
            print(f"   Location: ({place.lat}, {place.lon})\n")
    else:
        print("No attractions returned.")

    print("\n--- End Test ---\n")


def main():
    run_without_preferences()
    run_with_preferences()


if __name__ == "__main__":
    main()
