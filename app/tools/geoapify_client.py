# app/tools/geoapify_client.py

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Geoapify API base URLs
GEOAPIFY_GEOCODE_BASE_V1 = "https://api.geoapify.com/v1/geocode"
GEOAPIFY_PLACES_BASE_V2 = "https://api.geoapify.com/v2"


class GeoapifyClient:
    """
    Thin client for Geoapify APIs.

    Responsibilities:
    - Perform HTTP requests
    - Handle API versioning (v1 geocode, v2 places)
    - Return raw JSON responses

    This client contains NO business logic.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key or os.getenv("GEOAPIFY_API_KEY")
        if not self.api_key:
            raise ValueError("GEOAPIFY_API_KEY is not set")

        self.timeout = timeout

    # ------------------------------------------------------------------
    # Geocoding (v1)
    # ------------------------------------------------------------------

    def geocode(self, text: str, limit: int = 5) -> Dict[str, Any]:
        """
        Convert a place name into geographic coordinates.
        """
        url = f"{GEOAPIFY_GEOCODE_BASE_V1}/search"
        params = {
            "text": text,
            "limit": limit,
            "apiKey": self.api_key,
        }
        return self._get(url, params)

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Convert coordinates into place details.
        """
        url = f"{GEOAPIFY_GEOCODE_BASE_V1}/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "apiKey": self.api_key,
        }
        return self._get(url, params)

    # ------------------------------------------------------------------
    # Places (v2)
    # ------------------------------------------------------------------

    def places(
        self,
        categories: str,
        lat: float,
        lon: float,
        radius: int = 3000,
        limit: int = 10,
        named_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch nearby places using Geoapify Places API (v2).

        Args:
            categories: Geoapify category string (whitelisted upstream)
            lat, lon: center point
            radius: search radius in meters
            limit: max number of results
            named_only: whether to return only named places

        Returns:
            Raw Geoapify JSON response.
        """
        url = f"{GEOAPIFY_PLACES_BASE_V2}/places"
        params = {
            "categories": categories,
            "filter": f"circle:{lon},{lat},{radius}",
            "limit": limit,
            "apiKey": self.api_key,
        }

        if named_only:
            params["conditions"] = "named"

        return self._get(url, params)

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    def _get(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(url, params=params, timeout=self.timeout)

        if not response.ok:
            raise RuntimeError(
                f"Geoapify API error {response.status_code}: {response.text}"
            )

        return response.json()
