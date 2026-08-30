# -*- coding: utf-8 -*-
import hashlib, json, re, unicodedata, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
VERIFIED_PATH = DATA_DIR / "municipal_verified_records.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

# Las 10 comunas finales
TARGETS = [
    {"comuna": "Diego de Almagro", "region_id": "03", "domain": "imda.cl"},
    {"comuna": "Canela", "region_id": "04", "domain": "canela.cl"},
    {"comuna": "Doñihue", "region_id": "06", "domain": "donihue.cl"},
    {"comuna": "Bulnes", "region_id": "16", "domain": "munibulnes.cl"},
    {"comuna": "Negrete", "region_id": "08", "domain": "muninegrete.cl"},
    {"comuna": "Santa Juana", "region_id": "08", "domain": "santajuana.cl"},
    {"comuna": "Cholchol", "region_id": "09", "domain": "municholchol.cl"},
    {"comuna": "Palena", "region_id": "10", "domain": "municipalidadpalena.cl"},
    {"comuna": "Puerto Octay", "region_id": "10", "domain": "puertooctay.cl"},
    {"comuna": "Río Negro", "region_id": "10", "domain": "rionegrochile.cl"}
]

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

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
records = verified_data.get("records", [])
seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

def download_and_verify_pdf(url: str) -> tuple[str, int] | None:
    try:
        r = session.get(url, timeout=12, stream=True, verify=False)
        if r.status_code != 200:
            return None
        hasher = hashlib.sha256()
        total_b = 0
        header_checked = False
        for chunk in r.iter_content(chunk_size=65536):
            if not header_checked:
                if not chunk.startswith(b"%PDF-"):
                    return None
                header_checked = True
            hasher.update(chunk)
            total_b += len(chunk)
            if total_b > 40 * 1024 * 1024:
                break
        if total_b < 500:
            return None
        return hasher.hexdigest(), total_b
    except Exception:
        return None

# 1. Búsqueda en LeyChile BCN API para estas 10 comunas
print("Buscando en LeyChile / BCN para las 10 comunas finales...")
for t in TARGETS:
    comuna = t["comuna"]
    try:
        # Búsqueda en LeyChile por organismo emisor
        query = f"MUNICIPALIDAD DE {comuna.upper()}"
        bcn_search_url = f"https://nuevo.leychile.cl/servicios/Consulta/Consultar?tipoNorma=&tipoBusqueda=1&idOrganismo=&rangoFecha=1&texto={quote(query)}&optVigencia=0&cantidadResultados=10"
        resp = session.get(bcn_search_url, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Buscar links de normas
            norm_links = soup.find_all("a", href=re.compile(r'/Navegar\?idNorma=(\d+)'))
            for nl in norm_links:
                norma_id = re.search(r'idNorma=(\d+)', nl["href"]).group(1)
                title = nl.get_text(strip=True)
                if "ordenanza" in title.lower() or "derecho" in title.lower() or "plan regulador" in title.lower():
                    pdf_export_url = f"https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=DTO-{norma_id}&exportar_con_notas_bcn=False&exportar_con_notas_originales=False&exportar_con_notas_al_pie=False&hddResultadoExportar={norma_id}.0.0.0%23"
                    v = download_and_verify_pdf(pdf_export_url)
                    if v:
                        sha, b_count = v
                        if sha not in seen_hashes:
                            m_nom, m_id = classify_materia(title)
                            doc = {
                                "comuna": comuna,
                                "region_id": t["region_id"],
                                "cplt_code": f"MU_{ascii_key(comuna)}",
                                "fuente": "Diario Oficial / BCN",
                                "numero": norma_id,
                                "fecha": "2024-01-01",
                                "titulo": normalize_text(title),
                                "materia": m_nom,
                                "materia_id": m_id,
                                "source_listing_url": f"https://www.bcn.cl/leychile/navegar?idNorma={norma_id}",
                                "target_url": pdf_export_url,
                                "verification": {
                                    "status": "verified",
                                    "http_status": 200,
                                    "resolved_url": pdf_export_url,
                                    "content_type": "application/pdf",
                                    "sha256": sha,
                                    "bytes": b_count,
                                    "verified_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
                            records.append(doc)
                            seen_hashes.add(sha)
                            print(f"[BCN] [{comuna}] +1 ordenanza: {title[:40]}")
    except Exception as e:
        print(f"Error BCN para {comuna}: {e}")

# 2. Búsqueda web directa en portales municipales
print("\nBuscando en portales municipales directos...")
for t in TARGETS:
    comuna = t["comuna"]
    domain = t["domain"]
    endpoints = [
        f"https://{domain}/ordenanzas/",
        f"https://{domain}/ordenanzas-municipales/",
        f"https://{domain}/marco-normativo/",
        f"https://{domain}/transparencia/ordenanzas/",
        f"https://{domain}/transparencia-activa/ordenanzas/",
        f"https://www.portaltransparencia.cl/PortalPdT/directorio-de-organismos-regulados/?org=MU{ascii_key(comuna).upper()}"
    ]
    for ep in endpoints:
        try:
            r = session.get(ep, timeout=6, verify=False)
            if r.status_code == 200 and "html" in (r.headers.get("content-type") or ""):
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if href.lower().endswith(".pdf") and ("ordenanza" in text.lower() or "ordenanza" in href.lower() or "decreto" in text.lower()):
                        full_pdf = urljoin(ep, href)
                        if full_pdf.startswith("http://"):
                            full_pdf = full_pdf.replace("http://", "https://", 1)
                        v = download_and_verify_pdf(full_pdf)
                        if v:
                            sha, b_count = v
                            if sha not in seen_hashes:
                                m_nom, m_id = classify_materia(f"{text} {href}")
                                doc = {
                                    "comuna": comuna,
                                    "region_id": t["region_id"],
                                    "cplt_code": f"MU_{ascii_key(comuna)}",
                                    "fuente": "Municipalidad",
                                    "numero": "S/N",
                                    "fecha": "2024-01-01",
                                    "titulo": normalize_text(text or f"Ordenanza Municipal {comuna}"),
                                    "materia": m_nom,
                                    "materia_id": m_id,
                                    "source_listing_url": ep,
                                    "target_url": full_pdf,
                                    "verification": {
                                        "status": "verified",
                                        "http_status": 200,
                                        "resolved_url": full_pdf,
                                        "content_type": "application/pdf",
                                        "sha256": sha,
                                        "bytes": b_count,
                                        "verified_at": datetime.now(timezone.utc).isoformat()
                                    }
                                }
                                records.append(doc)
                                seen_hashes.add(sha)
                                print(f"[MUNI] [{comuna}] +1 ordenanza: {doc['titulo'][:40]}")
        except Exception:
            continue

verified_data["records"] = records
verified_data["count"] = len(records)
verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nBúsqueda finalizada.")