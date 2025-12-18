from app.tools.wikipedia import get_wikipedia_summary

print("Calling Wikipedia API...")

result = get_wikipedia_summary("Colosseum")

print("Result received:")
print(result)

if result.get("found"):
    print("✅ Wikipedia API communication successful")
else:
    print("❌ Wikipedia API returned no data")
