# app/conversation/navigator.py
from dataclasses import dataclass
from typing import Optional

from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import AttractionsAgentOutput
from app.conversation.slot_request import SlotRequestOutput


@dataclass
class NavigationResponse:
    text: str
    next_question: Optional[str] = None
    suggested_intent: Optional[str] = None


class ConversationNavigator:
    """
    Decides how to present agent output to the user
    and how to guide the conversation forward.
    """

    def navigate(self, agent_output) -> NavigationResponse:
        if isinstance(agent_output, SlotRequestOutput):
            return self._from_slot_request(agent_output)

        if isinstance(agent_output, WikipediaExplainerOutput):
            return self._from_wikipedia(agent_output)

        if isinstance(agent_output, AttractionsAgentOutput):
            return self._from_attractions(agent_output)

        return NavigationResponse(
            text="I'm not sure how to proceed from here.",
        )

    # -------------------------
    # Slot request flow
    # -------------------------

    def _from_slot_request(
        self, output: SlotRequestOutput
    ) -> NavigationResponse:
        if output.slot == "city":
            return NavigationResponse(
                text="Which city are you in?",
                suggested_intent="provide_city",
            )

        if output.slot == "preference":
            return NavigationResponse(
                text="What kind of places are you interested in? Museums, food, nature?",
                suggested_intent="clarify_preferences",
            )
        if output.slot == "clarify":
            return NavigationResponse(
                text="Sure — what would you like to do next?",
                next_question="For example: 'attractions nearby', or 'tell me about the Colosseum'.",
                suggested_intent="clarify",
            )
        return NavigationResponse(
            text="Could you tell me a bit more?",
        )

    # -------------------------
    # Wikipedia flow
    # -------------------------

    def _from_wikipedia(
        self, output: WikipediaExplainerOutput
    ) -> NavigationResponse:
        text = output.explanation

        next_question = None
        if output.followup_suggestions:
            next_question = output.followup_suggestions[0]

        return NavigationResponse(
            text=text,
            next_question=next_question,
            suggested_intent="explore_more",
        )

    # -------------------------
    # Attractions flow
    # -------------------------

    def _from_attractions(
        self, output: AttractionsAgentOutput
    ) -> NavigationResponse:
        if output.needs_clarification:
            return NavigationResponse(
                text=output.clarification_question,
                suggested_intent="clarify_preferences",
            )

        lines = []
        for i, a in enumerate(output.attractions[:3], 1):
            lines.append(f"{i}. {a.name} – {a.reason}")

        text = "Here are a few places you might enjoy:\n\n" + "\n".join(lines)

        return NavigationResponse(
            text=text,
            next_question="You can say a number to explore one of these places in more detail.",
            suggested_intent="deep_dive_place",
        )
