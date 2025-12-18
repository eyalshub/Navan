from app.conversation.navigator import ConversationNavigator
from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import (
    AttractionsAgentOutput,
    AttractionItem,
)


def test_wikipedia_flow():
    print("\n=== Navigator Test – WikipediaExplainerOutput ===\n")

    wiki_output = WikipediaExplainerOutput(
        explanation=(
            "The Sagrada Família is a church in Barcelona that has been under "
            "construction for many years. It was designed by Antoni Gaudí and "
            "is considered one of the most unique religious buildings in the world."
        ),
        key_points=[
            "Located in Barcelona",
            "Designed by Antoni Gaudí",
            "Still under construction",
        ],
        followup_suggestions=[
            "Would you like to know what makes Gaudí’s design unique?",
            "Are you interested in the history behind its construction?",
        ],
    )

    navigator = ConversationNavigator()
    response = navigator.navigate(wiki_output)

    print("[TEXT]")
    print(response.text)

    print("\n[NEXT QUESTION]")
    print(response.next_question)

    print("\n[SUGGESTED INTENT]")
    print(response.suggested_intent)


def test_attractions_flow():
    print("\n=== Navigator Test – AttractionsAgentOutput ===\n")

    attractions_output = AttractionsAgentOutput(
        needs_clarification=False,
        clarification_question=None,
        attractions=[
            AttractionItem(
                name="Park Güell",
                category="park",
                reason="A colorful public park designed by Antoni Gaudí",
                lat=41.4145,
                lon=2.1527,
            ),
            AttractionItem(
                name="Casa Batlló",
                category="architecture",
                reason="One of Gaudí’s most famous modernist buildings",
                lat=41.3917,
                lon=2.1649,
            ),
            AttractionItem(
                name="La Pedrera",
                category="architecture",
                reason="A unique residential building with a sculptural façade",
                lat=41.3954,
                lon=2.1619,
            ),
        ],
    )

    navigator = ConversationNavigator()
    response = navigator.navigate(attractions_output)

    print("[TEXT]")
    print(response.text)

    print("\n[NEXT QUESTION]")
    print(response.next_question)

    print("\n[SUGGESTED INTENT]")
    print(response.suggested_intent)


def test_attractions_clarification():
    print("\n=== Navigator Test – Attractions Clarification ===\n")

    attractions_output = AttractionsAgentOutput(
        needs_clarification=True,
        clarification_question="What type of attractions are you interested in?",
        attractions=[],
    )

    navigator = ConversationNavigator()
    response = navigator.navigate(attractions_output)

    print("[TEXT]")
    print(response.text)

    print("\n[SUGGESTED INTENT]")
    print(response.suggested_intent)


if __name__ == "__main__":
    test_wikipedia_flow()
    test_attractions_flow()
    test_attractions_clarification()

    print("\n=== Navigator Tests Completed ===\n")
