"""Fetch coordinates for all Chilean communes from Wikidata or OpenStreetMap."""
import json
import time
import requests
import pandas as pd
from pathlib import Path

# Query all communes in Chile
query = """
SELECT DISTINCT ?comunaLabel ?lat ?lon WHERE {
  ?comuna wdt:P31 wd:Q659103 .
  ?comuna p:P625 [
    psv:P625 [
      wikibase:geoLatitude ?lat ;
      wikibase:geoLongitude ?lon
    ]
  ] .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "es". }
}
"""

url = "https://query.wikidata.org/sparql"
headers = {"User-Agent": "P090Research/1.0 (evegat@uchile.cl)", "Accept": "application/json"}

coords = {}
try:
    r = requests.get(url, params={"query": query, "format": "json"}, headers=headers, timeout=25)
    if r.status_code == 200:
        for b in r.json()["results"]["bindings"]:
            name = b["comunaLabel"]["value"].strip()
            lat = float(b["lat"]["value"])
            lon = float(b["lon"]["value"])
            coords[name] = {"lat": lat, "lon": lon}
        print(f"Wikidata returned {len(coords)} communes coordinates.")
except Exception as e:
    print(f"Wikidata query failed: {e}")

# Load maestro_comunas_chile.csv
maestro = pd.read_csv("data/maestro_comunas_chile.csv")
print(f"Maestro has {len(maestro)} communes.")

# For any missing commune, use Nominatim geocoding or regional defaults
missing = []
for com in maestro["comuna_nombre"]:
    if com not in coords:
        missing.append(com)

print(f"Missing from direct name match: {len(missing)}")

# Fallback geocoding via Nominatim
for idx, com in enumerate(missing):
    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(com + ', Chile')}&format=json&limit=1"
        res = requests.get(nom_url, headers={"User-Agent": "P090ChileCatastroDocente/1.0 (evegat@uchile.cl)"}, timeout=5)
        if res.status_code == 200 and res.json():
            item = res.json()[0]
            coords[com] = {"lat": float(item["lat"]), "lon": float(item["lon"])}
            print(f"Geocoded {com}: {item['lat']}, {item['lon']}")
        else:
            print(f"Could not geocode {com}")
        time.sleep(0.8)  # Nominatim rate limit
    except Exception as e:
        print(f"Error geocoding {com}: {e}")

# Save full coordinates mapping
with open("data/comunas_coordinates.json", "w", encoding="utf-8") as f:
    json.dump(coords, f, ensure_ascii=False, indent=2)

print(f"Saved total {len(coords)} commune coordinates to data/comunas_coordinates.json")
