import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from amadeus import Client, ResponseError, Location

# Load environment variables
load_dotenv()
AMADEUS_KEY    = os.getenv("AMADEUS_API_KEY")
AMADEUS_SECRET = os.getenv("AMADEUS_API_SECRET")
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY")

# Initialize clients
amadeus = Client(
    client_id=AMADEUS_KEY,
    client_secret=AMADEUS_SECRET
)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Routes to analyze
routes = [
    {"from": "JFK", "to": "LHR"},
    {"from": "LAX", "to": "ORD"},
    {"from": "DFW", "to": "MIA"},
    {"from": "SFO", "to": "SEA"},
    {"from": "ATL", "to": "DEN"}
]

def fetch_price_analysis(origin, destination, date):
    """
    Fetches historical price metrics via the Price Analysis API.
    Always returns a dict with every key, defaulting to None on error.
    """
    defaults = {
        "min_price": None,
        "max_price": None,
        "avg_price": None,
        "p25":       None,
        "p50":       None,
        "p75":       None
    }

    try:
        resp = amadeus.analytics.itinerary_price_metrics.get(
            originIataCode=origin,
            destinationIataCode=destination,
            departureDate=date,
            currencyCode="USD",
            oneWay=True
        )

        data_list = resp.data if isinstance(resp.data, list) else [resp.data]
        if not data_list:
            return defaults

        d = data_list[0]
        return {
            "min_price": float(d.get("minimumPrice", 0)),
            "max_price": float(d.get("maximumPrice", 0)),
            "avg_price": float(d.get("averagePrice", 0)),
            "p25":       float(d.get("percentile25", 0)),
            "p50":       float(d.get("percentile50", 0)),
            "p75":       float(d.get("percentile75", 0))
        }

    except Exception as e:
        print(f"[Price Analysis error on {origin}-{destination} {date}]: {e}")
        return defaults


def get_coords(iata):
    """Looks up an airport's latitude/longitude via the Locations API."""
    try:
        res = amadeus.reference_data.locations.get(
            keyword=iata,
            subType=Location.AIRPORT
        )
        ap = res.data[0]
        geo = ap["geoCode"]
        return geo["latitude"], geo["longitude"]
    except Exception:
        return None, None


def find_candidate_hubs(lat1, lon1, lat2, lon2, top_n=3):
    """Finds the top-n busiest airports around the geographic midpoint."""
    if None in (lat1, lon1, lat2, lon2):
        return []
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    try:
        res = amadeus.reference_data.locations.airports.get(
            latitude=mid_lat,
            longitude=mid_lon
        )
        return [a["iataCode"] for a in res.data[:top_n]]
    except Exception:
        return []


def cheapest_direct(origin, destination, date):
    """Fetches the cheapest non-stop flight via Flight Offers Search."""
    try:
        res = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1,
            nonStop=True,
            max=5,
            currencyCode="USD"
        )
        prices = [float(f["price"]["total"]) for f in res.data]
        return min(prices) if prices else None
    except Exception:
        return None


def cheapest_one_stop(origin, hub, destination, date):
    """Fetches the cheapest two-leg itinerary via a hub."""
    body = {
        "currencyCode": "USD",
        "originDestinations": [
            {"id": "1", "originLocationCode": origin,     "destinationLocationCode": hub,        "departureDate": date},
            {"id": "2", "originLocationCode": hub,        "destinationLocationCode": destination, "departureDate": date}
        ],
        "travelers": [{"id": "1", "travelerType": "ADULT"}],
        "sources": ["GDS"],
        "max": 5
    }
    try:
        res = amadeus.shopping.flight_offers_search.post(body)
        prices = [float(o["price"]["total"]) for o in res.data]
        return min(prices) if prices else None
    except Exception:
        return None


def hub_on_time_pct(hub, date):
    """Gets on-time departure percentage for the hub airport."""
    try:
        res = amadeus.airport.predictions.on_time.get(
            airportCode=hub,
            date=date
        )
        return float(res.data.get("onTime", 0))
    except Exception:
        return None

# Generate dates for July 2025
start_date = datetime(2025, 7, 20)
dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]

# Ensure output folder
os.makedirs("data", exist_ok=True)

for route in routes:
    o, d = route["from"], route["to"]
    print(f"\nProcessing {o} → {d}")
    lat1, lon1 = get_coords(o)
    lat2, lon2 = get_coords(d)
    hubs = find_candidate_hubs(lat1, lon1, lat2, lon2)

    records = []
    for date in dates:
        # Fetch all data
        price_stats = fetch_price_analysis(o, d, date)
        direct = cheapest_direct(o, d, date)
        best_hub, best_price = None, None
        for hub in hubs:
            p = cheapest_one_stop(o, hub, d, date)
            if p is not None and (best_price is None or p < best_price):
                best_price = p
                best_hub = hub
        ontime = hub_on_time_pct(best_hub, date) if best_hub else None

        # Build record explicitly
        record = {
            "origin":           o,
            "destination":      d,
            "departure_date":   date,
            "min_price":        price_stats["min_price"],
            "max_price":        price_stats["max_price"],
            "avg_price":        price_stats["avg_price"],
            "p25":              price_stats["p25"],
            "p50":              price_stats["p50"],
            "p75":              price_stats["p75"],
            "direct_price":     direct,
            "synthetic_hub":    best_hub,
            "synthetic_price":  best_price,
            "hub_on_time_pct":  ontime
        }

        records.append(record)
        time.sleep(0.1)  # respect rate limits

    # Preview a sample record
    if records:
        import pprint
        print("Sample record:")
        pprint.pprint(records[0])

    # Save locally
    file_path = f"data/{o}_to_{d}_flight_strategies_july2025.json"
    with open(file_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"  Wrote {len(records)} records to {file_path}")

    # Insert into Supabase and return inserted rows
    try:
        result = (
            supabase
            .table("flight_strategies")
            .insert(records)
            .select("*")
            .execute()
        )
        if result.get("error"):
            print("Supabase insert error:")
            print(json.dumps(result, indent=2))
        else:
            print("Inserted and returned rows:")
            pprint.pprint(result.get("data"))
    except Exception as e:
        print("Unexpected exception during Supabase insert:", e)

print("\n✨ All routes processed.")
