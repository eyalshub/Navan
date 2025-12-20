# test_llm_conversation_responder.py

from app.llm_conversation_responder import LLMConversationResponder
from app.state.conversation_state import ConversationState
from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import AttractionsAgentOutput, AttractionItem


def test_llm_response_wikipedia():
    state = ConversationState()
    state.city = "Rome"
    state.subject_name = "Colosseum"
    state.last_executed_action = "wikipedia"

    agent_output = WikipediaExplainerOutput(
        explanation="The Colosseum is an ancient Roman amphitheatre...",
        followup_suggestions=["What else should I see in Rome?"],
        key_points=[
            "Built in 70–80 AD",
            "Hosted gladiator contests",
            "Located in Rome"
        ]
    )

    response = LLMConversationResponder.generate_response(
        user_input="Tell me more about the Colosseum",
        agent_output=agent_output,
        conversation_state=state,
    )

    print("Wikipedia Response:")
    print("TEXT:", response.text)
    print("FOLLOWUP:", response.followup_question)
    print("INTENT:", response.suggested_intent)
    print("====\n")


def test_llm_response_attractions():
    state = ConversationState()
    state.city = "Barcelona"
    state.preferences = ["museums"]
    state.last_executed_action = "attractions"

    agent_output = AttractionsAgentOutput(
        needs_clarification=False,
        clarification_question=None,
        attractions=[
            AttractionItem(name="Sagrada Familia", category="architecture", reason="iconic architecture by Gaudi", lat=0.0, lon=0.0),
            AttractionItem(name="Picasso Museum", category="art", reason="famous for its collection of Pablo Picasso's works", lat=0.0, lon=0.0),
        ]
    )

    response = LLMConversationResponder.generate_response(
        user_input="What museums can I visit in Barcelona?",
        agent_output=agent_output,
        conversation_state=state,
    )

    print("Attractions Response:")
    print("TEXT:", response.text)
    print("FOLLOWUP:", response.followup_question)
    print("INTENT:", response.suggested_intent)
    print("====\n")


if __name__ == "__main__":
    test_llm_response_wikipedia()
    test_llm_response_attractions()