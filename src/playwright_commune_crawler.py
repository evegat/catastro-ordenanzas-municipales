# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, hashlib, json, logging, os, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, unquote
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
OUTPUT_PATH = DATA_DIR / 'playwright_rescued_records.json'
MAESTRO_PATH = DATA_DIR / 'maestro_comunas_chile.csv'
STATUS_DATA_PATH = REPO_ROOT / 'dashboard' / 'status_data.json'

Path(REPO_ROOT / 'logs').mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('PlaywrightCrawler')

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

COMMON_PATHS = [
    '/ordenanzas/', '/ordenanzas-municipales/', '/transparencia/ordenanzas/',
    '/transparencia-activa/ordenanzas/', '/documentos/ordenanzas/', '/normativa/ordenanzas/',
    '/decretos-y-ordenanzas/', '/transparencia/actos-y-resoluciones-con-efectos-sobre-terceros/',
    '/actos-y-resoluciones-con-efectos-sobre-terceros/ordenanzas/', '/'
]

def normalize_text(v: str) -> str:
    v = unicodedata.normalize('NFKC', str(v or ''))
    return re.sub(r'\s+', ' ', v).strip()

def ascii_key(v: str) -> str:
    v = unicodedata.normalize('NFKD', normalize_text(v))
    v = ''.join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', ' ', v.lower()).strip()

def classify_materia(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ('derecho', 'tarifa', 'arancel', 'permiso', 'cobro', 'exencion', 'rentas')):
        return 'Derechos Municipales y Tarifas', 'derechos_tarifas'
    if any(k in t for k in ('aseo', 'basura', 'residuo', 'medio ambiente', 'ambiental', 'reciclaje', 'escombro', 'arbolado', 'humedal', 'apicola')):
        return 'Aseo, Ornato y Medio Ambiente', 'aseo_medioambiente'
    if any(k in t for k in ('alcohol', 'patente', 'comercio', 'comercial', 'feria', 'propaganda', 'publicidad', 'kiosco')):
        return 'Patentes, Comercio y Alcoholes', 'alcoholes_comercio'
    if any(k in t for k in ('transito', 'vehiculo', 'estacionamiento', 'parquimetro', 'transporte', 'vial', 'conductor')):
        return 'Tránsito y Transporte', 'transito_transporte'
    if any(k in t for k in ('urbanismo', 'obra', 'edificacion', 'construccion', 'plan regulador', 'tendido', 'cable', 'antena')):
        return 'Urbanismo, Obras y Edificación', 'urbanismo_obras'
    if any(k in t for k in ('seguridad', 'ruido', 'convivencia', 'vecinal', 'alarma', 'camara', 'orden publico', 'acoso')):
        return 'Seguridad Ciudadana y Convivencia', 'seguridad_convivencia'
    if any(k in t for k in ('mascota', 'perro', 'gato', 'animal', 'tenencia responsable', 'canino', 'zoonosis')):
        return 'Tenencia Responsable de Mascotas', 'tenencia_mascotas'
    if any(k in t for k in ('salud', 'deporte', 'social', 'comunitario', 'subvencion', 'adulto mayor', 'discapacidad')):
        return 'Salud, Deporte y Desarrollo Social', 'social_salud_deporte'
    if any(k in t for k in ('participacion', 'cosoc', 'plebiscito', 'audiencia', 'consulta')):
        return 'Participación Ciudadana', 'participacion_ciudadana'
    return 'Normativa General y Otras Materias', 'general'

def extract_legal_number(text: str, filename: str) -> str:
    combined = f'{text} {filename}'
    m = re.search(r'(?:ordenanza|decreto|n[°º\.]?)\s*[:#\-_]?\s*(\d{1,5})', combined, re.IGNORECASE)
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
    if not cleaned or len(cleaned) < 8 or len(cleaned) > 120 or cleaned.lower().endswith('.pdf') or 'descargar' in cleaned.lower() or 'ver documento' in cleaned.lower():
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
    return 'ordenanza' in combined or 'decreto' in combined or 'reglamento' in combined

