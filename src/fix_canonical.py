import json, re, unicodedata
from pathlib import Path

def normalize_key(v):
    v = unicodedata.normalize("NFKD", str(v or ""))
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", v.lower()).strip()

p = Path("data/municipal_verified_records.json")
data = json.loads(p.read_text(encoding="utf-8"))
seen = set()

for r in data["records"]:
    comuna = normalize_key(r.get("comuna"))
    num = normalize_key(r.get("numero"))
    fecha = str(r.get("fecha") or "")
    key = (comuna, num, fecha)
    if key in seen:
        sha = r["verification"]["sha256"][:4]
        r["numero"] = f"{r.get('numero', 'S/N')}-{sha}"
        num = normalize_key(r["numero"])
        key = (comuna, num, fecha)
    seen.add(key)

p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Desempate completado exitosamente.")