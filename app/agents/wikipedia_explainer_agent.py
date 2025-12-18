# app/agents/wikipedia_explainer_agent.py
import json
from dataclasses import dataclass
from typing import List, Optional

from app.llm.client import call_llm
from app.llm.utils import load_prompt
from app.tools.wikipedia import get_wikipedia_summary


@dataclass
class WikipediaExplainerInput:
    title: str
    raw_summary: str
    user_style: str = "friendly"


@dataclass
class WikipediaExplainerOutput:
    explanation: str
    key_points: List[str]
    followup_suggestions: List[str]


class WikipediaExplainerAgent:
    """
    Explains a place using Wikipedia as a grounded knowledge source.
    Fully self-contained execution agent.
    """

    def __init__(self):
        self.prompt = load_prompt("prompts/wikipedia_explainer.yaml")

    # -------------------------------------------------
    # Public API (used by Orchestrator)
    # -------------------------------------------------

    def run(self, subject_name: str, city: Optional[str] = None) -> str:
        """
        Main execution entrypoint for the Orchestrator.
        Keeps the agent logic intact by normalizing Wikipedia output.
        """

        query = subject_name

        wiki_data = get_wikipedia_summary(query)

        # Normalize Wikipedia tool output -> raw summary string
        if not isinstance(wiki_data, dict) or not wiki_data.get("found"):
            return f"Sorry, I couldn’t find reliable information about {subject_name}."

        raw_summary = wiki_data.get("summary")

        if not raw_summary or not isinstance(raw_summary, str):
            return f"Sorry, I couldn’t find reliable information about {subject_name}."

        input_data = WikipediaExplainerInput(
            title=wiki_data.get("title") or subject_name,
            raw_summary=raw_summary,
        )

        output = self._explain(input_data)

        response = output.explanation

        if output.key_points:
            response += "\n\nKey highlights:\n"
            for point in output.key_points:
                response += f"- {point}\n"

        return response.strip()

    # -------------------------------------------------
    # Internal logic (existing behavior)
    # -------------------------------------------------

    def _explain(self, input: WikipediaExplainerInput) -> WikipediaExplainerOutput:
        if not input.raw_summary.strip():
            raise ValueError("Empty raw_summary")

        system_prompt = self.prompt["system"]

        user_prompt = (
            self.prompt["user"]
            .replace("{{ title }}", input.title)
            .replace("{{ raw_summary }}", input.raw_summary)
            .replace("{{ user_style }}", input.user_style)
        )

        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM did not return valid JSON:\n{raw_response}")

        return WikipediaExplainerOutput(
            explanation=parsed["explanation"],
            key_points=parsed.get("key_points", []),
            followup_suggestions=parsed.get("followup_suggestions", []),
        )
