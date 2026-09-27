import json
import os
from datetime import datetime

with open("data/municipal_verified_records.json", "r", encoding="utf-8") as f:
    data = json.load(f)

records = data.get("records", [])
print(f"Registros verificados previos: {len(records)}")

with open("data/subagent_verified_batch.json", "r", encoding="utf-8") as f:
    batch = json.load(f)

current_urls = {r.get("target_url") for r in records}
added = 0

for item in batch:
    if item.get("verified") and item["target_url"] not in current_urls:
        rec = {
            "comuna": item["comuna"],
            "region_id": item["region_id"],
            "cplt_code": item.get("cplt_code", ""),
            "fuente": "Municipalidad",
            "numero": item.get("numero", "S/N"),
            "fecha": item["fecha"],
            "titulo": item["titulo"],
            "materia": item["materia"],
            "materia_id": item["materia_id"],
            "source_listing_url": item.get("source_listing_url", ""),
            "target_url": item["target_url"],
            "verification": {
                "status": "verified",
                "http_status": item["http_status"],
                "resolved_url": item["target_url"],
                "content_type": "application/pdf",
                "sha256": item["sha256"],
                "bytes": item["size_bytes"],
                "verified_at": item["verified_at"]
            }
        }
        records.append(rec)
        current_urls.add(item["target_url"])
        added += 1

print(f"Nuevos registros añadidos: {added}")
data["count"] = len(records)
data["records"] = records
data["generated_at"] = datetime.now().isoformat()

with open("data/municipal_verified_records.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total registros en municipal_verified_records.json: {len(records)}")
