# app/agents/attractions_agent.py
import json
from dataclasses import dataclass
from typing import List, Optional

from app.llm.client import call_llm
from app.llm.utils import load_prompt
from app.tools.geoapify_client import GeoapifyClient


# ======================================================
# Data models
# ======================================================

@dataclass
class AttractionsAgentInput:
    city: str
    lat: float
    lon: float
    preferences: Optional[List[str]]
    radius_km: int = 3


@dataclass
class AttractionItem:
    name: str
    category: str
    reason: str
    lat: float
    lon: float


@dataclass
class AttractionsAgentOutput:
    needs_clarification: bool
    clarification_question: Optional[str]
    attractions: List[AttractionItem]


# ======================================================
# Preference → Geoapify category mapping
# ======================================================

CATEGORY_MAP = {
    "food": "catering.restaurant",
    "culture": "entertainment.culture",
    "museum": "entertainment.museum",
    "art": "entertainment.culture.gallery",
    "park": "leisure.park",
    "nature": "natural",
    "history": "tourism.attraction",
    "sightseeing": "tourism.sights",
}

# ======================================================
# Agent implementation
# ======================================================

class AttractionsAgent:
    """
    Suggests and ranks nearby attractions based on user preferences
    and location. Uses Geoapify for raw places and an LLM for
    clarification, ranking, and explanation.
    """

    def __init__(self):
        self.prompt = load_prompt("prompts/attractions_agent.yaml")
        self.geo_client = GeoapifyClient()

    def run(self, input: AttractionsAgentInput) -> AttractionsAgentOutput:
        # --------------------------------------------------
        # Basic validation
        # --------------------------------------------------
        if not input.city or input.lat is None or input.lon is None:
            raise ValueError("AttractionsAgentInput missing city or coordinates")

        # --------------------------------------------------
        # Clarification FIRST (no API calls)
        # --------------------------------------------------
        if not input.preferences:
            return self._ask_for_clarification(input)

        # Normalize preferences (lowercase, strip)
        normalized_prefs = [
            p.lower().strip() for p in input.preferences if p.strip()
        ]

        if not normalized_prefs:
            return self._ask_for_clarification(input)

        # --------------------------------------------------
        # Fetch nearby places (Geoapify)
        # --------------------------------------------------
        places = self._fetch_places(
            lat=input.lat,
            lon=input.lon,
            preferences=normalized_prefs,
            radius_km=input.radius_km,
        )

        # If nothing was found, do not waste an LLM call
        if not places:
            return AttractionsAgentOutput(
                needs_clarification=False,
                clarification_question=None,
                attractions=[],
            )

        # --------------------------------------------------
        # LLM ranking & explanation
        # --------------------------------------------------
        system_prompt = self.prompt["system"]
        user_prompt = (
            self.prompt["user"]
            .replace("{{ city }}", input.city)
            .replace("{{ lat }}", str(input.lat))
            .replace("{{ lon }}", str(input.lon))
            .replace("{{ preferences }}", ", ".join(normalized_prefs))
            .replace("{{ radius_km }}", str(input.radius_km))
            .replace("{{ places }}", json.dumps(places, ensure_ascii=False))
        )

        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            raise ValueError(
                f"LLM response is not valid JSON:\n{raw_response}"
            )

        attractions: List[AttractionItem] = []
        for item in parsed.get("attractions", []):
            try:
                attractions.append(
                    AttractionItem(
                        name=item.get("name", "Unknown"),
                        category=item.get("category", ""),
                        reason=item.get("reason", ""),
                        lat=item["lat"],
                        lon=item["lon"],
                    )
                )
            except KeyError:
                # Skip malformed items
                continue

        return AttractionsAgentOutput(
            needs_clarification=parsed.get("needs_clarification", False),
            clarification_question=parsed.get("clarification_question"),
            attractions=attractions,
        )

    # ======================================================
    # Internal helpers
    # ======================================================

    def _ask_for_clarification(
        self, input: AttractionsAgentInput
    ) -> AttractionsAgentOutput:
        """
        Ask a single clarification question via LLM
        (no external API calls).
        """
        system_prompt = self.prompt["system"]
        user_prompt = (
            self.prompt["user"]
            .replace("{{ city }}", input.city)
            .replace("{{ lat }}", str(input.lat))
            .replace("{{ lon }}", str(input.lon))
            .replace("{{ preferences }}", "not specified")
            .replace("{{ radius_km }}", str(input.radius_km))
            .replace("{{ places }}", "[]")
        )

        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            raise ValueError(
                f"LLM clarification response is not valid JSON:\n{raw_response}"
            )

        return AttractionsAgentOutput(
            needs_clarification=True,
            clarification_question=parsed.get("clarification_question"),
            attractions=[],
        )

    def _fetch_places(
        self,
        lat: float,
        lon: float,
        preferences: List[str],
        radius_km: int,
    ):
        """
        Adapter over GeoapifyClient.places().
        Converts agent-level preferences into Geoapify categories
        and normalizes the response into a simple list.
        """
        category_strings = []

        for pref in preferences:
            mapped = CATEGORY_MAP.get(pref)
            if mapped:
                category_strings.append(mapped)

        if not category_strings:
            return []

        categories = ",".join(category_strings)

        raw = self.geo_client.places(
            categories=categories,
            lat=lat,
            lon=lon,
            radius=radius_km * 1000,  # meters
            limit=15,
            named_only=True,
        )

        features = raw.get("features", [])

        normalized = []
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])

            if len(coords) != 2:
                continue

            normalized.append(
                {
                    "name": props.get("name", "Unknown"),
                    "category": ", ".join(props.get("categories", [])),
                    "lat": coords[1],
                    "lon": coords[0],
                }
            )

        return normalized
