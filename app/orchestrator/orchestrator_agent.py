# app/orchestrator/orchestrator_agent.py
from __future__ import annotations

import re
from typing import Optional

from app.state.conversation_state import ConversationState, normalize_preferences
from app.orchestrator.extraction import extract_information

from app.agents.attractions_agent import (
    AttractionsAgent,
    AttractionsAgentInput,
    AttractionsAgentOutput,
)
from app.agents.wikipedia_explainer_agent import (
    WikipediaExplainerAgent,
    WikipediaExplainerOutput,
)

from app.conversation.slot_request import SlotRequestOutput
from app.tools.geoapify_client import GeoapifyClient


class OrchestratorAgent:
    """
    Deterministic conversation orchestrator.

    Contract:
    ---------
    handle_message() MUST return exactly one of:
    - SlotRequestOutput
    - WikipediaExplainerOutput
    - AttractionsAgentOutput

    NEVER returns:
    - str
    - None
    """

    GOAL_DISCOVER = "discover_attractions"
    GOAL_LEARN = "learn_about_place"

    ACTION_ATTRACTIONS = "run_attractions"
    ACTION_WIKIPEDIA = "explain_subject"

    def __init__(self):
        self.state = ConversationState()
        self.attractions_agent = AttractionsAgent()
        self.wikipedia_agent = WikipediaExplainerAgent()
        self.geo_client = GeoapifyClient()

    # =================================================
    # Public API
    # =================================================

    def handle_message(self, user_message: str):
        self.state.increment_turn()

        user_text = (user_message or "").strip()
        user_lower = user_text.lower()

        # 1) Extract + update state (LLM extraction can be noisy)
        extracted = extract_information(user_text)
        self.state.update_from_extraction(extracted)
        # 🔴 If user intent is DISCOVER, old subject must not leak
        if self.state.user_goal == self.GOAL_DISCOVER:
            self.state.subject_name = None
            self.state.subject_type = None
        # 2) Deterministic enrichments (fallbacks)
        self._fallback_city_parse(user_text)
        self._fallback_subject_parse(user_text)

        # 3) Conservative goal inference if missing
        if not self.state.user_goal:
            if self._looks_like_discover_request(user_lower):
                self.state.user_goal = self.GOAL_DISCOVER
                self.state.goal_confidence = max(self.state.goal_confidence, 0.7)
            elif self._looks_like_learn_request(user_lower):
                self.state.user_goal = self.GOAL_LEARN
                self.state.goal_confidence = max(self.state.goal_confidence, 0.7)

        # 4) If user explicitly asks "tell me about X" -> force LEARN even if we were in DISCOVER
        if self._looks_like_learn_request(user_lower) and self.state.subject_name:
            self.state.user_goal = self.GOAL_LEARN

        # 🔴 EXIT RAMP: learn about a specific place from attractions
        learn_subject = self._looks_like_learn_about_place(user_text)
        if learn_subject:
            self.state.subject_name = learn_subject
            self.state.user_goal = self.GOAL_LEARN
            return self._run_wikipedia()

        # 5) Route flows
        if self.state.user_goal == self.GOAL_LEARN:
            return self._handle_learn_flow(user_lower)

        if self.state.user_goal == self.GOAL_DISCOVER:
            return self._handle_discover_flow(user_lower, user_text)

        # 6) No action -> clarify
        return SlotRequestOutput(slot="clarify")

    # =================================================
    # Flow handlers
    # =================================================

    def _handle_learn_flow(self, user_lower: str):
        if not self.state.has_subject():
            return SlotRequestOutput(slot="subject")

        # Avoid loops on acknowledgements
        if self._looks_like_ack(user_lower):
            return SlotRequestOutput(slot="clarify")

        # Avoid repeating Wikipedia unless user asked again
        if (
            self.state.last_executed_action == self.ACTION_WIKIPEDIA
            and not self._looks_like_learn_request(user_lower)
        ):
            return SlotRequestOutput(slot="clarify")

        return self._run_wikipedia()

    def _handle_discover_flow(self, user_lower: str, user_text: str):
        # City must exist
        if not self.state.city:
            return SlotRequestOutput(slot="city")

        # If preferences missing, try to treat the user's message as a preference answer
        if not self.state.preferences and not self._looks_like_discover_request(user_lower):
            # Example: user answers "Museums" or "Food"
            prefs = normalize_preferences([user_text])
            for p in prefs:
                if p not in self.state.preferences:
                    self.state.preferences.append(p)

        # Still missing preferences -> ask
        if not self.state.preferences:
            return SlotRequestOutput(slot="preference")

        # Avoid loops on acknowledgements after we already executed
        if self._looks_like_ack(user_lower) and self.state.last_executed_action == self.ACTION_ATTRACTIONS:
            return SlotRequestOutput(slot="clarify")

        # If we just executed attractions and user didn't ask again -> don't re-run
        if (
            self.state.last_executed_action == self.ACTION_ATTRACTIONS
            and not self._looks_like_discover_request(user_lower)
        ):
            return SlotRequestOutput(slot="clarify")

        return self._run_attractions()

    # =================================================
    # Execution
    # =================================================

    def _run_attractions(self) -> AttractionsAgentOutput:
        # Resolve coordinates if missing
        if self.state.latitude is None or self.state.longitude is None:
            geo = self.geo_client.geocode(self.state.city, limit=1)
            if geo and geo.get("features"):
                coords = geo["features"][0]["geometry"]["coordinates"]
                self.state.longitude = coords[0]
                self.state.latitude = coords[1]

        if self.state.latitude is None or self.state.longitude is None:
            return AttractionsAgentOutput(
                needs_clarification=True,
                clarification_question=f"I couldn't determine coordinates for {self.state.city}. Which area/neighborhood are you in?",
                attractions=[],
            )

        result = self.attractions_agent.run(
            AttractionsAgentInput(
                city=self.state.city,
                lat=self.state.latitude,
                lon=self.state.longitude,
                preferences=self.state.preferences,
            )
        )

        self.state.last_executed_action = self.ACTION_ATTRACTIONS
        self._soft_reset_after_action()
        return result

    def _run_wikipedia(self) -> WikipediaExplainerOutput:
        result = self.wikipedia_agent.run(
            subject_name=self.state.subject_name,
            city=self.state.city,
        )

        self.state.last_executed_action = self.ACTION_WIKIPEDIA
        self._soft_reset_after_action()
        return result

    def _soft_reset_after_action(self) -> None:
        """
        Reset ONLY short-term signals.
        Keep goal & subject so the conversation can continue naturally.
        """
        self.state.goal_confidence = 0.0
        self.state.preferences = []
    # =================================================
    # Deterministic fallbacks
    # =================================================

    def _fallback_city_parse(self, user_text: str) -> None:
        """
        If extractor missed city, catch simple patterns:
        - "I'm in Rome"
        - "visiting London"
        - "in New York"
        """
        if self.state.city:
            return

        text = user_text.strip()

        # in <city>
        m = re.search(r"\b(?:i am|i'm)?\s*(?:in)\s+([A-Z][A-Za-z\s\-']+)", text)
        if m:
            self.state.city = m.group(1).strip().rstrip(".!,")
            return

        # visiting <city>
        m = re.search(r"\bvisiting\s+([A-Z][A-Za-z\s\-']+)", text, flags=re.IGNORECASE)
        if m:
            self.state.city = m.group(1).strip().rstrip(".!,")
            return

    def _fallback_subject_parse(self, user_text: str) -> None:
        """
        If extractor missed subject, catch:
        - "tell me more about X"
        - "learn about X"
        """
        text = user_text.strip()

        patterns = [
            r"\btell me more about\s+(.+)$",
            r"\blearn about\s+(.+)$",
            r"\bexplain\s+(.+)$",
        ]
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                candidate = m.group(1).strip().rstrip(".!,")
                if candidate:
                    self.state.subject_name = candidate
                return

    # =================================================
    # Text heuristics
    # =================================================

    def _looks_like_ack(self, text: str) -> bool:
        t = text.strip()
        return t in {
            "thanks", "thank you", "thx",
            "ok", "okay", "cool", "great", "nice",
            "awesome", "perfect", "got it", "alright",
        }

    def _looks_like_learn_request(self, text: str) -> bool:
        learn_triggers = (
            "learn about", "tell me about", "tell me more about",
            "explain", "what is", "who is", "history of",
            "more about", "details about",
        )
        return any(t in text for t in learn_triggers)

    def _looks_like_discover_request(self, text: str) -> bool:
        discover_triggers = (
            "attractions", "things to do", "what to do", "activities",
            "nearby", "around here", "what else should i see",
            "what can i see", "recommend", "recommendations",
            "places to visit", "points of interest",
        )
        return any(t in text for t in discover_triggers)



    def _looks_like_learn_about_place(self, text: str) -> Optional[str]:
        """
        Detect requests like:
        - 'tell me about X'
        - 'teach me about X'
        - 'learn about X'
        Returns the extracted subject if found.
        """
        patterns = [
            r"tell me about\s+(.+)",
            r"teach me about\s+(.+)",
            r"learn about\s+(.+)",
            r"explain\s+(.+)",
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".!,")
        return None
