# app/llm_conversation_responder.py

from typing import Optional, Union
from app.state.conversation_state import ConversationState
from app.agents.wikipedia_explainer_agent import WikipediaExplainerOutput
from app.agents.attractions_agent import AttractionsAgentOutput
from app.llm.client import call_llm
from app.llm.utils import load_prompt
from app.models.agent_response import AgentResponse


class LLMConversationResponder:
    """
    Generates a natural-sounding assistant response based on agent output
    and conversation state, using an LLM prompt.
    """

    SYSTEM_PROMPT = load_prompt("prompts/conversation.yaml")["system"]

    @classmethod
    def generate_response(
        cls,
        user_input: str,
        agent_output: Union[WikipediaExplainerOutput, AttractionsAgentOutput],
        conversation_state: ConversationState,
    ) -> AgentResponse:
        """
        Builds context and generates an assistant response via LLM.
        """

        # Build structured context for the LLM
        context = {
            "user_input": user_input,
            "agent_output": (
                agent_output.explanation if isinstance(agent_output, WikipediaExplainerOutput) else None
            ),
            "attractions": (
                [a.name for a in agent_output.attractions] if isinstance(agent_output, AttractionsAgentOutput) else []
            ),
            "city": conversation_state.city,
            "preferences": conversation_state.preferences,
            "subject_name": conversation_state.subject_name,
            "last_action": conversation_state.last_executed_action,
        }

        # Construct user prompt for LLM
        user_prompt = (
            f"The user said:\n{user_input}\n\n"
            f"Conversation context:\n{context}"
        )

        # Call the LLM
        llm_response = call_llm(
            system_prompt=cls.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        # Parse or fallback
        try:
            parsed = cls._parse_response(llm_response)
        except Exception:
            parsed = AgentResponse(text=llm_response.strip())

        return parsed

    @staticmethod
    def _parse_response(raw: str) -> AgentResponse:
        """
        Expects a structured LLM response with keys:
        TEXT: ...
        FOLLOWUP: ...
        INTENT: ...
        """

        text = followup = intent = None
        lines = raw.strip().splitlines()

        for line in lines:
            if line.startswith("TEXT:"):
                text = line.removeprefix("TEXT:").strip()
            elif line.startswith("FOLLOWUP:"):
                followup = line.removeprefix("FOLLOWUP:").strip()
            elif line.startswith("INTENT:"):
                intent = line.removeprefix("INTENT:").strip()

        return AgentResponse(
            text=text or raw.strip(),
            followup_question=followup or None,
            suggested_intent=intent or None,
        )
