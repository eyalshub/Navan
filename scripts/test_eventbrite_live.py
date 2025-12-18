from app.tools.eventbrite import get_events_by_city

cities = [
    "London",
    "New York",
    "Berlin",
    "Paris",
    "Amsterdam",
    "Barcelona",
    "Rome",
]

print("🔎 Testing Eventbrite API across multiple cities...\n")

for city in cities:
    print(f"📍 City: {city}")

    events = get_events_by_city(city, max_results=2)

    if events:
        print("  ✅ Events found:")
        for e in events:
            print(f"   - {e['name']} ({e['start_time']})")
    else:
        print("  ❌ No events found")

    print("-" * 40)
