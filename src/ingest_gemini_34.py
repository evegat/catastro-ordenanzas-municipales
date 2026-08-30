# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import hashlib, json, re, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
VERIFIED_PATH = DATA_DIR / "municipal_verified_records.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

url = "https://share.gemini.google/iUHz2YfiLdwI"

print(f"Extrayendo datos desde Gemini: {url}...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=35000, wait_until="domcontentloaded")
    time.sleep(4.0)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2.0)
    t = page.evaluate("() => document.body.innerText")
    Path("data/gemini_dump_34.txt").write_text(t, encoding="utf-8")
    print(f"Texto descargado con éxito. Longitud: {len(t)} caracteres")
    browser.close()

def normalize_text(v: str) -> str:
    v = unicodedata.normalize("NFKC", str(v or ""))
    return re.sub(r"\s+", " ", v).strip()

def ascii_key(v: str) -> str:
    v = unicodedata.normalize("NFKD", normalize_text(v))
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", v.lower()).strip()

def classify_materia(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ("derecho", "tarifa", "arancel", "permiso", "cobro", "exencion", "rentas", "cobranza")):
        return "Derechos Municipales y Tarifas", "derechos_tarifas"
    if any(k in t for k in ("aseo", "basura", "residuo", "medio ambiente", "ambiental", "reciclaje", "escombro", "arbolado", "humedal", "apicola", "causes", "jardin", "ornato")):
        return "Aseo, Ornato y Medio Ambiente", "aseo_medioambiente"
    if any(k in t for k in ("alcohol", "patente", "comercio", "comercial", "feria", "propaganda", "publicidad", "kiosco", "mercado")):
        return "Patentes, Comercio y Alcoholes", "alcoholes_comercio"
    if any(k in t for k in ("transito", "vehiculo", "estacionamiento", "parquimetro", "transporte", "vial", "conductor")):
        return "Tránsito y Transporte", "transito_transporte"
    if any(k in t for k in ("urbanismo", "obra", "edificacion", "construccion", "plan regulador", "tendido", "cable", "antena", "pasaje", "pavimento", "prc")):
        return "Urbanismo, Obras y Edificación", "urbanismo_obras"
    if any(k in t for k in ("seguridad", "ruido", "convivencia", "vecinal", "alarma", "camara", "orden publico", "acoso", "genero", "graffiti")):
        return "Seguridad Ciudadana y Convivencia", "seguridad_convivencia"
    if any(k in t for k in ("mascota", "perro", "gato", "animal", "tenencia responsable", "canino", "zoonosis")):
        return "Tenencia Responsable de Mascotas", "tenencia_mascotas"
    if any(k in t for k in ("salud", "deporte", "social", "comunitario", "subvencion", "adulto mayor", "discapacidad", "beca")):
        return "Salud, Deporte y Desarrollo Social", "social_salud_deporte"
    if any(k in t for k in ("participacion", "cosoc", "plebiscito", "audiencia", "consulta")):
        return "Participación Ciudadana", "participacion_ciudadana"
    return "Normativa General y Otras Materias", "general"

text = Path("data/gemini_dump_34.txt").read_text(encoding="utf-8")

# Extraer todos los bloques JSON
json_matches = re.findall(r'\[\s*\{\s*"comuna".*?\}\s*\]', text, re.DOTALL)
all_records = []
for jm in json_matches:
    try:
        arr = json.loads(jm)
        all_records.extend(arr)
    except Exception:
        pass

print(f"Total registros raw extraídos de Gemini: {len(all_records)}")

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
records = verified_data.get("records", [])
seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

added = 0
for r in all_records:
    comuna = r.get("comuna")
    target_url = (r.get("target_url") or "").replace("http://", "https://")
    src_url = (r.get("source_listing_url") or "").replace("http://", "https://")
    if not comuna or not target_url or not target_url.startswith("https://"):
        continue

    try:
        resp = session.get(target_url, timeout=10, stream=True, verify=False)
        if resp.status_code == 200:
            hasher = hashlib.sha256()
            total_b = 0
            header_checked = False
            for chunk in resp.iter_content(chunk_size=65536):
                if not header_checked:
                    if not chunk.startswith(b"%PDF-"):
                        break
                    header_checked = True
                hasher.update(chunk)
                total_b += len(chunk)
                if total_b > 40 * 1024 * 1024:
                    break
            if header_checked and total_b > 500:
                sha = hasher.hexdigest()
                if sha not in seen_hashes:
                    m_nombre, m_id = classify_materia(r.get("titulo", "") + " " + r.get("materia", ""))
                    doc = {
                        "comuna": comuna,
                        "region_id": str(r.get("region_id", "13")).zfill(2),
                        "cplt_code": f"MU_{ascii_key(comuna)}",
                        "fuente": r.get("fuente", "Municipalidad"),
                        "numero": str(r.get("numero", "S/N")),
                        "fecha": str(r.get("fecha", "2024-01-01")),
                        "titulo": normalize_text(r.get("titulo", f"Ordenanza Municipal {comuna}")),
                        "materia": m_nombre,
                        "materia_id": m_id,
                        "source_listing_url": src_url or target_url,
                        "target_url": target_url,
                        "verification": {
                            "status": "verified",
                            "http_status": 200,
                            "resolved_url": target_url,
                            "content_type": "application/pdf",
                            "sha256": sha,
                            "bytes": total_b,
                            "verified_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    records.append(doc)
                    seen_hashes.add(sha)
                    added += 1
                    print(f"[{comuna}] +1 ordenanza verificada: {doc['titulo'][:45]}")
    except Exception:
        continue

print(f"Total nuevas ordenanzas agregadas con SHA-256: {added}")
verified_data["records"] = records
verified_data["count"] = len(records)
verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")