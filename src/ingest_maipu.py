# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, io, json, logging, os, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, quote
import openpyxl
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
logger = logging.getLogger('MaipuIngest')

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
    if any(k in t for k in ('derecho', 'tarifa', 'arancel', 'permiso', 'cobro', 'exencion', 'rentas', 'cobranza', 'conseciones')):
        return 'Derechos Municipales y Tarifas', 'derechos_tarifas'
    if any(k in t for k in ('aseo', 'basura', 'residuo', 'medio ambiente', 'ambiental', 'reciclaje', 'escombro', 'arbolado', 'humedal', 'apicola', 'causes', 'jardin', 'ornato', 'daoga')):
        return 'Aseo, Ornato y Medio Ambiente', 'aseo_medioambiente'
    if any(k in t for k in ('alcohol', 'patente', 'comercio', 'comercial', 'feria', 'propaganda', 'publicidad', 'kiosco', 'mercado', 'pulga')):
        return 'Patentes, Comercio y Alcoholes', 'alcoholes_comercio'
    if any(k in t for k in ('transito', 'vehiculo', 'estacionamiento', 'parquimetro', 'transporte', 'vial', 'conductor', 'restriccion')):
        return 'Tránsito y Transporte', 'transito_transporte'
    if any(k in t for k in ('urbanismo', 'obra', 'edificacion', 'construccion', 'plan regulador', 'tendido', 'cable', 'antena', 'pasaje', 'pavimento', 'cierre', 'trabajos')):
        return 'Urbanismo, Obras y Edificación', 'urbanismo_obras'
    if any(k in t for k in ('seguridad', 'ruido', 'convivencia', 'vecinal', 'alarma', 'camara', 'orden publico', 'acoso', 'genero', 'graffiti')):
        return 'Seguridad Ciudadana y Convivencia', 'seguridad_convivencia'
    if any(k in t for k in ('mascota', 'perro', 'gato', 'animal', 'tenencia responsable', 'canino', 'zoonosis')):
        return 'Tenencia Responsable de Mascotas', 'tenencia_mascotas'
    if any(k in t for k in ('salud', 'deporte', 'social', 'comunitario', 'subvencion', 'adulto mayor', 'discapacidad', 'beca', 'biblioteca')):
        return 'Salud, Deporte y Desarrollo Social', 'social_salud_deporte'
    if any(k in t for k in ('participacion', 'cosoc', 'plebiscito', 'audiencia', 'consulta')):
        return 'Participación Ciudadana', 'participacion_ciudadana'
    return 'Normativa General y Otras Materias', 'general'

def download_and_verify(session: requests.Session, url: str, source_url: str, comuna: str, region_id: str, numero: str, fecha_val: str, denominacion: str) -> dict | None:
    try:
        # Asegurar HTTPS y codificación de caracteres especiales
        safe_url = url.replace('http://', 'https://')
        r = session.get(safe_url, timeout=12, stream=True, verify=False)
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
        
        # Fecha
        fecha_str = '2024-01-01'
        if fecha_val:
            if isinstance(fecha_val, datetime):
                fecha_str = fecha_val.strftime('%Y-%m-%d')
            else:
                m = re.search(r'\b(20\d{2})[-_](\d{2})[-_](\d{2})\b', str(fecha_val))
                if m:
                    fecha_str = f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
                else:
                    m2 = re.search(r'\b(20\d{2})\b', str(fecha_val))
                    if m2:
                        fecha_str = f'{m2.group(1)}-01-01'

        titulo = normalize_text(denominacion)
        if not titulo or len(titulo) < 6:
            titulo = f"Ordenanza Municipal N° {numero} Maipú"
        
        materia_nombre, materia_id = classify_materia(f"{titulo} {safe_url}")
        
        return {
            "comuna": comuna,
            "region_id": str(region_id).zfill(2),
            "cplt_code": f"MU_{ascii_key(comuna)}",
            "fuente": "Municipalidad",
            "numero": str(numero or 'S/N'),
            "fecha": fecha_str,
            "titulo": titulo,
            "materia": materia_nombre,
            "materia_id": materia_id,
            "source_listing_url": source_url,
            "target_url": safe_url,
            "verification": {
                "status": "verified",
                "http_status": 200,
                "resolved_url": safe_url,
                "content_type": "application/pdf",
                "sha256": sha256,
                "bytes": total_bytes,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        return None

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    records = verified_data.get("records", [])
    seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

    excel_url = "https://www.transparenciamaipu.cl/wp-content/uploads/2006/04/Ordenanzas_vigentes.xlsx"
    logger.info("Descargando catálogo oficial de ordenanzas de Maipú...")
    r = session.get(excel_url, timeout=15, verify=False)
    if r.status_code != 200:
        logger.error("No se pudo descargar el Excel de Maipú")
        return

    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    ws = wb.active

    maipu_added = 0
    for row_idx, row in enumerate(ws.iter_rows(values_only=False), start=1):
        if row_idx < 3:
            continue
        vals = [c.value for c in row]
        links = [c.hyperlink.target for c in row if c.hyperlink and c.hyperlink.target]
        if not links:
            continue
        pdf_url = links[0]
        denominacion = str(vals[2] or '')
        numero = str(vals[3] or 'S/N')
        fecha_val = vals[4]

        doc = download_and_verify(session, pdf_url, excel_url, "Maipú", "13", numero, fecha_val, denominacion)
        if doc and doc["verification"]["sha256"] not in seen_hashes:
            records.append(doc)
            seen_hashes.add(doc["verification"]["sha256"])
            maipu_added += 1
            log_nav("Maipú", pdf_url, 200, 1)

    logger.info(f"¡Maipú incorporada con éxito! Total ordenanzas verificadas SHA-256: {maipu_added}")

    verified_data["records"] = records
    verified_data["count"] = len(records)
    verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == '__main__':
    main()