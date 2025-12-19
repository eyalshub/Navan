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

    Contract:
    - run(...) returns WikipediaExplainerOutput (structured)
    - NEVER returns str (formatting belongs to the ConversationNavigator)
    """

    def __init__(self):
        self.prompt = load_prompt("prompts/wikipedia_explainer.yaml")

    # -------------------------------------------------
    # Public API (used by Orchestrator)
    # -------------------------------------------------

    def run(
        self,
        subject_name: str,
        city: Optional[str] = None,
        user_style: str = "friendly",
    ) -> WikipediaExplainerOutput:
        """
        Main execution entrypoint for the Orchestrator.
        Returns a structured WikipediaExplainerOutput.
        """

        wiki_data = get_wikipedia_summary(
            title=subject_name,
            city=city,
        )

        # If no reliable source -> return structured "not found"
        if not isinstance(wiki_data, dict) or not wiki_data.get("found"):
            return WikipediaExplainerOutput(
                explanation=f"Sorry, I couldn’t find reliable information about {subject_name}.",
                key_points=[],
                followup_suggestions=[],
            )

        raw_summary = wiki_data.get("summary")
        title = wiki_data.get("title") or subject_name

        if not raw_summary or not isinstance(raw_summary, str):
            return WikipediaExplainerOutput(
                explanation=f"Sorry, I couldn’t find reliable information about {subject_name}.",
                key_points=[],
                followup_suggestions=[],
            )

        input_data = WikipediaExplainerInput(
            title=title,
            raw_summary=raw_summary,
            user_style=user_style,
        )

        # LLM-based explanation (grounded)
        try:
            return self._explain(input_data)
        except Exception:
            # Defensive fallback: never crash orchestrator
            return WikipediaExplainerOutput(
                explanation=f"I found information about {subject_name}, but I couldn’t format it reliably right now.",
                key_points=[],
                followup_suggestions=[],
            )

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------

    def _build_query(self, subject_name: str, city: Optional[str]) -> str:
        """
        Optional disambiguation:
        if city exists and subject is not obviously a city itself,
        we can enrich the query slightly.
        """
        subject = (subject_name or "").strip()
        if not subject:
            return subject_name

        if city and city.strip():
            # This is safe and often helps Wikipedia resolve the right article.
            return f"{subject}, {city.strip()}"

        return subject

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
            temperature=0.2,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {e}\n{raw_response}")

        explanation = parsed.get("explanation")
        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(f"LLM JSON missing 'explanation': {parsed}")

        key_points = parsed.get("key_points", [])
        if not isinstance(key_points, list):
            key_points = []

        followups = parsed.get("followup_suggestions", [])
        if not isinstance(followups, list):
            followups = []

        # Normalize list items to strings
        key_points = [str(x).strip() for x in key_points if str(x).strip()]
        followups = [str(x).strip() for x in followups if str(x).strip()]

        return WikipediaExplainerOutput(
            explanation=explanation.strip(),
            key_points=key_points,
            followup_suggestions=followups,
        )
