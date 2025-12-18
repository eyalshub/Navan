import json
from dataclasses import dataclass
from typing import List

from app.llm.client import call_llm
from app.llm.utils import load_prompt


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
    Transforms a raw Wikipedia summary into a user-friendly explanation.
    """

    def __init__(self):
        self.prompt = load_prompt("prompts/wikipedia_explainer.yaml")

    def run(self, input: WikipediaExplainerInput) -> WikipediaExplainerOutput:
        if not input.raw_summary.strip():
            raise ValueError("Empty raw_summary")

        system_prompt = self.prompt["system"]

        user_prompt = self.prompt["user"] \
            .replace("{{ title }}", input.title) \
            .replace("{{ raw_summary }}", input.raw_summary) \
            .replace("{{ user_style }}", input.user_style)

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
