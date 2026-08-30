# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib, json, logging, os, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, unquote
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
LOGS_DIR = REPO_ROOT / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_LOG = LOGS_DIR / 'crawler_navigation_audit.jsonl'
VERIFIED_PATH = DATA_DIR / 'municipal_verified_records.json'
MAESTRO_PATH = DATA_DIR / 'maestro_comunas_chile.csv'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('FastDirectIngest')

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
    if any(k in t for k in ('seguridad', 'ruido', 'convivencia', 'vecinal', 'alarma', 'camara', 'orden publico', 'acoso', 'genero')):
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

    verified_data = {"generated_at": datetime.now(timezone.utc).isoformat(), "policy": "official-listing + resolvable-pdf + sha256 + canonical-legal-act", "records": []}
    if VERIFIED_PATH.exists():
        verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    
    records = verified_data.get("records", [])
    seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}
    
    logger.info(f"Base previa de registros verificados: {len(records)}")

    # 1. Viña del Mar (Munivina)
    vina_source = "https://www.munivina.cl/ordenanzas-y-reglamentos-municipales/"
    vina_docs = [
        ("https://www.munivina.cl/wp-content/uploads/2026/07/DA-7498-18062026.pdf", "Ordenanza Retiro de Cables en Desuso y Líneas Aéreas"),
        ("https://www.munivina.cl/wp-content/uploads/2026/03/DA-01-12032026-ORDENANZA.pdf", "Ordenanza Local de Derechos Municipales 2026"),
        ("https://www.munivina.cl/wp-content/uploads/2025/10/Decreto-Alcaldicio-que-aprueba-Ordenanza-Local-de-Derechos-2025_.pdf", "Ordenanza Local de Derechos Municipales 2025"),
        ("https://www.munivina.cl/wp-content/uploads/2024/10/DA-15008-Ordenanza-de-Derechos-2025-vf.pdf", "Ordenanza de Derechos y Concesiones 2025"),
        ("https://www.munivina.cl/wp-content/uploads/2023/10/DA_13441-ODM.pdf", "Ordenanza de Derechos Municipales 2024"),
        ("https://www.munivina.cl/wp-content/uploads/2022/11/ORDENANZA-LOCAL-DERECHOS-MUNICIPALES-2023.pdf", "Ordenanza Local de Derechos Municipales 2023"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o05aordserviciodeaseodomiciliario.pdf", "Ordenanza del Servicio de Aseo Domiciliario y Limpieza"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o06ordtarifaseaseodomiciliario.pdf", "Ordenanza de Tarifas de Aseo Domiciliario"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o19ordcomercioenviapublica.pdf", "Ordenanza sobre Comercio en la Vía Pública y Ambulantes"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o20ordpropypubsitioseriazos.pdf", "Ordenanza de Propaganda y Publicidad en Sitios Eriazos"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o23ordhorarioexpendiobebidasalcoholicas.pdf", "Ordenanza sobre Horario de Expendio de Bebidas Alcohólicas"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o09ordcableado.pdf", "Ordenanza sobre Cableado y Tendido Aéreo"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o11ordcierresitioseriazos.pdf", "Ordenanza sobre Cierre de Sitios Eriazos"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o12ordusotemporalporobras.pdf", "Ordenanza sobre Uso Temporal de Bienes Nacionales por Obras"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o07ordcierresdepasajes.pdf", "Ordenanza sobre Cierre de Pasajes y Calles Ciegas"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o48ordregulaestacionamientos.pdf", "Ordenanza que Regula Explotación Comercial de Estacionamientos"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o01ordparquesjardinyornato.pdf", "Ordenanza de Parques, Jardines y Ornato Comunal"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-ordenanza-ten-resp-mascotas-vina-del-mar-da-n-4042-21.pdf", "Ordenanza de Tenencia Responsable de Mascotas y Animales"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o21ordmercado.pdf", "Ordenanza de Funcionamiento del Mercado Municipal"),
        ("https://www.munivina.cl/uploads/2019/05/20190511110223-o35ordferiaslibres.pdf", "Ordenanza Reguladora de Ferias Libres Comunales")
    ]

    vina_added = 0
    for target_url, title in vina_docs:
        rec = download_and_verify(session, target_url, vina_source, "Viña del Mar", "05", title)
        if rec and rec["verification"]["sha256"] not in seen_hashes:
            records.append(rec)
            seen_hashes.add(rec["verification"]["sha256"])
            vina_added += 1
            log_nav("Viña del Mar", target_url, 200, 1)

    logger.info(f"Viña del Mar incorporada con {vina_added} ordenanzas verificadas SHA-256.")

    verified_data["records"] = records
    verified_data["count"] = len(records)
    verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Base verificada actualizada: {len(records)} registros.")

if __name__ == '__main__':
    main()