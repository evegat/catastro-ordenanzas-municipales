import json
from datetime import datetime

with open("data/municipal_verified_records.json", "r", encoding="utf-8") as f:
    data = json.load(f)

records = data.get("records", [])
current_urls = {r.get("target_url") for r in records}

with open("data/subagent_verified_batch2.json", "r", encoding="utf-8") as f:
    batch = json.load(f)

added = 0
for item in batch:
    # Corregir url de Ovalle si venia con http
    target_url = item["target_url"]
    if target_url.startswith("http://transparenciaovalle.cl"):
        target_url = target_url.replace("http://", "https://")
        item["target_url"] = target_url
        item["verification"]["resolved_url"] = target_url
        
    if target_url not in current_urls:
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
            "target_url": target_url,
            "verification": {
                "status": "verified",
                "http_status": item["http_status"],
                "resolved_url": target_url,
                "content_type": "application/pdf",
                "sha256": item["sha256"],
                "bytes": item["size_bytes"],
                "verified_at": item["verified_at"]
            }
        }
        records.append(rec)
        current_urls.add(target_url)
        added += 1

print(f"Nuevos registros añadidos: {added}")
data["count"] = len(records)
data["records"] = records
data["generated_at"] = datetime.now().isoformat()

with open("data/municipal_verified_records.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total registros municipales verificados: {len(records)}")
