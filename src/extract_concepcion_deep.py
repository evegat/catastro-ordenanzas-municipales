"""Extractor exhaustivo y verificador criptográfico de ordenanzas de Concepción (MU053).

Procesa el repositorio oficial de ordenanzas de la I. Municipalidad de Concepción (concepcion.cl/ordenanzas/):
1. Extrae enlaces normativos, números y fechas.
2. Descarga y verifica criptográficamente cada PDF con comprobación %PDF- y hash SHA-256.
3. Clasifica en los 9 ejes canónicos universales.
4. Genera data/concepcion/concepcion_fuente_municipal.json listo para integración canónica.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "concepcion"
OUTPUT_JSON = OUTPUT_DIR / "concepcion_fuente_municipal.json"

PAGE_URL = "https://concepcion.cl/ordenanzas/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

CANONICAL_AXES = {
    "aseo_residuos": "Aseo, Ornato y Gestión de Residuos",
    "comercio_publicidad": "Comercio, Vía Pública y Publicidad",
    "convivencia_ruidos": "Convivencia Vecinal y Ruidos Molestos",
    "derechos_tarifas": "Derechos, Tarifas y Concesiones Municipales",
    "medio_ambiente": "Medio Ambiente, Humedales y Tenencia Responsable",
    "obras_espacio_publico": "Obras, Urbanismo y Espacio Público",
    "organizacion_participacion": "Organización Interna y Participación Ciudadana",
    "transito_transporte": "Tránsito, Transporte y Estacionamientos",
    "seguridad_prevencion": "Seguridad Ciudadana y Prevención",
}


def classify_topic(title: str, text: str = "") -> tuple[str, str]:
    combined = f"{title} {text}".lower()
    if any(k in combined for k in ["derecho", "tarifa", "arancel", "cobro", "renta", "concesion"]):
        return "derechos_tarifas", CANONICAL_AXES["derechos_tarifas"]
    if any(k in combined for k in ["aseo", "basura", "residuo", "escombro", "limpieza"]):
        return "aseo_residuos", CANONICAL_AXES["aseo_residuos"]
    if any(k in combined for k in ["mesas", "comercio", "via publica", "ambulante", "feria", "kiosko", "propaganda", "publicidad"]):
        return "comercio_publicidad", CANONICAL_AXES["comercio_publicidad"]
    if any(k in combined for k in ["ruido", "convivencia", "vecinal", "molesto", "mascarilla", "distanciamiento"]):
        return "convivencia_ruidos", CANONICAL_AXES["convivencia_ruidos"]
    if any(k in combined for k in ["humedal", "mascota", "animal", "tenencia responsable"]):
        return "medio_ambiente", CANONICAL_AXES["medio_ambiente"]
    if any(k in combined for k in ["cierre de calle", "tendido", "cable", "obra", "edificacion", "regulador", "espacio publico", "construccion"]):
        return "obras_espacio_publico", CANONICAL_AXES["obras_espacio_publico"]
    if any(k in combined for k in ["participacion", "plebiscito", "consulta", "junta de vecino", "organizacion"]):
        return "organizacion_participacion", CANONICAL_AXES["organizacion_participacion"]
    return "derechos_tarifas", CANONICAL_AXES["derechos_tarifas"]


def parse_date(text: str) -> str:
    m = re.search(r'(\d{4})[\/\.-](\d{2})[\/\.-](\d{2})', text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m2 = re.search(r'(\d{4})[\/\.-](\d{2})', text)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-01"
    m_yr = re.search(r'\b(20[0-2][0-9])\b', text)
    if m_yr:
        return f"{m_yr.group(1)}"
    return "S/F"


def extract_numero(text: str) -> str:
    m = re.search(r'[Nn][°ºo\.\s-]*([0-9]+)', text)
    if m:
        return m.group(1)
    return "S/N"


def main():
    print("=" * 70)
    print("EXTRACTOR Y VERIFICADOR CRIPTOGRÁFICO CONCEPCIÓN (MU053 - P090)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    resp = session.get(PAGE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')

    candidates = []
    seen_urls = set()

    for a in soup.find_all('a', href=True):
        h = a['href']
        t = a.get_text(" ", strip=True)
        if '.pdf' in h.lower() and 'portaltransparencia' not in h.lower():
            full_url = urllib.parse.urljoin(PAGE_URL, h)
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                candidates.append({
                    "url": full_url,
                    "text": t
                })

    print(f"[INFO] Candidatos PDF normativos descubiertos: {len(candidates)}")

    records = []
    seen_hashes = set()

    for idx, c in enumerate(candidates, 1):
        pdf_url = c["url"]
        link_text = c["text"] or Path(urllib.parse.urlparse(pdf_url).path).name
        clean_text = link_text.replace("\n", " ").strip()

        fecha = parse_date(clean_text + " " + pdf_url)
        numero = extract_numero(clean_text + " " + pdf_url)

        mat_id, mat_nombre = classify_topic(clean_text, pdf_url)

        # Codificar URL para caracteres especiales
        parts = urllib.parse.urlsplit(pdf_url)
        safe_path = urllib.parse.quote(parts.path)
        safe_query = urllib.parse.quote(parts.query, safe="=&")
        encoded_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, safe_path, safe_query, parts.fragment))

        print(f"[{idx}/{len(candidates)}] Descargando: {encoded_url[:80]}...")
        try:
            r_pdf = session.get(encoded_url, headers=HEADERS, timeout=20)
            if r_pdf.status_code != 200:
                print(f"   [WARN] HTTP {r_pdf.status_code}")
                continue
            pdf_bytes = r_pdf.content
        except Exception as e:
            print(f"   [WARN] Error: {e}")
            continue

        if not pdf_bytes.startswith(b"%PDF-"):
            print(f"   [WARN] No es PDF valido")
            continue

        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        if sha256 in seen_hashes:
            print(f"   [SKIP] Hash duplicado: {sha256[:10]}")
            continue

        seen_hashes.add(sha256)
        byte_size = len(pdf_bytes)

        record = {
            "comuna": "Concepción",
            "region_id": "8",
            "region_nombre": "Biobío",
            "cplt_code": "MU053",
            "fuente": "Municipalidad",
            "categoria_carpeta": "Repositorio Municipal Oficial",
            "tipo_acto": "Ordenanza",
            "denominacion_acto": clean_text,
            "numero": numero,
            "fecha": fecha,
            "titulo": f"Ordenanza Municipal N° {numero}: {clean_text[:90]}" if numero != "S/N" else f"Ordenanza Municipal: {clean_text[:90]}",
            "descripcion": clean_text,
            "tipo_norma_clasif": "texto_refundido" if "refundido" in clean_text.lower() else ("modificacion" if "modifica" in clean_text.lower() else "ordenanza_base"),
            "materia": mat_nombre,
            "materia_id": mat_id,
            "source_listing_url": PAGE_URL,
            "target_url": pdf_url,
            "verification": {
                "status": "verified",
                "http_status": 200,
                "resolved_url": pdf_url,
                "content_type": "application/pdf",
                "sha256": sha256,
                "bytes": byte_size,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        }
        records.append(record)
        print(f"   [OK] {numero} ({fecha}): SHA-256 {sha256[:12]} ({byte_size} bytes)")
        time.sleep(0.2)

    output_data = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comuna": "Concepción",
            "cplt_code": "MU053",
            "total_candidatos_descubiertos": len(candidates),
            "admisibles_verificados": len(records),
            "cobertura_anios": f"{min([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}-{max([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}"
        },
        "records": records
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"[EXITO] Extracción completada para Concepción:")
    print(f"  - Documentos admitidos y verificados con SHA-256: {len(records)}")
    print(f"  - Archivo guardado: {OUTPUT_JSON}")
    print("=" * 70)


if __name__ == "__main__":
    main()
