# app/tools/geo_tool.py

from typing import Dict, Any, List

from app.tools.geoapify_client import GeoapifyClient
from app.routing.place_intent import PlaceIntent
from app.routing.place_category_resolver import PlaceCategoryResolver


class GeoTool:
    """
    High-level geographic tool.

    Orchestrates:
    - geocoding
    - intent → category resolution
    - nearby places lookup

    This is the single entry point for location-based queries.
    """

    def __init__(self, geo_client: GeoapifyClient | None = None):
        self.geo_client = geo_client or GeoapifyClient()

    def get_places(
        self,
        city: str,
        intent: PlaceIntent,
        radius: int = 3000,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get nearby places for a given city and intent.

        Returns:
            A list of Geoapify place feature objects.
        """
        lat, lon = self._geocode_city(city)
        category = PlaceCategoryResolver.resolve(intent)

        places_response = self.geo_client.places(
            categories=category,
            lat=lat,
            lon=lon,
            radius=radius,
            limit=limit,
        )

        return places_response.get("features", [])

    # ------------------------
    # Internal helpers
    # ------------------------

    def _geocode_city(self, city: str) -> tuple[float, float]:
        geo = self.geo_client.geocode(city)
        features = geo.get("features", [])

        if not features:
            raise ValueError(f"Could not geocode city: {city}")

        props = features[0].get("properties", {})
        lat = props.get("lat")
        lon = props.get("lon")

        if lat is None or lon is None:
            raise ValueError(f"Invalid geocoding result for city: {city}")

        return lat, lon
