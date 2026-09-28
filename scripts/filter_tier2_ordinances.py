import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

data = json.load(open("data/tier2_probe_results.json", encoding="utf-8"))

for item in data:
    c = item["comuna"]
    mu = item["mu"]
    links = item["cplt_mn_links"] + item["web_links"]
    ordinances = []
    for l in links:
        t = l.get("text", "")
        h = l.get("href", "")
        combo = (t + " " + h).lower()
        if "ordenanza" in combo or ("decreto" in combo and any(y in combo for y in ["2021", "2022", "2023", "2024", "2025", "2026"])):
            ordinances.append((t, h))
    if ordinances:
        print(f"=== {c} ({mu}) - {len(ordinances)} ORDENANZAS / DECRETOS ===")
        for t, h in ordinances[:10]:
            print(f"  * {t[:50]} | {h}")
