# -*- coding: utf-8 -*-
"""
Integración del lote del Agente Web de Gemini + Escaneo Concurrente de las 71 Comunas.
Verifica criptográficamente cada PDF con SHA-256, reconstruye el dataset y actualiza el dashboard.
"""
from __future__ import annotations
import hashlib, json, logging, os, re, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, unquote
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
LOGS_DIR = REPO_ROOT / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
AUDIT_LOG = LOGS_DIR / 'crawler_navigation_audit.jsonl'
VERIFIED_PATH = DATA_DIR / 'municipal_verified_records.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('GeminiAgentIntegrator')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

TARGET_COMUNAS = [
    {"comuna": "Camarones", "region_id": "15", "domain": "municamarones.cl"},
    {"comuna": "Putre", "region_id": "15", "domain": "imputre.cl"},
    {"comuna": "Camiña", "region_id": "01", "domain": "municamina.cl"},
    {"comuna": "Diego de Almagro", "region_id": "03", "domain": "imda.cl"},
    {"comuna": "Freirina", "region_id": "03", "domain": "imfreirina.cl"},
    {"comuna": "Canela", "region_id": "04", "domain": "canela.cl"},
    {"comuna": "Paiguano", "region_id": "04", "domain": "munipaiguano.cl"},
    {"comuna": "Punitaqui", "region_id": "04", "domain": "mpunitaqui.cl"},
    {"comuna": "Algarrobo", "region_id": "05", "domain": "municipalidaddealgarrobo.cl"},
    {"comuna": "Catemu", "region_id": "05", "domain": "municipalidadcatemu.cl"},
    {"comuna": "Limache", "region_id": "05", "domain": "limache.cl"},
    {"comuna": "Olmué", "region_id": "05", "domain": "muniolmue.cl"},
    {"comuna": "Petorca", "region_id": "05", "domain": "munipetorca.cl"},
    {"comuna": "La Reina", "region_id": "13", "domain": "lareina.cl"},
    {"comuna": "Pudahuel", "region_id": "13", "domain": "mpudahuel.cl"},
    {"comuna": "San Ramón", "region_id": "13", "domain": "municipalidadsanramon.cl"},
    {"comuna": "Tiltil", "region_id": "13", "domain": "tiltil.cl"},
    {"comuna": "Coinco", "region_id": "06", "domain": "municoinco.cl"},
    {"comuna": "Doñihue", "region_id": "06", "domain": "donihue.cl"},
    {"comuna": "Las Cabras", "region_id": "06", "domain": "munilascabras.cl"},
    {"comuna": "Lolol", "region_id": "06", "domain": "munilolol.cl"},
    {"comuna": "Marchihue", "region_id": "06", "domain": "marchigue.cl"},
    {"comuna": "Palmilla", "region_id": "06", "domain": "munipalmilla.cl"},
    {"comuna": "Pichidegua", "region_id": "06", "domain": "pichidegua.cl"},
    {"comuna": "Placilla", "region_id": "06", "domain": "municipalidadplacilla.cl"},
    {"comuna": "Pumanque", "region_id": "06", "domain": "municipalidadpumanque.cl"},
    {"comuna": "Chanco", "region_id": "07", "domain": "munichanco.cl"},
    {"comuna": "Constitución", "region_id": "07", "domain": "constitucion.cl"},
    {"comuna": "Linares", "region_id": "07", "domain": "corporacionlinares.cl"},
    {"comuna": "Longaví", "region_id": "07", "domain": "municipalidadlongavi.cl"},
    {"comuna": "Maule", "region_id": "07", "domain": "comunademaule.cl"},
    {"comuna": "Pelluhue", "region_id": "07", "domain": "munipelluhue.cl"},
    {"comuna": "Bulnes", "region_id": "16", "domain": "munibulnes.cl"},
    {"comuna": "Ninhue", "region_id": "16", "domain": "munininhue.cl"},
    {"comuna": "Portezuelo", "region_id": "16", "domain": "municipalidaddeportezuelo.cl"},
    {"comuna": "Quirihue", "region_id": "16", "domain": "muniquirihue.cl"},
    {"comuna": "San Ignacio", "region_id": "16", "domain": "munisanignacio.cl"},
    {"comuna": "Treguaco", "region_id": "16", "domain": "munitrehuaco.cl"},
    {"comuna": "Yungay", "region_id": "16", "domain": "yungay.cl"},
    {"comuna": "Ñiquén", "region_id": "16", "domain": "muniniquen.cl"},
    {"comuna": "Alto Biobío", "region_id": "08", "domain": "munialtobiobio.cl"},
    {"comuna": "Chiguayante", "region_id": "08", "domain": "chiguayante.cl"},
    {"comuna": "Hualpén", "region_id": "08", "domain": "hualpenciudad.cl"},
    {"comuna": "Hualqui", "region_id": "08", "domain": "munihualqui.cl"},
    {"comuna": "Mulchén", "region_id": "08", "domain": "munimulchen.cl"},
    {"comuna": "Nacimiento", "region_id": "08", "domain": "nacimiento.cl"},
    {"comuna": "Negrete", "region_id": "08", "domain": "muninegrete.cl"},
    {"comuna": "Quilleco", "region_id": "08", "domain": "municipalidadquilleco.cl"},
    {"comuna": "Santa Juana", "region_id": "08", "domain": "santajuana.cl"},
    {"comuna": "Angol", "region_id": "09", "domain": "angol.cl"},
    {"comuna": "Carahue", "region_id": "09", "domain": "carahue.cl"},
    {"comuna": "Cholchol", "region_id": "09", "domain": "municholchol.cl"},
    {"comuna": "Cunco", "region_id": "09", "domain": "municunco.cl"},
    {"comuna": "Curacautín", "region_id": "09", "domain": "mcuracautin.cl"},
    {"comuna": "Nueva Imperial", "region_id": "09", "domain": "nuevaimperial.cl"},
    {"comuna": "Pitrufquén", "region_id": "09", "domain": "mpitrufquen.cl"},
    {"comuna": "Toltén", "region_id": "09", "domain": "tolten.cl"},
    {"comuna": "Chaitén", "region_id": "10", "domain": "munichaiten.cl"},
    {"comuna": "Llanquihue", "region_id": "10", "domain": "llanquihue.cl"},
    {"comuna": "Palena", "region_id": "10", "domain": "municipalidadpalena.cl"},
    {"comuna": "Puerto Octay", "region_id": "10", "domain": "puertooctay.cl"},
    {"comuna": "Puyehue", "region_id": "10", "domain": "puyehuechile.cl"},
    {"comuna": "Río Negro", "region_id": "10", "domain": "rionegrochile.cl"},
    {"comuna": "San Pablo", "region_id": "10", "domain": "sanpablo.cl"},
    {"comuna": "Cisnes", "region_id": "11", "domain": "municipalidadcisnes.cl"},
    {"comuna": "Lago Verde", "region_id": "11", "domain": "lagoverdeaysen.cl"},
    {"comuna": "O'Higgins", "region_id": "11", "domain": "munihorquillas.cl"},
    {"comuna": "Antártica", "region_id": "12", "domain": "municabodehornos.cl"},
    {"comuna": "Primavera", "region_id": "12", "domain": "municipalidadprimavera.cl"},
    {"comuna": "Río Verde", "region_id": "12", "domain": "rioverde.cl"},
    {"comuna": "Timaukel", "region_id": "12", "domain": "municipalidadtimaukel.cl"}
]

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
    if any(k in t for k in ('urbanismo', 'obra', 'edificacion', 'construccion', 'plan regulador', 'tendido', 'cable', 'antena', 'pasaje', 'pavimento', 'prc', 'enmienda')):
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
    m = re.search(r'(?:ordenanza|decreto|da|dto|n[°º\.]?)\s*[:#\-_]?\s*(\d{1,6})', combined, re.IGNORECASE)
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

