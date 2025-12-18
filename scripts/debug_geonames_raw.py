import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://api.geonames.org/searchJSON"
USERNAME = os.getenv("GEONAMES_USERNAME")

params = {
    "q": "Rome",
    "maxRows": 20,
    "username": USERNAME
}

print("Request params:", params)

response = requests.get(BASE_URL, params=params)
print("Status code:", response.status_code)

data = response.json()

print("Total results:", len(data.get("geonames", [])))
for item in data.get("geonames", []):
    print(
        item.get("name"),
        "| featureClass:", item.get("featureClass"),
        "| featureCode:", item.get("featureCode")
    )
