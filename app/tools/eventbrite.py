import os
import requests
from dotenv import load_dotenv
from typing import List, Dict
from pathlib import Path
from datetime import datetime

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

EVENTBRITE_API_KEY = os.getenv("EVENTBRITE_API_KEY")
BASE_URL = "https://www.eventbriteapi.com/v3/events/search/"

# Hard-coded city coordinates (minimal & reliable)
CITY_COORDS = {
    "London": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Berlin": (52.52, 13.405),
    "Paris": (48.8566, 2.3522),
    "Amsterdam": (52.3676, 4.9041),
    "Barcelona": (41.3874, 2.1686),
    "Rome": (41.9028, 12.4964),
}


def get_events_by_city(
    city: str,
    max_results: int = 3
) -> List[Dict]:
    if not EVENTBRITE_API_KEY:
        raise ValueError("EVENTBRITE_API_KEY is not set")

    if city not in CITY_COORDS:
        return []

    lat, lon = CITY_COORDS[city]

    headers = {
        "Authorization": f"Bearer {EVENTBRITE_API_KEY}"
    }

    params = {
        "location.latitude": lat,
        "location.longitude": lon,
        "location.within": "25km",
        "start_date.range_start": datetime.utcnow().isoformat() + "Z",
        "page_size": max_results,
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=10
    )

    if response.status_code != 200:
        return []

    events = response.json().get("events", [])

    results = []
    for e in events:
        results.append({
            "name": e["name"]["text"] if e.get("name") else None,
            "start_time": e["start"]["local"] if e.get("start") else None,
            "url": e.get("url"),
            "source": "eventbrite",
        })

    return results
