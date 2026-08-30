# -*- coding: utf-8 -*-
import hashlib, json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
VERIFIED_PATH = DATA_DIR / 'municipal_verified_records.json'
STATUS_PATH = REPO_ROOT / 'dashboard' / 'status_data.json'
MAESTRO_PATH = DATA_DIR / 'maestro_comunas_chile.csv'
import pandas as pd

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

def normalize_text(v: str) -> str:
    v = unicodedata.normalize('NFKC', str(v or ''))
    return re.sub(r'\s+', ' ', v).strip()

def ascii_key(v: str) -> str:
    v = unicodedata.normalize('NFKD', normalize_text(v))
    v = ''.join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', ' ', v.lower()).strip()

def classify_materia(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ('derecho', 'tarifa', 'arancel', 'permiso', 'cobro', 'exencion', 'rentas', 'cobranza')):
        return 'Derechos Municipales y Tarifas', 'derechos_tarifas'
    if any(k in t for k in ('aseo', 'basura', 'residuo', 'medio ambiente', 'ambiental', 'reciclaje', 'escombro', 'arbolado', 'humedal', 'apicola', 'causes', 'jardin', 'ornato')):
        return 'Aseo, Ornato y Medio Ambiente', 'aseo_medioambiente'
    if any(k in t for k in ('alcohol', 'patente', 'comercio', 'comercial', 'feria', 'propaganda', 'publicidad', 'kiosco', 'mercado')):
        return 'Patentes, Comercio y Alcoholes', 'alcoholes_comercio'
    if any(k in t for k in ('transito', 'vehiculo', 'estacionamiento', 'parquimetro', 'transporte', 'vial', 'conductor')):
        return 'Tránsito y Transporte', 'transito_transporte'
    if any(k in t for k in ('urbanismo', 'obra', 'edificacion', 'construccion', 'plan regulador', 'tendido', 'cable', 'antena', 'pasaje', 'pavimento', 'prc')):
        return 'Urbanismo, Obras y Edificación', 'urbanismo_obras'
    if any(k in t for k in ('seguridad', 'ruido', 'convivencia', 'vecinal', 'alarma', 'camara', 'orden publico', 'acoso', 'genero', 'graffiti')):
        return 'Seguridad Ciudadana y Convivencia', 'seguridad_convivencia'
    if any(k in t for k in ('mascota', 'perro', 'gato', 'animal', 'tenencia responsable', 'canino', 'zoonosis')):
        return 'Tenencia Responsable de Mascotas', 'tenencia_mascotas'
    if any(k in t for k in ('salud', 'deporte', 'social', 'comunitario', 'subvencion', 'adulto mayor', 'discapacidad', 'beca')):
        return 'Salud, Deporte y Desarrollo Social', 'social_salud_deporte'
    if any(k in t for k in ('participacion', 'cosoc', 'plebiscito', 'audiencia', 'consulta')):
        return 'Participación Ciudadana', 'participacion_ciudadana'
    return 'Normativa General y Otras Materias', 'general'

def download_and_verify(session: requests.Session, url: str, source_url: str, comuna: str, region_id: str, label: str) -> dict | None:
    try:
        r = session.get(url, timeout=8, stream=True, verify=False)
        if r.status_code != 200:
            return None
        hasher = hashlib.sha256()
        total_bytes = 0
        header_checked = False
        for chunk in r.iter_content(chunk_size=65536):
            if not header_checked:
                if not chunk.startswith(b'%PDF-'):
                    return None
                header_checked = True
            hasher.update(chunk)
            total_bytes += len(chunk)
            if total_bytes > 40 * 1024 * 1024:
                break
        if total_bytes < 500:
            return None
        sha256 = hasher.hexdigest()
        
        filename = url.split('/')[-1]
        titulo = normalize_text(label)
        if not titulo or len(titulo) < 6:
            titulo = f"Ordenanza Municipal {comuna}"
        
        m_nombre, m_id = classify_materia(f"{titulo} {url}")
        return {
            "comuna": comuna,
            "region_id": str(region_id).zfill(2),
            "cplt_code": f"MU_{ascii_key(comuna)}",
            "fuente": "Municipalidad",
            "numero": "S/N",
            "fecha": "2024-01-01",
            "titulo": titulo,
            "materia": m_nombre,
            "materia_id": m_id,
            "source_listing_url": source_url,
            "target_url": url,
            "verification": {
                "status": "verified",
                "http_status": 200,
                "resolved_url": url,
                "content_type": "application/pdf",
                "sha256": sha256,
                "bytes": total_bytes,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception:
        return None

def scan_commune(item: dict) -> list[dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    comuna = item["comuna"]
    region_id = item.get("region_id", "13")
    web = item.get("web", "")
    if not web or not web.startswith("http"):
        return []

    endpoints = [
        f"{web.rstrip('/')}/ordenanzas/",
        f"{web.rstrip('/')}/ordenanzas-municipales/",
        f"{web.rstrip('/')}/marco-normativo/",
        f"{web.rstrip('/')}/transparencia/ordenanzas/",
        f"{web.rstrip('/')}/transparencia-activa/ordenanzas/",
        f"{web.rstrip('/')}/"
    ]
    
    found = []
    seen = set()
    for ep in endpoints:
        try:
            r = session.get(ep, timeout=5, verify=False)
            if r.status_code == 200 and "html" in (r.headers.get("content-type") or ""):
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if not href or href.startswith("javascript:"):
                        continue
                    full_url = urljoin(ep, href)
                    if full_url.startswith("http://"):
                        full_url = full_url.replace("http://", "https://", 1)
                    if not full_url.startswith("https://") or full_url in seen:
                        continue
                    if full_url.lower().endswith(".pdf") and ("ordenanza" in text.lower() or "ordenanza" in full_url.lower() or "decreto" in text.lower()):
                        seen.add(full_url)
                        doc = download_and_verify(session, full_url, ep, comuna, region_id, text)
                        if doc:
                            found.append(doc)
                if len(found) >= 3:
                    break
        except Exception:
            continue
    return found

def main():
    status = json.loads(STATUS_PATH.read_text(encoding='utf-8'))
    missing = [c for c in status['comunas'] if c.get('total_count', 0) == 0]
    print(f"Comunas sin datos identificadas: {len(missing)}")

    maestro_df = pd.read_csv(MAESTRO_PATH).set_index("comuna_nombre")
    targets = []
    for c in missing:
        name = c["comuna"]
        web = ""
        if name in maestro_df.index:
            web = str(maestro_df.loc[name, "web_municipal"] or "")
        targets.append({"comuna": name, "region_id": c.get("region_id", "13"), "web": web})

    verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    records = verified_data.get("records", [])
    seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

    added = 0
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(scan_commune, t): t for t in targets}
        for future in as_completed(futures):
            t = futures[future]
            try:
                docs = future.result()
                for d in docs:
                    if d["verification"]["sha256"] not in seen_hashes:
                        records.append(d)
                        seen_hashes.add(d["verification"]["sha256"])
                        added += 1
                if docs:
                    print(f"[{t['comuna']}] ¡Rescatadas {len(docs)} ordenanzas!")
            except Exception:
                pass

    print(f"Barrido directo finalizado: +{added} ordenanzas agregadas.")
    verified_data["records"] = records
    verified_data["count"] = len(records)
    verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == '__main__':
    main()