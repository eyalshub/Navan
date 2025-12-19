# app/tools/wikipedia.py
import requests
from urllib.parse import quote

WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def _fetch(title: str) -> dict | None:
    url = WIKIPEDIA_API_URL + quote(title.replace(" ", "_"))

    response = requests.get(
        url,
        headers={"User-Agent": "TravelAssistant/1.0"}
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("extract"):
        return None

    return {
        "found": True,
        "title": data.get("title"),
        "summary": data.get("extract"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        "source": "wikipedia"
    }


def get_wikipedia_summary(title: str, city: str | None = None) -> dict:
    """
    Deterministic Wikipedia summary fetch with safe fallbacks.
    """

    candidates = []

    if city:
        candidates.extend([
            f"{title} ({city})",
            f"{title}, {city}",
            f"{title} {city}",
        ])

    candidates.append(title)

    for candidate in candidates:
        result = _fetch(candidate)
        if result:
            return result

    return {
        "found": False,
        "title": title,
        "summary": None,
        "source": "wikipedia"
    }
