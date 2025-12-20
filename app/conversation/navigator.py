# app/conversation/navigator.py
from dataclasses import dataclass
from typing import Optional, Union

from app.models.agent_response import AgentResponse
from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import AttractionsAgentOutput
from app.conversation.slot_request import SlotRequestOutput


@dataclass
class NavigationResponse:
    text: str
    next_question: Optional[str] = None


class ConversationNavigator:
    def navigate(
        self,
        output: Union[
            WikipediaExplainerOutput,
            AttractionsAgentOutput,
            SlotRequestOutput,
            AgentResponse,
            None
        ],
    ) -> NavigationResponse:
        # print("[DEBUG] navigator got type:", type(output))
        # print("[DEBUG] expected AgentResponse:", AgentResponse)       
        # ✅ THIS WILL NOW WORK
        if isinstance(output, AgentResponse):
            return NavigationResponse(
                text=output.text,
                next_question=output.followup_question,
            )

        if isinstance(output, WikipediaExplainerOutput):
            return NavigationResponse(text=output.text)

        if isinstance(output, AttractionsAgentOutput):
            return NavigationResponse(text=output.text)

        if isinstance(output, SlotRequestOutput):
            return NavigationResponse(
                text=output.prompt,
                next_question=output.hint,
            )

        return NavigationResponse(
            text="I'm not sure how to proceed from here."
        )
