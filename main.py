import requests
import os
import json
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")
API_HOST = os.getenv("RAPIDAPI_HOST")

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

# 🔗 Exact URL (you can change the date/time here directly)
#url = "https://aerodatabox.p.rapidapi.com/flights/airports/iata/BOS/2025-07-24T09:00/2025-07-24T19:00?withLeg=true&direction=Departure&withCancelled=true&withCodeshared=true&withCargo=true&withPrivate=true&withLocation=false"
#url = "https://aerodatabox.p.rapidapi.com/flights/airports/iata/JFK/2025-07-24T09:00/2025-07-24T19:00?withLeg=true&direction=Departure&withCancelled=true&withCodeshared=true&withCargo=true&withPrivate=true&withLocation=false"
#url = "https://aerodatabox.p.rapidapi.com/flights/airports/iata/ORD/2025-07-24T09:00/2025-07-24T19:00?withLeg=true&direction=Departure&withCancelled=true&withCodeshared=true&withCargo=true&withPrivate=true&withLocation=false"
url = "https://aerodatabox.p.rapidapi.com/flights/airports/iata/SEA/2025-07-24T09:00/2025-07-24T19:00?withLeg=true&direction=Departure&withCancelled=true&withCodeshared=true&withCargo=true&withPrivate=true&withLocation=false"
# Fetch
print("📡 Requesting data from AeroDataBox...")

response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"Error {response.status_code}: {response.text}")
    exit()

data = response.json()

# Save full response
os.makedirs("data", exist_ok=True)
#full_path = "data/BOS_full_response.json"
#full_path = "data/JFK_full_response.json"
#full_path = "data/ORD_full_response.json"
full_path = "data/SEA_full_response.json"
with open(full_path, "w") as f:
    json.dump(data, f, indent=4)
print(f"✅ Full response saved to {full_path}")

#filtered flights
departures = data.get("departures", [])

#sfo_flights = [
#mia_flights = [
#den_flights = [
lax_flights = [
    flight for flight in departures
    #if flight.get("arrival", {}).get("airport", {}).get("iata") == "SFO"
    #if flight.get("arrival", {}).get("airport", {}).get("iata") == "MIA"
    #if flight.get("arrival", {}).get("airport", {}).get("iata") == "DEN"
    if flight.get("arrival", {}).get("airport", {}).get("iata") == "LAX"
]
#filtered_path = "data/BOS_to_SFO_only.json"
#filtered_path = "data/JFK_to_MIA_only.json"
#filtered_path = "data/ORD_to_DEN_only.json"
filtered_path = "data/SEA_to_LAX_only.json"
with open(filtered_path, "w") as f:
    #json.dump(sfo_flights, f, indent=4)
    #json.dump(mia_flights, f, indent=4)
    #json.dump(den_flights, f, indent=4)
    json.dump(lax_flights, f, indent=4)
    #print(f"✅ {len(sfo_flights)} BOS → SFO flights saved to {filtered_path}")
    #print(f"✅ {len(mia_flights)} JFK → MIA flights saved to {filtered_path}")
    #print(f"✅ {len(den_flights)} ORD → DEN flights saved to {filtered_path}")
print(f"✅ {len(lax_flights)} SEA → LAX flights saved to {filtered_path}")