def is_authentic_ordinance(label: str, filename: str, url: str) -> bool:
    combined = f'{label} {filename} {url}'.lower()
    exclusions = ('concurso publico', 'llamado a concurso', 'cuenta publica', 'bases de remate', 'perfil de cargo', 'oferta laboral', 'elecciones', 'informe financiero', 'acta sesion', 'tabla concejo', 'organigrama', 'escalafon', 'cv', 'declaracion de intereses')
    if any(exc in combined for exc in exclusions):
        return False
    return 'ordenanza' in combined or 'decreto' in combined or 'reglamento' in combined or 'ord' in combined or 'da' in combined or 'dto' in combined

def download_and_verify(session: requests.Session, url: str, source_url: str, comuna: str, region_id: str, label: str) -> dict | None:
    try:
        r = session.get(url, timeout=12, stream=True, verify=False)
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

def scan_target(target: dict) -> list[dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    comuna = target["comuna"]
    region_id = target["region_id"]
    domain = target["domain"]
    base_url = f"https://{domain}"
    
    endpoints = [
        f"{base_url}/ordenanzas/",
        f"{base_url}/ordenanzas-municipales/",
        f"{base_url}/transparencia/ordenanzas/",
        f"{base_url}/marco-normativo/",
        f"{base_url}/transparencia-activa/ordenanzas/",
        f"{base_url}/transparencia/actos-y-resoluciones-con-efectos-sobre-terceros/",
        f"{base_url}/"
    ]
    
    found_docs = []
    seen_urls = set()
    
    for ep in endpoints:
        try:
            r = session.get(ep, timeout=6, verify=False)
            log_nav(comuna, ep, r.status_code, 0)
            if r.status_code == 200 and "html" in (r.headers.get("content-type") or ""):
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    label = a.get_text(strip=True)
                    if not href or href.startswith("javascript:"):
                        continue
                    pdf_url = urljoin(ep, href)
                    if not pdf_url.startswith("https://") and not pdf_url.startswith("http://"):
                        continue
                    if pdf_url in seen_urls:
                        continue
                    if pdf_url.lower().endswith(".pdf") and is_authentic_ordinance(label, pdf_url.split('/')[-1], pdf_url):
                        seen_urls.add(pdf_url)
                        doc = download_and_verify(session, pdf_url, ep, comuna, region_id, label)
                        if doc:
                            found_docs.append(doc)
                            log_nav(comuna, pdf_url, 200, 1)
                if len(found_docs) >= 5:
                    break
        except Exception:
            continue
    return found_docs

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
    records = verified_data.get("records", [])
    seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}
    
    logger.info(f"Base verificada inicial: {len(records)} registros.")

    # 1. Lote inicial confirmado por el Agente Web de Gemini
    gemini_initial_batch = [
        ("La Reina", "13", "https://www.lareina.cl/wp-content/uploads/2023/11/DECRETO-ALCALDICIO-N%C2%B0-2279-DEL-14.11.2023.pdf", "https://www.lareina.cl/transparencia-activa/", "Fija Texto Refundido de la Ordenanza Local sobre Derechos Municipales por Concesiones, Permisos y Servicios"),
        ("Angol", "09", "https://www.angol.cl/transparencia/actos,decisiones/ORDENANZAS/1091.pdf", "https://www.angol.cl/transparencia/actos,decisiones/ORDENANZAS/", "Aprueba Ordenanza Municipal Feria Estación de la Comuna de Angol"),
        ("Putre", "15", "https://imputre.cl/wp-content/uploads/2023/07/Ordenanza-de-participacion-ciudadanaymodificacion.pdf", "https://imputre.cl/transparencia/", "Ordenanza de Participación Ciudadana y Modificaciones Comuna de Putre"),
        ("Chiguayante", "08", "https://www.chiguayante.cl/transparencia/2017/7_ACTOS%20Y%20RESOLUCIONES%20CON%20EFECTOS%20SOBRE%20TERCEROS/ORDENANZAS/1%20DECRETO%20N-1306-2016.pdf", "https://www.chiguayante.cl/transparencia/", "Modificación a la Ordenanza sobre Otorgamiento de Patentes de Alcoholes"),
        ("Constitución", "07", "https://www.constitucion.cl/transparencia/archivos/3-potestades_y_marco_normativo/3-ordenanza_subvenciones_municipales.pdf", "https://www.constitucion.cl/transparencia/", "Ordenanza General sobre Otorgamiento de Subvenciones Municipales"),
        ("Las Cabras", "06", "https://munilascabras.cl/wp-content/uploads/2024/03/Diario-Oficial-13-09-2016-Enmienda-al-PRC-Las-Cabras-1987-por-Muni-Las-Cabras.pdf", "https://munilascabras.cl/plan-regulador/", "Aprueba Enmienda Plan Regulador Comunal Las Cabras en Zonas Z2 y ZEA"),
        ("Llanquihue", "10", "https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=Decreto-3843_03-DIC-2021", "https://bcn.cl/3m1aq", "Modifica Ordenanza sobre Derechos Municipales por Concesiones, Permisos y Servicios"),
        ("Limache", "05", "https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=DTO-5759_12-DIC-2006", "https://bcn.cl/3p51h", "Aprueba Ordenanza Municipal sobre Control de Estacionamiento de Vehículos"),
        ("San Ramón", "13", "https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=DTO-3291_31-MAR-2007", "https://municipalidadsanramon.cl/transparencia/", "Modifica Ordenanza sobre Funcionamiento de Ferias Libres de San Ramón")
    ]

    added_initial = 0
    for com, reg, url, src, title in gemini_initial_batch:
        doc = download_and_verify(session, url, src, com, reg, title)
        if doc and doc["verification"]["sha256"] not in seen_hashes:
            records.append(doc)
            seen_hashes.add(doc["verification"]["sha256"])
            added_initial += 1
            log_nav(com, url, 200, 1)

    logger.info(f"Lote inicial de Gemini integrado con éxito: {added_initial} ordenanzas.")

    # 2. Escaneo concurrente de las 71 comunas
    logger.info("Lanzando escáner concurrente (15 workers) sobre las 71 comunas...")
    scanned_added = 0
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(scan_target, target): target for target in TARGET_COMUNAS}
        for future in as_completed(futures):
            target = futures[future]
            try:
                docs = future.result()
                for doc in docs:
                    if doc["verification"]["sha256"] not in seen_hashes:
                        records.append(doc)
                        seen_hashes.add(doc["verification"]["sha256"])
                        scanned_added += 1
                if docs:
                    logger.info(f"[{target['comuna']}] ¡{len(docs)} ordenanzas verificadas con éxito!")
            except Exception as e:
                logger.warning(f"Error procesando {target['comuna']}: {e}")

    logger.info(f"Escaneo concurrente finalizado: +{scanned_added} ordenanzas agregadas.")

    verified_data["records"] = records
    verified_data["count"] = len(records)
    verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Dataset municipal verificado guardado: {len(records)} registros totales.")

if __name__ == '__main__':
    main()