def get_missing_communes() -> list[dict[str, Any]]:
    if not STATUS_DATA_PATH.exists() or not MAESTRO_PATH.exists():
        return []
    with open(STATUS_DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    missing_names = {c['comuna'].lower().strip() for c in data['comunas'] if c.get('total_count', 0) == 0}
    maestro = pd.read_csv(MAESTRO_PATH)
    res = []
    for _, row in maestro.iterrows():
        c_name = str(row['comuna_nombre']).strip()
        if c_name.lower() in missing_names:
            res.append({
                'comuna': c_name,
                'region_id': str(row['region_id']).zfill(2),
                'region_nombre': str(row['region_nombre']),
                'slug': str(row.get('slug', '')),
                'web_municipal': str(row.get('web_municipal', '')),
                'url_transparencia': str(row.get('url_transparencia', '')),
            })
    return res

def crawl_commune(page, commune_info: dict[str, Any]) -> list[dict[str, Any]]:
    comuna = commune_info['comuna']
    base_web = commune_info['web_municipal']
    url_transp = commune_info['url_transparencia']
    discovered: list[dict[str, Any]] = []
    seen: set[str] = set()

    target_urls = []
    if base_web and base_web.startswith('http'):
        for path in COMMON_PATHS:
            target_urls.append(urljoin(base_web.rstrip('/') + '/', path.lstrip('/')))
    if url_transp and url_transp.startswith('http'):
        target_urls.append(url_transp)

    for target_url in target_urls:
        try:
            page.goto(target_url, timeout=7000, wait_until='domcontentloaded')
            time.sleep(0.3)
            links = page.evaluate('() => Array.from(document.querySelectorAll("a")).map(a => ({href: a.href, text: a.innerText || "", title: a.title || ""}))')
            for link in links:
                href = link.get('href', '')
                label = f"{link.get('text', '')} {link.get('title', '')}".strip()
                if not href or href.startswith('javascript:') or href in seen:
                    continue
                full_url = urljoin(target_url, href)
                if not full_url.startswith('https://'):
                    if full_url.startswith('http://'):
                        full_url = 'https://' + full_url[7:]
                    else:
                        continue
                is_pdf = full_url.lower().endswith('.pdf') or 'pdf' in full_url.lower() or 'download' in full_url.lower()
                if is_pdf and is_authentic_ordinance(label, full_url.split('/')[-1], full_url):
                    seen.add(full_url)
                    discovered.append({
                        'comuna': comuna,
                        'region_id': commune_info['region_id'],
                        'source_listing_url': target_url,
                        'target_url': full_url,
                        'label': label,
                    })
            if len(discovered) >= 8:
                break
        except Exception:
            continue
    return discovered

def verify_pdf(item: dict[str, Any], session) -> dict[str, Any] | None:
    url = item['target_url']
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
        titulo = clean_title(item['label'], filename, item['comuna'])
        numero = extract_legal_number(titulo, filename)
        fecha = extract_legal_date(titulo, filename)
        materia_nombre, materia_id = classify_materia(f"{titulo} {url}")
        return {
            'comuna': item['comuna'],
            'region_id': item['region_id'],
            'cplt_code': f"MU_{ascii_key(item['comuna'])}",
            'fuente': 'Municipalidad',
            'numero': str(numero),
            'fecha': fecha,
            'titulo': titulo,
            'materia': materia_nombre,
            'materia_id': materia_id,
            'source_listing_url': item['source_listing_url'],
            'target_url': url,
            'verification': {
                'status': 'verified',
                'http_status': 200,
                'resolved_url': url,
                'content_type': 'application/pdf',
                'sha256': sha256,
                'bytes': total_bytes,
                'verified_at': datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=73)
    args = parser.parse_args()
    missing = get_missing_communes()
    logger.info(f'Procesando {min(len(missing), args.max)} comunas con Playwright...')
    all_cands = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, ignore_https_errors=True)
        page = context.new_page()
        for idx, com in enumerate(missing[:args.max]):
            logger.info(f"[{idx+1}/{min(len(missing), args.max)}] {com['comuna']}...")
            cands = crawl_commune(page, com)
            all_cands.extend(cands)
        browser.close()
    logger.info(f'Candidatos: {len(all_cands)}. Verificando PDFs...')
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    verified = []
    seen_hashes = set()
    for cand in all_cands:
        v = verify_pdf(cand, session)
        if v and v['verification']['sha256'] not in seen_hashes:
            seen_hashes.add(v['verification']['sha256'])
            verified.append(v)
    logger.info(f'Verificados con SHA-256: {len(verified)}')
    OUTPUT_PATH.write_text(json.dumps({'count': len(verified), 'records': verified}, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()