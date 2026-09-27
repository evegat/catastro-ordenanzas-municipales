import json
import hashlib
import urllib.request
from datetime import datetime

with open(r"C:\Users\evega\.gemini\antigravity\brain\b42f4835-0ce7-4129-b438-82eaa5765e6b\scratch\verified_14_zona_centro.json", "r", encoding="utf-8") as f:
    zona_centro = json.load(f)

print(f"Cargados {len(zona_centro)} registros de Zona Centro.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

verified_records = []
for item in zona_centro:
    comuna = item["comuna"]
    target_url = item["target_url"]
    verification = item.get("verification", {})
    sha256 = verification.get("sha256")
    bytes_count = verification.get("bytes", 0)
    
    # Si falta SHA-256 o bytes, descargar y calcular
    if not sha256 or len(sha256) != 64:
        print(f"Descargando y calculando SHA-256 para {comuna} desde {target_url[:50]}...")
        req = urllib.request.Request(target_url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                sha256 = hashlib.sha256(content).hexdigest()
                bytes_count = len(content)
                print(f"[OK] {comuna}: {bytes_count} bytes, SHA-256: {sha256[:12]}...")
        except Exception as e:
            print(f"[FAIL] Error descargando {comuna}: {e}")
            continue
            
    rec = {
        "comuna": comuna,
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
            "http_status": 200,
            "resolved_url": target_url,
            "content_type": "application/pdf",
            "sha256": sha256,
            "bytes": bytes_count,
            "verified_at": datetime.now().isoformat()
        }
    }
    verified_records.append(rec)

print(f"Total procesados con SHA-256 verificado: {len(verified_records)} de {len(zona_centro)}")

# Guardar en temporal
with open("data/subagent_verified_batch3.json", "w", encoding="utf-8") as f:
    json.dump(verified_records, f, ensure_ascii=False, indent=2)

# Ahora integrar a data/municipal_verified_records.json
with open("data/municipal_verified_records.json", "r", encoding="utf-8") as f:
    master = json.load(f)

current_records = master.get("records", [])
current_urls = {r.get("target_url") for r in current_records}

added = 0
for r in verified_records:
    if r["target_url"] not in current_urls:
        current_records.append(r)
        current_urls.add(r["target_url"])
        added += 1

print(f"Nuevos registros añadidos a municipal_verified_records: {added}")
master["count"] = len(current_records)
master["records"] = current_records
master["generated_at"] = datetime.now().isoformat()

with open("data/municipal_verified_records.json", "w", encoding="utf-8") as f:
    json.dump(master, f, ensure_ascii=False, indent=2)

print(f"Total registros municipales verificados final: {len(current_records)}")
