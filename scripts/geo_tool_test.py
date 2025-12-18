from app.tools.geo_tool import GeoTool
from app.routing.place_intent import PlaceIntent

geo_tool = GeoTool()

places = geo_tool.get_places(
    city="Barcelona",
    intent=PlaceIntent.SUPERMARKET,
    limit=5,
)

for p in places:
    props = p.get("properties", {})
    print(props.get("name") or props.get("formatted"))