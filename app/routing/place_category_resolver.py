# app/routing/place_category_resolver.py

from app.routing.place_intent import PlaceIntent


class PlaceCategoryResolver:
    """
    Resolves a high-level PlaceIntent into a Geoapify Places category.

    This resolver acts as a strict whitelist to prevent invalid
    or hallucinated categories from reaching external APIs.
    """

    _INTENT_TO_CATEGORY = {
        PlaceIntent.SUPERMARKET: "commercial.supermarket",
        PlaceIntent.RESTAURANT: "catering.restaurant",
        PlaceIntent.CAFE: "catering.cafe",
        PlaceIntent.PARK: "leisure.park",
        PlaceIntent.MUSEUM: "entertainment.museum",
        PlaceIntent.ATTRACTION: "tourism.attraction",
        PlaceIntent.HOTEL: "accommodation.hotel",
        PlaceIntent.BAR: "catering.bar",
        PlaceIntent.SHOPPING: "commercial.shopping_mall",
        PlaceIntent.PHARMACY: "commercial.health_and_beauty.pharmacy",
    }

    @classmethod
    def resolve(cls, intent: PlaceIntent) -> str:
        """
        Convert PlaceIntent into a Geoapify category string.

        Raises:
            ValueError: if the intent is not supported.
        """
        try:
            return cls._INTENT_TO_CATEGORY[intent]
        except KeyError:
            raise ValueError(
                f"Unsupported PlaceIntent: {intent}. "
                f"Supported intents: {list(cls._INTENT_TO_CATEGORY.keys())}"
            )
