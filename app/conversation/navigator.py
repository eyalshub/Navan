# app/conversation/navigator.py
from dataclasses import dataclass
from typing import Optional

from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import AttractionsAgentOutput


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
        if isinstance(agent_output, WikipediaExplainerOutput):
            return self._from_wikipedia(agent_output)

        if isinstance(agent_output, AttractionsAgentOutput):
            return self._from_attractions(agent_output)

        return NavigationResponse(
            text="I'm not sure how to proceed from here.",
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
            lines.append(
                f"{i}. {a.name} – {a.reason}"
            )

        text = "Here are a few places you might enjoy:\n\n" + "\n".join(lines)

        return NavigationResponse(
            text=text,
            next_question="Would you like to explore one of these places in more detail?",
            suggested_intent="deep_dive_place",
        )
