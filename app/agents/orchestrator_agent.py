from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agents.attractions_agent import AttractionsAgent, AttractionsAgentInput
from app.agents.wikipedia_explainer_agent import (
    WikipediaExplainerAgent,
    WikipediaExplainerInput,
)
from app.conversation.navigator import ConversationNavigator
from app.tools.geoapify_client import GeoapifyClient
from app.tools.wikipedia import get_wikipedia_summary
from app.tools.geonames import get_points_of_interest


# ======================================================
# Conversation Memory (Short-Term)
# ======================================================

@dataclass
class ConversationState:
    has_greeted: bool = False

    last_city: Optional[str] = None
    last_country: Optional[str] = None
    last_place: Optional[str] = None

    last_lat: Optional[float] = None
    last_lon: Optional[float] = None

    last_intent: Optional[str] = None  # "attractions" | "explain" | "location"

    last_suggested_places: Optional[List[str]] = None
    focus_place: Optional[str] = None

    allow_followup_question: bool = False

    # Slot filling
    pending_slot: Optional[str] = None  # "city" | "country"
    last_preferences: Optional[List[str]] = None


# ======================================================
# Orchestrator Agent
# ======================================================

class OrchestratorAgent:
    """
    Deterministic, intent-driven conversation orchestrator.
    """

    def __init__(self):
        self.attractions_agent = AttractionsAgent()
        self.wikipedia_agent = WikipediaExplainerAgent()
        self.navigator = ConversationNavigator()
        self.geo_client = GeoapifyClient()
        self.state = ConversationState()

    # ==================================================
    # Public API
    # ==================================================

    def handle_message(self, user_message: str) -> str:
        text = (user_message or "").strip()
        if not text:
            return "Please tell me what you are looking for."

        # Greeting (once)
        if not self.state.has_greeted and self._is_greeting(text):
            self.state.has_greeted = True
            return self.get_initial_message()

        # 1️⃣ Slot filling has highest priority
        slot_response = self._handle_pending_slot(text)
        if slot_response is not None:
            return slot_response

        # 2️⃣ Extract entities & update memory
        extracted = self._extract_entities(text)
        self._update_memory(extracted)

        # 3️⃣ Detect intent
        intent = self._detect_intent(text)

        if intent == "location":
            return self._handle_location()

        if intent == "explain":
            return self._handle_explain()

        if intent == "attractions":
            return self._handle_attractions(text)

        return self._ask_minimal_clarification()

    # ==================================================
    # Slot Filling
    # ==================================================

    def _handle_pending_slot(self, text: str) -> Optional[str]:
        if self.state.pending_slot == "city":
            self.state.last_city = text.strip()
            self.state.pending_slot = None
            self.state.last_lat = None
            self.state.last_lon = None

            if self.state.last_intent == "attractions":
                return self._handle_attractions(text)

            return f"Got it — you're in {self.state.last_city}. What are you looking for?"

        if self.state.pending_slot == "country":
            self.state.last_country = text.strip()
            self.state.pending_slot = None
            self.state.last_lat = None
            self.state.last_lon = None

            if self.state.last_intent == "attractions":
                return self._handle_attractions(text)

            return f"Thanks — {self.state.last_city}, {self.state.last_country}. What would you like to do?"

        return None

    # ==================================================
    # Intent Detection (ORDER MATTERS)
    # ==================================================

    def _detect_intent(self, text: str) -> str:
        t = text.lower()

        # 1️⃣ Explicit selection from last suggested list
        if self.state.last_suggested_places:
            for place in self.state.last_suggested_places:
                if place.lower() in t:
                    self.state.last_place = place
                    self.state.last_intent = "explain"
                    return "explain"

        # 2️⃣ Location intent (HIGH PRIORITY)
        if self.state.focus_place and re.search(
            r"\b(where is|location|address|coordinates|how do i get there|exact location)\b",
            t,
        ):
            self.state.last_intent = "location"
            return "location"

        # 3️⃣ Explicit explain intent
        if re.search(
            r"\b(explain|tell me about|history of|what is|who is|background)\b",
            t,
        ):
            self.state.last_intent = "explain"
            return "explain"

        # 4️⃣ Implicit explain follow-up
        if self.state.focus_place and re.search(
            r"\b(what|which|how|menu|dishes)\b",
            t,
        ):
            self.state.last_intent = "explain"
            return "explain"

        # 5️⃣ Attractions intent
        if re.search(
            r"\b(restaurant|restaurants|food|eat|bar|cafe|museum|museums|"
            r"attraction|attractions|things to do|what to do|places to visit)\b",
            t,
        ):
            self.state.last_intent = "attractions"
            return "attractions"

        # 6️⃣ Generic continuation
        if re.search(r"\b(more|continue|details)\b", t):
            if self.state.last_intent:
                return self.state.last_intent

        return "unknown"

    # ==================================================
    # Attractions Flow
    # ==================================================

    def _handle_attractions(self, text: str) -> str:
        self.state.last_intent = "attractions"

        # 1️⃣ Preferences (dictionary-based only)
        extracted_prefs = self._extract_preferences(text)
        if extracted_prefs:
            self.state.last_preferences = extracted_prefs

        preferences = self.state.last_preferences
        if not preferences:
            return (
                "What kind of places are you looking for? "
                "(museums, food, art, parks, history, etc.)"
            )

        # 2️⃣ City required
        if not self.state.last_city:
            self.state.pending_slot = "city"
            return "Which city are you in?"

        # 3️⃣ Resolve coordinates
        if not self._ensure_location():
            if not self.state.last_country:
                self.state.pending_slot = "country"
                return (
                    f"I found the city '{self.state.last_city}', "
                    "but I need the country as well. Which country is it in?"
                )
            return f"I couldn't determine an exact location for {self.state.last_city}, {self.state.last_country}."

        # 4️⃣ Run AttractionsAgent
        agent_input = AttractionsAgentInput(
            city=self.state.last_city,
            lat=self.state.last_lat,
            lon=self.state.last_lon,
            preferences=preferences,
        )

        result = self.attractions_agent.run(agent_input)

        # 5️⃣ Update memory
        self.state.last_suggested_places = [a.name for a in result.attractions]
        self.state.focus_place = None
        self.state.allow_followup_question = False

        nav = self.navigator.navigate(result)
        return self._compose(nav)

    # ==================================================
    # Explain Flow
    # ==================================================

    def _handle_explain(self) -> str:
        self.state.last_intent = "explain"
        self.state.last_preferences = None  # 🔧 critical cleanup

        if not self.state.last_place:
            return "Which place would you like me to explain?"

        self.state.focus_place = self.state.last_place
        self.state.last_suggested_places = None
        self.state.allow_followup_question = True

        summary = (get_wikipedia_summary(self.state.last_place) or {}).get("summary")
        if not summary:
            return f"I could not find reliable information about {self.state.last_place}."

        agent_input = WikipediaExplainerInput(
            title=self.state.last_place,
            raw_summary=summary,
        )

        result = self.wikipedia_agent.run(agent_input)
        nav = self.navigator.navigate(result)
        return self._compose(nav)

    # ==================================================
    # Location Flow (GeoNames)
    # ==================================================

    def _handle_location(self) -> str:
        if not self.state.focus_place:
            return "Which place are you referring to?"

        if not self.state.last_city:
            return "I need the city to determine the exact location."

        # 1️⃣ Geoapify geocode – exact place lookup
        query = f"{self.state.focus_place}, {self.state.last_city}"
        if self.state.last_country:
            query += f", {self.state.last_country}"

        geo = self.geo_client.geocode(query, limit=1)
        features = geo.get("features", [])

        if features:
            coords = features[0]["geometry"]["coordinates"]
            props = features[0].get("properties", {})

            lat = coords[1]
            lon = coords[0]

            google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"

            return (
                f"📍 **{self.state.focus_place}**\n"
                f"Address: {props.get('formatted', 'N/A')}\n"
                f"Latitude: {lat}\n"
                f"Longitude: {lon}\n"
                f"🗺️ Google Maps: {google_maps_url}"
            )

        return (
            f"I couldn't find exact coordinates for **{self.state.focus_place}**, "
            f"but it is located in **{self.state.last_city}**."
        )


    # ==================================================
    # Entity Extraction
    # ==================================================

    def _extract_entities(self, text: str) -> Dict[str, Optional[str]]:
        entities = {"city": None, "country": None, "place": None}

        city_match = re.search(
            r"\b(?:in|visiting|traveling to)\s+([A-Za-zÀ-ÿ' -]{2,})",
            text,
            re.IGNORECASE,
        )
        if city_match:
            city = re.split(r"[,.;]| and | but ", city_match.group(1))[0]
            entities["city"] = city.strip()

        country_match = re.search(
            r"\b(?:in|from)\s+([A-Za-zÀ-ÿ' -]{2,})$",
            text,
            re.IGNORECASE,
        )
        if country_match and not entities["city"]:
            entities["country"] = country_match.group(1).strip()

        quoted = re.findall(r"['\"“”](.+?)['\"“”]", text)
        if quoted:
            entities["place"] = quoted[0].strip()

        return entities

    # ==================================================
    # Preferences Extraction (Controlled Vocabulary)
    # ==================================================

    def _extract_preferences(self, text: str) -> List[str]:
        t = text.lower()
        prefs = []

        if re.search(r"\b(museum|museums)\b", t):
            prefs.append("museum")
        if re.search(r"\b(food|restaurant|eat|bar|cafe)\b", t):
            prefs.append("food")
        if re.search(r"\b(art|gallery)\b", t):
            prefs.append("art")
        if re.search(r"\b(park|nature|hike)\b", t):
            prefs.append("nature")
        if re.search(r"\b(history|historic)\b", t):
            prefs.append("history")

        return list(dict.fromkeys(prefs))

    # ==================================================
    # Location Resolution
    # ==================================================

    def _ensure_location(self) -> bool:
        if self.state.last_lat and self.state.last_lon:
            return True

        if not self.state.last_city:
            return False

        query = self.state.last_city
        if self.state.last_country:
            query = f"{self.state.last_city}, {self.state.last_country}"

        geo = self.geo_client.geocode(query, limit=3)
        features = geo.get("features", [])
        if not features:
            return False

        coords = features[0]["geometry"]["coordinates"]
        self.state.last_lon = coords[0]
        self.state.last_lat = coords[1]
        return True

    # ==================================================
    # Memory Update
    # ==================================================

    def _update_memory(self, extracted: Dict[str, Optional[str]]) -> None:
        if extracted.get("city"):
            self.state.last_city = extracted["city"]
            self.state.last_lat = None
            self.state.last_lon = None

        if extracted.get("country"):
            self.state.last_country = extracted["country"]
            self.state.last_lat = None
            self.state.last_lon = None

        if extracted.get("place"):
            self.state.last_place = extracted["place"]

    # ==================================================
    # Utilities
    # ==================================================

    def _is_greeting(self, text: str) -> bool:
        return text.lower().startswith(("hi", "hello", "hey"))

    def _ask_minimal_clarification(self) -> str:
        if self.state.focus_place:
            return f"What would you like to know about {self.state.focus_place}?"
        if self.state.last_city:
            return f"What are you looking for in {self.state.last_city}?"
        return "What would you like to do?"

    def _compose(self, nav: Any) -> str:
        parts = []

        if getattr(nav, "text", None):
            parts.append(nav.text)

        if (
            self.state.allow_followup_question
            and self.state.last_intent == "explain"
            and getattr(nav, "next_question", None)
        ):
            parts.append(nav.next_question)
            self.state.allow_followup_question = False

        return "\n\n".join(parts)

    def get_initial_message(self) -> str:
        return (
            "Hi! I'm your travel assistant.\n"
            "Tell me where you are traveling and what you're looking for "
            "(restaurants, attractions, history, etc.)."
        )
