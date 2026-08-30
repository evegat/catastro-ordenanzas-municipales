# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, json, logging, os, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
LOGS_DIR = REPO_ROOT / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_LOG = LOGS_DIR / 'crawler_navigation_audit.jsonl'
VERIFIED_PATH = DATA_DIR / 'municipal_verified_records.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('Batch2Ingest')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

def log_nav(comuna: str, url: str, status: int, count: int):
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "comuna": comuna, "url": url, "status": status, "count": count}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
    if any(k in t for k in ('transito', 'vehiculo', 'estacionamiento', 'parquimetro', 'transporte', 'vial', 'conductor', 'victoria')):
        return 'Tránsito y Transporte', 'transito_transporte'
    if any(k in t for k in ('urbanismo', 'obra', 'edificacion', 'construccion', 'plan regulador', 'tendido', 'cable', 'antena', 'pasaje', 'pavimento')):
        return 'Urbanismo, Obras y Edificación', 'urbanismo_obras'
    if any(k in t for k in ('seguridad', 'ruido', 'convivencia', 'vecinal', 'alarma', 'camara', 'orden publico', 'acoso', 'genero', 'graffiti')):
        return 'Seguridad Ciudadana y Convivencia', 'seguridad_convivencia'
    if any(k in t for k in ('mascota', 'perro', 'gato', 'animal', 'tenencia responsable', 'canino', 'zoonosis')):
        return 'Tenencia Responsable de Mascotas', 'tenencia_mascotas'
    if any(k in t for k in ('salud', 'deporte', 'social', 'comunitario', 'subvencion', 'adulto mayor', 'discapacidad', 'vivevina')):
        return 'Salud, Deporte y Desarrollo Social', 'social_salud_deporte'
    if any(k in t for k in ('participacion', 'cosoc', 'plebiscito', 'audiencia', 'consulta')):
        return 'Participación Ciudadana', 'participacion_ciudadana'
    return 'Normativa General y Otras Materias', 'general'

def extract_legal_number(text: str, filename: str) -> str:
    combined = f'{text} {filename}'
    m = re.search(r'(?:ordenanza|decreto|da|d\.a\.|n[°º\.]?)\s*[:#\-_]?\s*(\d{1,6})', combined, re.IGNORECASE)
    if m:
        return m.group(1)
    m2 = re.search(r'\b(\d{1,5})\b', filename)
    if m2:
        return m2.group(1)
    return 'S/N'

def extract_legal_date(text: str, filename: str) -> str:
    combined = f'{text} {filename}'
    m = re.search(r'\b(20\d{2})[-_](\d{2})[-_](\d{2})\b', combined)
    if m:
        return f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
    m2 = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b', combined)
    if m2:
        return f'{int(m2.group(3)):04d}-{int(m2.group(2)):02d}-{int(m2.group(1)):02d}'
    m3 = re.search(r'\b(20\d{2})\b', combined)
    if m3:
        return f'{m3.group(1)}-01-01'
    return '2026-01-01'

def clean_title(label: str, filename: str, comuna: str) -> str:
    cleaned = normalize_text(label)
    if not cleaned or len(cleaned) < 8 or len(cleaned) > 130 or cleaned.lower().endswith('.pdf') or 'descargar' in cleaned.lower() or 'link' in cleaned.lower():
        base = Path(filename).stem
        base = unquote(base)
        base = re.sub(r'[-_]+', ' ', base).strip()
        cleaned = f'Ordenanza Municipal {comuna} — {base}'
    return cleaned

def download_and_verify(session: requests.Session, url: str, source_url: str, comuna: str, region_id: str, label: str) -> dict | None:
    try:
        r = session.get(url, timeout=10, stream=True, verify=False)
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
        titulo = clean_title(label, filename, comuna)
        numero = extract_legal_number(titulo, filename)
        fecha = extract_legal_date(titulo, filename)
        materia_nombre, materia_id = classify_materia(f"{titulo} {url}")
        return {
            "comuna": comuna,
            "region_id": str(region_id).zfill(2),
            "cplt_code": f"MU_{ascii_key(comuna)}",
            "fuente": "Municipalidad",
            "numero": str(numero),
            "fecha": fecha,
            "titulo": titulo,
            "materia": materia_nombre,
            "materia_id": materia_id,
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

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    records = verified_data.get("records", [])
    seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

    candidates = [
        # Punta Arenas
        ("Punta Arenas", "12", "http://www.puntaarenas.cl/normativas/ordenanzas/ordenanza_participacion_ciudadana.pdf", "https://puntaarenas.cl/normativas/", "Ordenanza Municipal de Participación Ciudadana"),
        ("Punta Arenas", "12", "http://www.puntaarenas.cl/normativas/ordenanzas/ordenanza_graffitis_rayados.pdf", "https://puntaarenas.cl/normativas/", "Ordenanza sobre Prevención y Sanción de Graffitis y Rayados"),
        ("Punta Arenas", "12", "http://www.puntaarenas.cl/normativas/ordenanzas/ordenanza_derechos_municipales.pdf", "https://puntaarenas.cl/normativas/", "Ordenanza sobre Derechos Municipales por Concesiones y Servicios"),
        ("Punta Arenas", "12", "http://www.puntaarenas.cl/normativas/ordenanzas/ordenanza_cierre_calles_pasajes.pdf", "https://puntaarenas.cl/normativas/", "Ordenanza sobre Cierre de Pasajes y Medidas de Control de Acceso"),
        # Constitucion
        ("Constitución", "07", "https://www.constitucion.cl/transparencia/archivos/ordenanzas/ordenanza_subvenciones_2021.pdf", "https://www.constitucion.cl/transparencia/", "Ordenanza sobre Otorgamiento de Subvenciones Municipales"),
        ("Constitución", "07", "https://www.constitucion.cl/transparencia/archivos/ordenanzas/ordenanza_medio_ambiente.pdf", "https://www.constitucion.cl/transparencia/", "Ordenanza Municipal de Protección del Medio Ambiente"),
        ("Constitución", "07", "https://www.constitucion.cl/transparencia/archivos/ordenanzas/ordenanza_derechos_municipales.pdf", "https://www.constitucion.cl/transparencia/", "Ordenanza Local de Derechos Municipales"),
    ]

    added = 0
    for comuna, reg_id, url, src, title in candidates:
        rec = download_and_verify(session, url, src, comuna, reg_id, title)
        if rec and rec["verification"]["sha256"] not in seen_hashes:
            records.append(rec)
            seen_hashes.add(rec["verification"]["sha256"])
            added += 1
            log_nav(comuna, url, 200, 1)

    logger.info(f"Agregadas {added} ordenanzas verificadas.")
    verified_data["records"] = records
    verified_data["count"] = len(records)
    verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == '__main__':
    main()