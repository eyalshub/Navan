# app/state/conversation_state.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ======================================================
# Canonical preference vocabulary
# ======================================================

PREFERENCE_SYNONYMS = {
    "museum": {
        "museum", "museums", "gallery", "galleries", "exhibition",
        "art museum", "history museum",
    },
    "history": {
        "history", "historical", "ancient", "ruins",
        "roman", "medieval", "heritage",
    },
    "art": {
        "art", "painting", "sculpture", "modern art",
    },
    "food": {
        "food", "restaurant", "restaurants", "cuisine", "local food",
    },
    "park": {
        "park", "parks", "garden", "nature", "green",
    },
    "sightseeing": {
        "sightseeing", "landmarks", "highlights", "must see",
    },
}


def normalize_preferences(raw_terms: List[str]) -> List[str]:
    """
    Normalize free-text and structured preference terms
    into a canonical preference vocabulary.
    """
    normalized = set()

    for term in raw_terms:
        if not isinstance(term, str):
            continue

        t = term.lower().strip()

        for canonical, synonyms in PREFERENCE_SYNONYMS.items():
            if canonical in t or any(s in t for s in synonyms):
                normalized.add(canonical)

    return list(normalized)


# ======================================================
# Conversation State
# ======================================================

@dataclass
class ConversationState:
    """
    Short-term, structured conversational state.

    This object:
    - Stores facts and signals
    - NEVER executes actions
    - NEVER calls agents
    - NEVER decides flow

    All decisions belong to the Orchestrator.
    """

    # =========================
    # User goal (WHAT the user wants)
    # =========================

    user_goal: Optional[str] = None
    """
    High-level goal.
    Examples:
    - 'discover_attractions'
    - 'learn_about_place'
    """

    goal_confidence: float = 0.0

    # =========================
    # Conversation subject
    # =========================

    subject_name: Optional[str] = None
    """
    Main subject of the conversation.
    Example: 'Colosseum', 'British Museum'
    """

    subject_type: Optional[str] = None
    """
    Example: 'attraction', 'museum', 'landmark'
    """

    # =========================
    # Location context
    # =========================

    city: Optional[str] = None
    country: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # =========================
    # User preferences
    # =========================

    preferences: List[str] = field(default_factory=list)

    # =========================
    # System control (internal)
    # =========================

    last_executed_action: Optional[str] = None
    """
    Prevents repeating the same agent action
    multiple times for the same intent.
    Example: 'explain_subject', 'run_attractions'
    """

    pending_action: Optional[str] = None
    awaiting_confirmation: bool = False

    # =========================
    # Meta
    # =========================

    turn_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # ==================================================
    # Update logic (from extraction)
    # ==================================================

    def update_from_extraction(self, data: Dict[str, Any]) -> None:
        """
        Update state from structured extraction output.

        This method:
        - Is defensive
        - Never triggers actions
        - Only updates fields if signals exist
        """

        if not data:
            return

        # -------------------------------------------------
        # 1. Explicit user goal (highest priority)
        # -------------------------------------------------

        if data.get("user_goal"):
            self.user_goal = data["user_goal"]
            self.goal_confidence = float(data.get("goal_confidence", 0.8))

        # -------------------------------------------------
        # 2. Subject inference
        # -------------------------------------------------

        subject = (
            data.get("subject_name")
            or data.get("attraction")
            or data.get("landmark")
            or data.get("place")
        )

        if subject:
            self.subject_name = subject
            self.subject_type = data.get("subject_type") or data.get("type")

            if not self.user_goal:
                self.user_goal = "learn_about_place"
                self.goal_confidence = 0.6

        # -------------------------------------------------
        # 3. Location handling (flat OR nested)
        # -------------------------------------------------

        if data.get("city"):
            self.city = data["city"]

        if data.get("country"):
            self.country = data["country"]

        if data.get("current_location"):
            self.city = data["current_location"]

        location = data.get("location")
        if isinstance(location, dict):
            if location.get("city"):
                self.city = location["city"]
            if location.get("country"):
                self.country = location["country"]

        if isinstance(location, str):
            self.city = location

        if data.get("latitude") is not None:
            self.latitude = data["latitude"]

        if data.get("longitude") is not None:
            self.longitude = data["longitude"]

        # -------------------------------------------------
        # 4. Preferences (semantic normalization)
        # -------------------------------------------------

        raw_prefs: List[str] = []

        if isinstance(data.get("preferences"), list):
            raw_prefs.extend(data["preferences"])

        if isinstance(data.get("interests"), list):
            raw_prefs.extend(data["interests"])

        if data.get("likes_museums"):
            raw_prefs.append("museum")

        if data.get("likes_history"):
            raw_prefs.append("history")

        request_text = data.get("request")
        if isinstance(request_text, str):
            raw_prefs.append(request_text)

        recs = data.get("recommendations")
        if isinstance(recs, dict):
            rec_type = recs.get("type")
            if isinstance(rec_type, str):
                raw_prefs.append(rec_type)

        normalized = normalize_preferences(raw_prefs)

        for pref in normalized:
            if pref not in self.preferences:
                self.preferences.append(pref)

        if self.preferences and not self.user_goal:
            self.user_goal = "discover_attractions"
            self.goal_confidence = 0.7

        # -------------------------------------------------
        # 5. Timestamp
        # -------------------------------------------------

        self.last_updated = datetime.utcnow()

    # ==================================================
    # System helpers
    # ==================================================

    def increment_turn(self) -> None:
        self.turn_count += 1
        self.last_updated = datetime.utcnow()

    def mark_proposal(self, action: str) -> None:
        self.pending_action = action
        self.awaiting_confirmation = True

    def reset_pending_action(self) -> None:
        self.pending_action = None
        self.awaiting_confirmation = False

    # ==================================================
    # Semantic checks (used by Orchestrator)
    # ==================================================

    def has_subject(self) -> bool:
        return bool(self.subject_name)

    def has_location(self) -> bool:
        return bool(self.city or (self.latitude is not None and self.longitude is not None))
