from app.tools.geonames import get_points_of_interest

print("Calling GeoNames API...")

results = get_points_of_interest("Rome", max_results=3)

print("Results received:")
for r in results:
    print(r)

if not results:
    print("❌ No results returned")
else:
    print("✅ API communication successful")
