# app/routing/place_intent.py

from enum import Enum


class PlaceIntent(str, Enum):
    """
    High-level user intent for location-based queries.

    This enum represents *what* the user is looking for,
    not *how* it is fetched or which API is used.
    """

    SUPERMARKET = "supermarket"
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    PARK = "park"
    MUSEUM = "museum"
    ATTRACTION = "attraction"

    # Future extensions
    HOTEL = "hotel"
    BAR = "bar"
    SHOPPING = "shopping"
    PHARMACY = "pharmacy"

    def __str__(self) -> str:
        return self.value
