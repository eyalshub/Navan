import requests


WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def get_wikipedia_summary(title: str) -> dict:
    """
    Fetch a summary for a Wikipedia page.
    Returns raw factual data only.
    """
    url = WIKIPEDIA_API_URL + title.replace(" ", "_")

    response = requests.get(
        url,
        headers={"User-Agent": "TravelAssistant/1.0"}
    )

    if response.status_code != 200:
        return {
            "found": False,
            "title": title,
            "summary": None,
            "source": "wikipedia"
        }

    data = response.json()

    return {
        "found": True,
        "title": data.get("title"),
        "summary": data.get("extract"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
        "source": "wikipedia"
    }
