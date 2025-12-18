# app/context.py
from datetime import datetime
from typing import Any


class ConversationContext:
    # ===== Location / Geography =====
    current_city: str | None
    country: str | None
    lat: float | None
    lon: float | None
    timezone: str | None

    # ===== Current conversational reference =====
    last_place: str | None
    last_place_type: str | None       # museum / attraction / restaurant
    last_place_id: str | None
    last_place_source: str | None     # geoapify / wikipedia

    # Optional unified place context (future-proof)
    current_place: dict[str, Any] | None

    # ===== Results & reasoning =====
    last_poi_list: list | None
    last_ranked_results: list | None

    # ===== Intent tracking =====
    last_intent: str | None            # find_poi / summarize_place / rank_results

    # ===== User preferences & settings =====
    user_language: str
    radius_km: float

    # ===== Time context (optional but powerful) =====
    current_time: datetime | None
