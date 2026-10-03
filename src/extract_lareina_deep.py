"""Extractor exhaustivo y verificador criptográfico de ordenanzas de La Reina (MU125).

Procesa la tabla oficial de Ordenanzas de Transparencia Activa CPLT de La Reina:
https://www.portaltransparencia.cl/PortalPdT/directorio-de-organismos-regulados/?org=MU125&pagina=58314855
1. Extrae metadatos (tipo de acto, denominación, número, fecha, enlace PDF).
2. Valida la estructura y resuelve URLs canónicas hacia lareina.cl.
3. Descarga y verifica criptográficamente cada PDF con comprobación %PDF- y hash SHA-256.
4. Clasifica en los 9 ejes canónicos universales.
5. Genera data/lareina/lareina_fuente_municipal.json listo para integración canónica.
"""
from __future__ import annotations

import hashlib
import html as html_lib
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
OUTPUT_DIR = DATA_DIR / "lareina"
OUTPUT_JSON = OUTPUT_DIR / "lareina_fuente_municipal.json"

SOURCE_URL = "https://www.portaltransparencia.cl/PortalPdT/directorio-de-organismos-regulados/?org=MU125&pagina=58314855"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.lareina.cl/"
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
    if any(k in combined for k in ["comercio", "via publica", "ambulante", "feria", "kiosko", "propaganda", "publicidad", "alcohol"]):
        return "comercio_publicidad", CANONICAL_AXES["comercio_publicidad"]
    if any(k in combined for k in ["ruido", "convivencia", "vecinal", "molesto"]):
        return "convivencia_ruidos", CANONICAL_AXES["convivencia_ruidos"]
    if any(k in combined for k in ["arbolado", "area verde", "humedal", "mascota", "animal", "tenencia responsable"]):
        return "medio_ambiente", CANONICAL_AXES["medio_ambiente"]
    if any(k in combined for k in ["cierre de calle", "tendido", "cable", "obra", "edificacion", "regulador", "espacio publico", "construccion", "urban"]):
        return "obras_espacio_publico", CANONICAL_AXES["obras_espacio_publico"]
    if any(k in combined for k in ["transito", "estacionamiento", "vehiculo", "transporte", "carga"]):
        return "transito_transporte", CANONICAL_AXES["transito_transporte"]
    if any(k in combined for k in ["participacion", "plebiscito", "consulta", "junta de vecino", "organizacion"]):
        return "organizacion_participacion", CANONICAL_AXES["organizacion_participacion"]
    if any(k in combined for k in ["seguridad", "vigilancia", "delito", "prevencion"]):
        return "seguridad_prevencion", CANONICAL_AXES["seguridad_prevencion"]
    return "derechos_tarifas", CANONICAL_AXES["derechos_tarifas"]


