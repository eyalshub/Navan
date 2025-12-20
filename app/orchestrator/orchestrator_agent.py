# app/orchestrator/orchestrator_agent.py
from __future__ import annotations

from typing import Optional

from app.state.conversation_state import ConversationState
from app.orchestrator.extraction import extract_information
from app.llm_conversation_responder import LLMConversationResponder

from app.agents.attractions_agent import (
    AttractionsAgent,
    AttractionsAgentInput,
)

from app.agents.wikipedia_explainer_agent import (
    WikipediaExplainerAgent,
)

from app.models.agent_response import AgentResponse
from app.tools.geoapify_client import GeoapifyClient


class OrchestratorAgent:
    """
    Central conversation orchestrator.

    Responsibilities:
    - Extract structured intent & entities using LLM
    - Maintain conversation state
    - Decide which agent to run
    - Return a clean AgentResponse (text only – UX handled elsewhere)
    """

    def __init__(self):
        self.state = ConversationState()
        self.attractions_agent = AttractionsAgent()
        self.wikipedia_agent = WikipediaExplainerAgent()
        self.geo_client = GeoapifyClient()

    # ======================================================
    # Public API
    # ======================================================

    def handle_message(self, user_input: str) -> AgentResponse:
        print("=" * 60)
        # print(f"[DEBUG] Turn #{self.state.turn_count + 1} | User: {user_input}")

        # --------------------------------------------------
        # Step 1: LLM-based extraction
        # --------------------------------------------------
        extracted = extract_information(user_input)
        # print("[DEBUG] extracted=", extracted)

        self.state.update_from_extraction(extracted)
        # print("[DEBUG] state_after_extraction=", self.state)

        # --------------------------------------------------
        # Step 2: Decide which action to take
        # --------------------------------------------------
        action = self._decide_action()
        self.state.last_executed_action = action
        # print("[DEBUG] decided_action=", action)

        # --------------------------------------------------
        # Step 3: Early fallback (no clear action yet)
        # --------------------------------------------------
        if not action:
            self.state.turn_count += 1
            return AgentResponse(
                text=(
                    f"Hi there! "
                    f"{f'It looks like you are in {self.state.city}. ' if self.state.city else ''}"
                    f"What would you like to do next? "
                    f"I can recommend attractions or explain a specific place."
                )
            )

        # --------------------------------------------------
        # Step 4: Run the selected agent
        # --------------------------------------------------
        agent_output = None

        if action == "wikipedia":
            if not self.state.subject_name:
                self.state.turn_count += 1
                return AgentResponse(
                    text="Which place would you like to learn about?"
                )

            agent_output = self.wikipedia_agent.run(
                subject_name=self.state.subject_name,
                city=self.state.city,
            )

        elif action == "attractions":
            if not self.state.city:
                self.state.turn_count += 1
                return AgentResponse(
                    text="Could you tell me which city you are in?"
                )

            # Ensure coordinates exist
            if self.state.latitude is None or self.state.longitude is None:
                coords = self._geocode(self.state.city)
                if not coords:
                    self.state.turn_count += 1
                    return AgentResponse(
                        text=f"I couldn't find the location for {self.state.city}. Could you clarify?"
                    )
                self.state.latitude, self.state.longitude = coords

            agent_output = self.attractions_agent.run(
                AttractionsAgentInput(
                    city=self.state.city,
                    lat=self.state.latitude,
                    lon=self.state.longitude,
                    preferences=self.state.preferences,
                )
            )

        # --------------------------------------------------
        # Step 5: Natural language response
        # --------------------------------------------------
        response = LLMConversationResponder.generate_response(
            user_input=user_input,
            agent_output=agent_output,
            conversation_state=self.state,
        )

        self.state.turn_count += 1
        return response

    # ======================================================
    # Decision Logic
    # ======================================================

    def _decide_action(self) -> Optional[str]:
        """
        Decide which agent should handle the request.
        This logic assumes extraction is already normalized.
        """
        goal = self.state.user_goal
        subject = self.state.subject_name
        city = self.state.city
        prefs = self.state.preferences

        if goal == "learn_about_place" and subject:
            return "wikipedia"

        if goal == "discover_attractions" and city:
            return "attractions"

        if goal == "get_recommendations" and city:
            return "attractions"

        if subject:
            return "wikipedia"

        return None

    # ======================================================
    # Utilities
    # ======================================================

    def _geocode(self, city: str) -> Optional[tuple[float, float]]:
        """
        Convert city name into (lat, lon).
        """
        geo = self.geo_client.geocode(city, limit=1)
        features = geo.get("features", [])
        if not features:
            return None

        coords = features[0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
