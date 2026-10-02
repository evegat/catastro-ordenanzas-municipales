import json
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent
STATUS_PATH = REPO_ROOT / "dashboard" / "status_data.json"
SPARQL_PATH = REPO_ROOT / "data" / "bcn_sparql_all_orz.json"

status_data = json.loads(STATUS_PATH.read_text(encoding="utf-8-sig"))
sparql_data = json.loads(SPARQL_PATH.read_text(encoding="utf-8")) if SPARQL_PATH.exists() else []

# Indexar sparql_data por (fecha, numero) y por título
sparql_by_act = defaultdict(list)
for item in sparql_data:
    orz = item.get("orz", {}).get("value", "")
    title = item.get("title", {}).get("value", "")
    date = item.get("date", {}).get("value", "")
    num = item.get("number", {}).get("value", "")
    org = item.get("org", {}).get("value", "")
    org_slug = org.split("/")[-1] if org else ""
    sparql_by_act[(date, str(num).strip().lower())].append((org_slug, title, orz))

# Recopilar URLs compartidas
url_to_records = defaultdict(list)
for comuna in status_data.get("comunas", []):
    c_name = comuna.get("comuna")
    for ord_ in comuna.get("ordenanzas", []):
        url = (ord_.get("target_url") or ord_.get("url") or "").strip()
        if url and not url.endswith("#") and len(url) > 10:
            url_to_records[url].append({
                "comuna": c_name,
                "numero": ord_.get("numero"),
                "fecha": ord_.get("fecha"),
                "titulo": ord_.get("titulo"),
                "fuente": ord_.get("fuente"),
                "rdf_url": ord_.get("rdf_url"),
                "materia": ord_.get("materia"),
                "ord_ref": ord_
            })

shared_urls = {k: v for k, v in url_to_records.items() if len(set(x["comuna"] for x in v)) > 1}
print(f"Total URLs compartidas entre más de una comuna: {len(shared_urls)}")

audit_report = []

for url, items in sorted(shared_urls.items(), key=lambda x: x[0]):
    communes = sorted(list(set(x["comuna"] for x in items)))
    fecha = items[0]["fecha"]
    num = str(items[0]["numero"]).strip().lower()
    tit = items[0]["titulo"]
    
    # Buscar en sparql
    matches = sparql_by_act.get((fecha, num), [])
    org_detected = None
    if matches:
        org_detected = matches[0][0]
    
    # Ver si en el título se menciona expresamente la comuna
    tit_upper = tit.upper()
    
    audit_report.append({
        "url": url,
        "communes": communes,
        "fecha": fecha,
        "numero": num,
        "titulo": tit,
        "org_sparql": org_detected,
        "count": len(communes)
    })

# Guardar informe para análisis
out_path = REPO_ROOT / "data" / "auditoria_149_shared_urls.json"
out_path.write_text(json.dumps(audit_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Auditoría guardada en {out_path}")

# Mostrar resumen de pares y su organismo SPARQL
by_pair = defaultdict(list)
for rep in audit_report:
    pair_key = tuple(rep["communes"])
    by_pair[pair_key].append(rep)

for pair, entries in sorted(by_pair.items(), key=lambda x: -len(x[1])):
    print(f"\nPar: {pair} -> {len(entries)} URLs")
    for e in entries[:3]:
        print(f"  URL: {e['url']} | Titulo: {e['titulo'][:50]} | Org SPARQL: {e['org_sparql']}")
