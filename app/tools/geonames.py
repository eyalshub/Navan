# app/tools/geonames.py
import os
import requests
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME")
BASE_URL = "http://api.geonames.org/searchJSON"


def get_city_coordinates(city: str) -> Optional[Dict[str, float]]:
    """
    Resolve a city name to its geographic coordinates using GeoNames.
    Returns a dict with lat/lon or None if not found.
    """
    if not GEONAMES_USERNAME:
        raise ValueError("GEONAMES_USERNAME is not set in environment variables")

    params = {
        "q": city,
        "featureClass": "P",  # Populated place (city, town)
        "maxRows": 1,
        "username": GEONAMES_USERNAME,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json().get("geonames", [])
    if not data:
        return None

    try:
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lng"]),
        }
    except (KeyError, ValueError):
        return None


def get_points_of_interest(city: str, max_results: int = 5) -> List[Dict]:
    """
    Fetch points of interest (POIs) near a given city using GeoNames.

    The function works in two steps:
    1. Resolve the city to coordinates.
    2. Search for POIs (featureClass='S') within a bounding box around the city.

    Returns a list of raw geographic entities only (no LLM processing).
    """
    city_coords = get_city_coordinates(city)
    if not city_coords:
        return []

    # Bounding box radius in degrees (~0.1 ≈ 10km)
    radius = 0.1

    params = {
        "featureClass": "S",  # Spots / specific places
        "north": city_coords["lat"] + radius,
        "south": city_coords["lat"] - radius,
        "east": city_coords["lon"] + radius,
        "west": city_coords["lon"] - radius,
        "maxRows": max_results,
        "username": GEONAMES_USERNAME,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    results = []
    for item in response.json().get("geonames", []):
        results.append({
            "name": item.get("name"),
            "country": item.get("countryName"),
            "lat": item.get("lat"),
            "lon": item.get("lng"),
            "source": "geonames",
        })

    return results
