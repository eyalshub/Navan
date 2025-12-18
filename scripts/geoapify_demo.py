# scripts/geoapify_demo.py

from app.tools.geo_tool import GeoTool
from app.routing.place_intent import PlaceIntent


def main():
    geo_tool = GeoTool()

    city = "Barcelona"

    TEST_INTENTS = [
        PlaceIntent.SUPERMARKET,
        PlaceIntent.MUSEUM,
        PlaceIntent.ATTRACTION,
        PlaceIntent.PARK,
        PlaceIntent.RESTAURANT,
        PlaceIntent.CAFE,
    ]

    for intent in TEST_INTENTS:
        print(f"\n=== Nearby {intent.value.capitalize()}s ===")

        places = geo_tool.get_places(
            city=city,
            intent=intent,
            radius=4000,
            limit=5,
        )

        if not places:
            print("No places found.")
            continue

        for p in places:
            props = p.get("properties", {})
            name = props.get("name") or props.get("formatted") or "Unnamed place"
            categories = props.get("categories", [])
            print(f"- {name} | categories: {categories}")


if __name__ == "__main__":
    main()