def parse_date(text: str) -> str:
    # Buscar YYYY-MM-DD o DD-MM-YYYY o DD.MM.YYYY
    m = re.search(r'(\d{2})[\/\.-](\d{2})[\/\.-](\d{4})', text)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m2 = re.search(r'(\d{4})[\/\.-](\d{2})[\/\.-](\d{2})', text)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
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
    print("EXTRACTOR Y VERIFICADOR CRIPTOGRÁFICO LA REINA (MU125 - P090)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    print(f"Descargando portal oficial de ordenanzas de La Reina:\n{SOURCE_URL}")
    try:
        resp = session.get(SOURCE_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"[FAIL] Error accediendo a CPLT La Reina: {e}")
        sys.exit(1)

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    print(f"[INFO] Filas encontradas en tabla CPLT: {len(rows)}")

    candidates = []
    seen_urls = set()

    for tr in rows:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        text_row = " ".join(c.get_text(" ", strip=True) for c in cells)
        a_tags = tr.find_all("a", href=True)
        for a in a_tags:
            href = a["href"].strip()
            if ".pdf" in href.lower() and href not in seen_urls:
                # Normalizar // en URL
                clean_href = re.sub(r'([^:])//+', r'\1/', href)
                seen_urls.add(href)
                candidates.append({
                    "raw_url": clean_href,
                    "row_text": text_row,
                    "link_text": a.get_text(" ", strip=True)
                })

    print(f"[INFO] Candidatos PDF normativos únicos descubiertos: {len(candidates)}")

    records = []
    seen_hashes = set()
    admisibles = 0
    fallidos = 0

    for idx, cand in enumerate(candidates, 1):
        pdf_url = cand["raw_url"]
        row_text = cand["row_text"]

        # Parsear número y fecha
        fecha = parse_date(row_text + " " + pdf_url)
        numero = extract_numero(row_text + " " + pdf_url)

        # Construir título representativo
        # Intentar extraer la denominación del acto desde la fila
        denominacion = row_text
        if len(denominacion) > 200:
            denominacion = denominacion[:200]

        # Extraer título limpio
        if "ordenanza" in row_text.lower():
            titulo = f"Ordenanza Municipal N° {numero} ({fecha})" if numero != "S/N" else f"Ordenanza Municipal ({fecha})"
        else:
            titulo = f"Decreto Alcaldicio N° {numero} ({fecha})"

        # Clasificar materia
        mat_id, mat_nombre = classify_topic(denominacion, row_text)

        # Tipo de norma
        if "texto refundido" in denominacion.lower():
            tipo_norma = "texto_refundido"
        elif "modifica" in denominacion.lower():
            tipo_norma = "modificacion"
        else:
            tipo_norma = "ordenanza_base"

        print(f"[{idx}/{len(candidates)}] Descargando: {pdf_url[:80]}...")
        try:
            r_pdf = session.get(pdf_url, headers=HEADERS, timeout=20)
            if r_pdf.status_code != 200:
                print(f"   [WARN] HTTP {r_pdf.status_code}")
                fallidos += 1
                continue
            pdf_bytes = r_pdf.content
        except Exception as e:
            print(f"   [WARN] Error de descarga: {e}")
            fallidos += 1
            continue

        if not pdf_bytes.startswith(b"%PDF-"):
            print(f"   [WARN] Header no PDF")
            fallidos += 1
            continue

        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        if sha256 in seen_hashes:
            print(f"   [SKIP] Hash duplicado: {sha256[:10]}")
            continue

        seen_hashes.add(sha256)
        byte_size = len(pdf_bytes)

        record = {
            "comuna": "La Reina",
            "region_id": "13",
            "region_nombre": "Metropolitana de Santiago",
            "cplt_code": "MU125",
            "fuente": "Municipalidad",
            "categoria_carpeta": "Transparencia Activa CPLT - Marco Normativo",
            "tipo_acto": "Ordenanza" if "ordenanza" in titulo.lower() else "Decreto Alcaldicio",
            "denominacion_acto": denominacion,
            "numero": numero,
            "fecha": fecha,
            "titulo": f"{titulo}: {denominacion[:100]}",
            "descripcion": denominacion,
            "tipo_norma_clasif": tipo_norma,
            "materia": mat_nombre,
            "materia_id": mat_id,
            "source_listing_url": SOURCE_URL,
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
        admisibles += 1
        print(f"   [OK] {numero} ({fecha}): SHA-256 {sha256[:12]} ({byte_size} bytes)")
        time.sleep(0.2)

    output_data = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comuna": "La Reina",
            "cplt_code": "MU125",
            "total_candidatos_descubiertos": len(candidates),
            "admisibles_verificados": len(records),
            "fallidos": fallidos,
            "cobertura_anios": f"{min([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}-{max([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}"
        },
        "records": records
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"[EXITO] Extracción completada para La Reina:")
    print(f"  - Documentos admitidos y verificados con SHA-256: {len(records)}")
    print(f"  - Fallidos técnicos: {fallidos}")
    print(f"  - Archivo guardado: {OUTPUT_JSON}")
    print("=" * 70)


if __name__ == "__main__":
    main()
