# app/orchestrator/orchestrator_agent.py
# app/orchestrator/orchestrator_agent.py
from typing import Optional
from urllib.parse import quote_plus

from app.state.conversation_state import ConversationState
from app.orchestrator.extraction import extract_information

from app.llm.client import call_llm
from app.llm.utils import load_prompt

from app.agents.attractions_agent import AttractionsAgent, AttractionsAgentInput
from app.agents.wikipedia_explainer_agent import WikipediaExplainerAgent
from app.tools.geoapify_client import GeoapifyClient


# =========================
# Prompts
# =========================

CONVERSATION_PROMPT = load_prompt("prompts/conversation.yaml")["system"]


class OrchestratorAgent:
    """
    Central conversation orchestrator.

    Responsibilities:
    - Manage natural conversation via LLM
    - Extract structured information from user input
    - Maintain deterministic conversation state
    - Decide when to propose and execute actions
    """

    def __init__(self):
        self.state = ConversationState()
        self.attractions_agent = AttractionsAgent()
        self.wikipedia_agent = WikipediaExplainerAgent()
        self.geo_client = GeoapifyClient()

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def handle_message(self, user_message: str) -> str:
        self.state.increment_turn()

        print("\n" + "=" * 60)
        print(f"[DEBUG] Turn #{self.state.turn_count} | User: {user_message}")

        # 1) Handle confirmation first
        if self.state.awaiting_confirmation:
            print(
                f"[DEBUG] awaiting_confirmation=True | pending_action={self.state.pending_action}"
            )
            return self._handle_confirmation(user_message)

        # 2) Extract structured information
        extracted = extract_information(user_message)
        print(f"[DEBUG] extracted={extracted}")

        self.state.update_from_extraction(extracted)
        print(f"[DEBUG] state_after_extraction={self.state}")

        # -------------------------------------------------
        # Semantic grounding (critical glue logic)
        # -------------------------------------------------

        destination = extracted.get("destination")
        user_lower = user_message.lower()

        # 1) Discover attractions intent
        if any(
            kw in user_lower
            for kw in ["attractions", "things to do", "what to do", "activities"]
        ):
            self.state.user_goal = "discover_attractions"
            self.state.goal_confidence = max(self.state.goal_confidence, 0.7)

        # 2) First destination → city (only if asking about attractions)
        if (
            destination
            and not self.state.city
            and self.state.user_goal == "discover_attractions"
        ):
            self.state.city = destination

        # 3) Destination inside an existing city → specific place
        elif destination and self.state.city:
            self.state.subject_name = destination
            self.state.user_goal = "learn_about_place"
            self.state.goal_confidence = max(self.state.goal_confidence, 0.7)

        # 4) Clarification → preferences (slot filling)
        category = extracted.get("category")
        if category and category not in self.state.preferences:
            self.state.preferences.append(category)

        # 5) Decide next deterministic action
        action = self._decide_next_action()
        print(f"[DEBUG] decided_action={action}")

        # 6) If clarification just completed → EXECUTE immediately
        if action == "run_attractions" and self.state.preferences:
            print("[DEBUG] executing run_attractions immediately after clarification")
            return self._execute_action(action)

        # 7) Otherwise → propose action
        if action:
            self.state.mark_proposal(action)
            proposal = self._propose_action(action)
            print(f"[DEBUG] proposal='{proposal}'")
            return proposal

        # 8) Fallback → natural conversation
        reply = self._conversational_reply(user_message)
        print(f"[DEBUG] conversational_reply='{reply[:150]}...'")
        return reply

    # -------------------------------------------------
    # Conversational layer (LLM-driven)
    # -------------------------------------------------

    def _conversational_reply(self, user_message: str) -> str:
        return call_llm(
            system_prompt=CONVERSATION_PROMPT,
            user_prompt=user_message,
            temperature=0.7,
        )

    # -------------------------------------------------
    # Decision layer (deterministic)
    # -------------------------------------------------

    def _decide_next_action(self) -> Optional[str]:
        if self.state.user_goal == "discover_attractions" and self.state.has_location():
            return "run_attractions"

        if self.state.user_goal == "learn_about_place" and self.state.has_subject():
            return "explain_subject"

        return None

    # -------------------------------------------------
    # Proposal & confirmation
    # -------------------------------------------------

    def _propose_action(self, action: str) -> str:
        link = self._google_maps_link_for_context()
        extra = f"\n\n📍 Google Maps: {link}" if link else ""

        if action == "run_attractions":
            return (
                "I can suggest a few interesting places nearby, ranked by relevance. "
                "Would you like me to do that?"
                + extra
            )

        if action == "explain_subject":
            return (
                f"I can tell you more about {self.state.subject_name} "
                "in a short, clear explanation. Would you like that?"
                + extra
            )

        return "Would you like me to continue?"

    def _handle_confirmation(self, user_message: str) -> str:
        normalized = user_message.strip().lower()

        yes_set = {
            "yes", "yeah", "yep", "sure", "ok", "okay",
            "please", "go ahead", "do it"
        }
        no_set = {"no", "nope", "nah", "not now", "later"}

        if any(word in normalized for word in yes_set):
            if not self.state.pending_action:
                self.state.reset_pending_action()
                return "Great — what would you like to explore next?"

            action = self.state.pending_action
            self.state.reset_pending_action()
            return self._execute_action(action)

        if any(word in normalized for word in no_set):
            self.state.reset_pending_action()
            return "No problem — tell me what you’d like to do instead."

        return "Just to be sure — would you like me to go ahead? (yes/no)"

    # -------------------------------------------------
    # Execution layer (agents)
    # -------------------------------------------------

    def _execute_action(self, action: str) -> str:
        if action == "run_attractions":

            # Resolve coordinates if missing
            if self.state.latitude is None or self.state.longitude is None:
                geo = self.geo_client.geocode(self.state.city, limit=1)

                if not geo:
                    return "I couldn’t determine your exact location."

                features = geo.get("features", [])
                if not features:
                    return "I couldn’t determine your exact location."

                coords = features[0]["geometry"]["coordinates"]
                self.state.longitude = coords[0]
                self.state.latitude = coords[1]

            result = self.attractions_agent.run(
                AttractionsAgentInput(
                    city=self.state.city,
                    lat=self.state.latitude,
                    lon=self.state.longitude,
                    preferences=self.state.preferences,
                )
            )

            if result.needs_clarification:
                return (
                    result.clarification_question
                    or "What kind of places are you interested in?"
                )

            if not result.attractions:
                response = self._wrap_action_response(
                    "I couldn’t find interesting places nearby "
                    "based on your preferences."
                )
                self._reset_after_action()
                return response

            lines = ["Here are some great places nearby:\n"]
            for i, place in enumerate(result.attractions, 1):
                maps_link = self._google_maps_search_link(
                    f"{place.name}, {self.state.city}"
                )
                lines.append(
                    f"{i}. {place.name}\n"
                    f"   Why: {place.reason}\n"
                    f"   📍 {maps_link}\n"
                )

            response = self._wrap_action_response("\n".join(lines))
            self._reset_after_action()
            return response

        if action == "explain_subject":
            content = self.wikipedia_agent.run(
                subject_name=self.state.subject_name,
                city=self.state.city,
            )
            response = self._wrap_action_response(content)
            self._reset_after_action()
            return response

        return "Something went wrong while executing the action."

    # -------------------------------------------------
    # Google Maps helpers
    # -------------------------------------------------

    def _google_maps_search_link(self, query: str) -> str:
        return (
            "https://www.google.com/maps/search/?api=1&query="
            + quote_plus(query)
        )

    def _google_maps_link_for_context(self) -> Optional[str]:
        if self.state.latitude is not None and self.state.longitude is not None:
            return self._google_maps_search_link(
                f"{self.state.latitude},{self.state.longitude}"
            )

        if self.state.subject_name and self.state.city:
            return self._google_maps_search_link(
                f"{self.state.subject_name}, {self.state.city}"
            )

        if self.state.city:
            return self._google_maps_search_link(self.state.city)

        return None

    # -------------------------------------------------
    # Response wrapper & reset
    # -------------------------------------------------

    def _wrap_action_response(self, content: str) -> str:
        return (
            f"{content}\n\n"
            "—\n"
            "What would you like to do next?\n"
            "• explore more attractions\n"
            "• learn about a specific place\n"
            "• change city"
        )

    def _reset_after_action(self):
        self.state.user_goal = None
        self.state.goal_confidence = 0.0
        self.state.pending_action = None
        self.state.awaiting_confirmation = False
        self.state.preferences = []

    # -------------------------------------------------
    # Initial greeting
    # -------------------------------------------------

    def get_initial_message(self) -> str:
        return (
            "Hi! 👋 I'm your travel assistant.\n"
            "You can tell me where you are, ask about places, "
            "or explore attractions nearby."
        )
