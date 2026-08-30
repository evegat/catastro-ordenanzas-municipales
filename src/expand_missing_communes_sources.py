"""Expand coverage for missing municipalities via direct official source crawling.

1. Probes the 129 missing communes using master URLs, common municipal ordinance paths,
   and transparency portals.
2. Discovers official PDF documents, downloads them, validates PDF structure (%PDF-),
   and calculates SHA-256 hashes.
3. Extracts and normalizes legal metadata (Comuna, Número, Fecha, Título, Materia).
4. Emits verified documentary evidence ready for promotion into `municipal_verified_records.json`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "missing_communes_extraction.json"

USER_AGENT = "P090-Ordenanzas-Crawler/1.2 (+https://github.com/evegat/catastro-ordenanzas-municipales)"
TIMEOUT = 12
MAX_PDF_BYTES = 50 * 1024 * 1024

COMMON_PATHS = [
    "/ordenanzas/",
    "/ordenanzas-municipales/",
    "/transparencia/ordenanzas/",
    "/transparencia/ordenanzas.html",
    "/transparencia-activa/ordenanzas/",
    "/transparencia/actos-y-resoluciones-con-efectos-sobre-terceros/",
    "/transparencia/actos_terceros_ordenanzas.htm",
    "/documentos/ordenanzas/",
    "/normativa/ordenanzas/",
    "/decretos-y-ordenanzas/",
    "/portal/ordenanzas/",
    "/",
]

ALIASES = {
    "paiguano": "paihuano",
    "llaillay": "llay llay",
    "marchihue": "marchige",
    "treguaco": "trehuaco",
    "o higgins": "ohiggins",
    "ohiggins": "ohiggins",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\ufeff", "").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def ascii_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", normalize_text(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def classify_materia(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ("derecho", "tarifa", "arancel", "permiso", "cobro", "exencion")):
        return "Derechos Municipales y Tarifas", "derechos_tarifas"
    if any(k in t for k in ("aseo", "basura", "residuo", "medio ambiente", "ambiental", "reciclaje", "escombro", "arbolado", "humedal")):
        return "Aseo, Ornato y Medio Ambiente", "aseo_medioambiente"
    if any(k in t for k in ("alcohol", "patente", "comercio", "comercial", "feria", "propaganda", "publicidad", "kiosco")):
        return "Patentes, Comercio y Alcoholes", "alcoholes_comercio"
    if any(k in t for k in ("transito", "vehiculo", "estacionamiento", "parquimetro", "transporte", "vial", "conductor")):
        return "Tránsito y Transporte", "transito_transporte"
    if any(k in t for k in ("urbanismo", "obra", "edificacion", "construccion", "plan regulador", "tendido", "cable", "antena")):
        return "Urbanismo, Obras y Edificación", "urbanismo_obras"
    if any(k in t for k in ("seguridad", "ruido", "convivencia", "vecinal", "alarma", "camara", "orden publico")):
        return "Seguridad Ciudadana y Convivencia", "seguridad_convivencia"
    if any(k in t for k in ("mascota", "perro", "gato", "animal", "tenencia responsable", "canino", "zoonosis")):
        return "Tenencia Responsable de Mascotas", "tenencia_mascotas"
    return "Normativa General y Otras Materias", "general"


def extract_legal_number(text: str, filename: str) -> str:
    combined = f"{text} {filename}"
    m = re.search(r"(?:ordenanza|decreto|n[°º\.]?)\s*[:#\-]?\s*(\d+)", combined, re.IGNORECASE)
    if m:
        return m.group(1)
    m2 = re.search(r"\b(\d{1,5})\b", filename)
    if m2:
        return m2.group(1)
    return "S/N"


def extract_legal_date(text: str, filename: str) -> str:
    combined = f"{text} {filename}"
    m = re.search(r"\b(20\d{2})[-_](\d{2})[-_](\d{2})\b", combined)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m2 = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b", combined)
    if m2:
        d = int(m2.group(1))
        mo = int(m2.group(2))
        y = int(m2.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m3 = re.search(r"\b(20\d{2})\b", combined)
    if m3:
        return f"{m3.group(1)}-01-01"
    return "2026-01-01"


def clean_title(label: str, filename: str, comuna: str) -> str:
    cleaned = normalize_text(label)
    if not cleaned or len(cleaned) < 8 or cleaned.lower().endswith(".pdf") or "descargar" in cleaned.lower() or "ver archivo" in cleaned.lower():
        base = Path(filename).stem
        base = re.sub(r"[-_]+", " ", base)
        cleaned = f"Ordenanza Municipal {comuna} ({base.strip()})"
    return cleaned


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/pdf,*/*"})
    return s


def is_ordinance_link(text: str, href: str) -> bool:
    combined = f"{text} {href}".lower()
    return "ordenanza" in combined or "decreto" in combined or "reglamento" in combined


def verify_and_hash_pdf(session: requests.Session, url: str) -> dict[str, Any] | None:
    try:
        resp = session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
        if resp.status_code != 200:
            return None
        
        content_type = (resp.headers.get("content-type") or "").split(";", 1)[0].lower()
        if not ("pdf" in content_type or "octet-stream" in content_type or url.lower().endswith(".pdf")):
            return None

        hasher = hashlib.sha256()
        total_bytes = 0
        header_checked = False
        
        for chunk in resp.iter_content(chunk_size=65536):
            if not header_checked:
                if not chunk.startswith(b"%PDF-"):
                    return None
                header_checked = True
            
            hasher.update(chunk)
            total_bytes += len(chunk)
            if total_bytes > MAX_PDF_BYTES:
                return None
        
        if total_bytes == 0:
            return None

        return {
            "status": "verified",
            "http_status": 200,
            "resolved_url": resp.url,
            "content_type": "application/pdf",
            "sha256": hasher.hexdigest(),
            "bytes": total_bytes,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return None


def crawl_missing_commune(commune_info: dict[str, Any]) -> list[dict[str, Any]]:
    comuna = commune_info["comuna"]
    region_id = commune_info.get("region_id", "13")
    cplt_code = commune_info.get("cplt_code", "MU000")
    base_url = commune_info.get("web_municipal", "")
    
    if not base_url:
        return []

    session = make_session()
    discovered_pdfs = []
    seen_pdf_urls = set()
    seen_hashes = set()

    paths_to_check = [base_url]
    for p in COMMON_PATHS:
        paths_to_check.append(urljoin(base_url, p))

    visited_pages = set()
    
    for page_url in paths_to_check:
        if page_url in visited_pages:
            continue
        visited_pages.add(page_url)

        try:
            r = session.get(page_url, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200 or "html" not in (r.headers.get("content-type") or ""):
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar links en <a>
            for a in soup.find_all("a", href=True):
                href = urljoin(r.url, a.get("href"))
                text = " ".join(a.stripped_strings)
                
                if href in seen_pdf_urls:
                    continue

                if href.lower().endswith(".pdf") or "pdf" in href.lower() or is_ordinance_link(text, href):
                    if is_ordinance_link(text, href) or "ordenanza" in href.lower():
                        seen_pdf_urls.add(href)
                        
                        verif = verify_and_hash_pdf(session, href)
                        if verif and verif["sha256"] not in seen_hashes:
                            seen_hashes.add(verif["sha256"])
                            
                            filename = href.split("/")[-1]
                            titulo = clean_title(text, filename, comuna)
                            numero = extract_legal_number(titulo, filename)
                            fecha = extract_legal_date(titulo, filename)
                            materia_nombre, materia_id = classify_materia(f"{titulo} {href}")

                            discovered_pdfs.append({
                                "comuna": comuna,
                                "region_id": str(region_id).zfill(2),
                                "cplt_code": cplt_code,
                                "fuente": "Municipalidad",
                                "numero": str(numero),
                                "fecha": fecha,
                                "titulo": titulo,
                                "materia": materia_nombre,
                                "materia_id": materia_id,
                                "source_listing_url": page_url,
                                "target_url": verif["resolved_url"],
                                "verification": verif,
                            })
        except Exception:
            continue

    return discovered_pdfs


def run_expansion(max_workers: int = 12, out_path: Path = DEFAULT_OUT) -> list[dict[str, Any]]:
    with open(REPO_ROOT / "dashboard" / "status_data.json", encoding="utf-8") as f:
        status_data = json.load(f)
    missing_communes = [c for c in status_data["comunas"] if c["total_count"] == 0]

    with open(REPO_ROOT / "data" / "cplt_municipal_directory.json", encoding="utf-8") as f:
        cplt_dir = json.load(f)
    cplt_by_key = {ascii_key(m["municipality_key"]): m for m in cplt_dir["municipalities"]}

    with open(REPO_ROOT / "data" / "maestro_comunas_chile.csv", encoding="utf-8-sig") as f:
        master = list(csv.DictReader(f))
    master_by_key = {ascii_key(r["comuna_nombre"]): r for r in master}

    targets = []
    for c in missing_communes:
        k = ascii_key(c["comuna"])
        lookup_key = ALIASES.get(k, k)
        cplt = cplt_by_key.get(lookup_key)
        if not cplt:
            for ck, cv in cplt_by_key.items():
                if ck == lookup_key or ck in lookup_key or lookup_key in ck:
                    cplt = cv
                    break
        m_row = master_by_key.get(k) or master_by_key.get(lookup_key)
        
        targets.append({
            "comuna": c["comuna"],
            "region_id": c.get("region_id") or (m_row.get("region_id") if m_row else "13"),
            "cplt_code": cplt["cplt_code"] if cplt else "MU000",
            "web_municipal": m_row["web_municipal"] if m_row else f"https://www.municipalidad{k}.cl",
        })

    print(f"Starting expansion crawl for {len(targets)} missing municipalities using {max_workers} threads...")
    all_discovered = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_missing_commune, t): t["comuna"] for t in targets}
        for future in as_completed(futures):
            comuna_name = futures[future]
            try:
                records = future.result()
                if records:
                    print(f"  [FOUND] {comuna_name}: {len(records)} verified ordinance PDFs")
                    all_discovered.extend(records)
                else:
                    print(f"  [EMPTY] {comuna_name}: 0 documents found in standard paths")
            except Exception as e:
                print(f"  [ERROR] {comuna_name}: {e}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "MW-P090-0010-EXPANSION",
        "policy": "direct-probe + resolvable-pdf + sha256 + canonical-legal-act",
        "count": len(all_discovered),
        "records": all_discovered,
    }
    out_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nExpansion complete: {len(all_discovered)} verified PDFs discovered across missing municipalities.")
    return all_discovered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    run_expansion(args.workers, args.out)


if __name__ == "__main__":
    main()
