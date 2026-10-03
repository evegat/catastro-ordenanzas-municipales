"""Extractor exhaustivo y verificador criptográfico de ordenanzas de Santiago Centro.

Descarga y procesa el repositorio oficial de documentos de la I. Municipalidad de Santiago (documentos.munistgo.cl):
1. Obtiene las URLs desde el sitemap oficial (wp-sitemap-posts-post-1.xml).
2. Extrae metadatos normativos (título, número, fecha, tipo de acto, materia).
3. Resuelve el PDF original embebido en el visor PDF.js.
4. Aplica la Política de Admisibilidad Documental (PAD-P090).
5. Descarga y verifica criptográficamente cada PDF calculando su hash SHA-256 inmutable.
6. Genera data/santiago/santiago_fuente_municipal.json listo para integración canónica.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = DATA_DIR / "santiago"
OUTPUT_JSON = OUTPUT_DIR / "santiago_fuente_municipal.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MESES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
}

PALABRAS_EXCLUSION_PAD = [
    "patente", "patentes", "concurso", "concursos", "premio", "premios",
    "duelo comunal", "cuenta publica", "cuentas publicas", "reavaluo",
    "sitios no edificados", "exhibicion de roles", "beca deportista",
    "juegos literarios", "subvencion", "subvenciones", "licitacion", "adjudicacion"
]

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
    if any(k in combined for k in ["artesania", "comercio", "via publica", "ambulante", "feria", "kiosko", "propaganda", "publicidad"]):
        return "comercio_publicidad", CANONICAL_AXES["comercio_publicidad"]
    if any(k in combined for k in ["ruido", "convivencia", "vecinal", "molesto", "alcohol"]):
        return "convivencia_ruidos", CANONICAL_AXES["convivencia_ruidos"]
    if any(k in combined for k in ["arbolado", "area verde", "humedal", "mascota", "animal", "tenencia responsable"]):
        return "medio_ambiente", CANONICAL_AXES["medio_ambiente"]
    if any(k in combined for k in ["cierre de calle", "tendido", "cable", "subterraneo", "aereo", "obra", "edificacion", "regulador", "espacio publico", "construccion"]):
        return "obras_espacio_publico", CANONICAL_AXES["obras_espacio_publico"]
    if any(k in combined for k in ["transito", "estacionamiento", "vehiculo", "transporte", "carga"]):
        return "transito_transporte", CANONICAL_AXES["transito_transporte"]
    if any(k in combined for k in ["participacion", "plebiscito", "consulta", "junta de vecino", "organizacion"]):
        return "organizacion_participacion", CANONICAL_AXES["organizacion_participacion"]
    if any(k in combined for k in ["seguridad", "vigilancia", "delito", "prevencion"]):
        return "seguridad_prevencion", CANONICAL_AXES["seguridad_prevencion"]
    return "derechos_tarifas", CANONICAL_AXES["derechos_tarifas"]


def parse_date(html_text: str, url: str) -> str:
    # 1. Buscar "DD de [mes] de YYYY"
    m = re.search(r'(\d{1,2})\s+de\s+([a-zA-Z]+)\s+de\s+(\d{4})', html_text)
    if m:
        dia, mes_nombre, anio = m.group(1), m.group(2).lower(), m.group(3)
        mes_num = MESES.get(mes_nombre)
        if mes_num:
            return f"{anio}-{mes_num}-{dia.zfill(2)}"
    # 2. Buscar en la URL del post o upload (ej. uploads/2025/12/...)
    m_up = re.search(r'/uploads/(\d{4})/(\d{2})/', html_text)
    if m_up:
        return f"{m_up.group(1)}-{m_up.group(2)}-01"
    # 3. Buscar año en el texto o título
    m_yr = re.search(r'\b(20[0-2][0-9])\b', url)
    if m_yr:
        return f"{m_yr.group(1)}"
    return "S/F"


def extract_numero(title: str, url: str) -> str:
    m = re.search(r'[Nn][°ºo\.\s-]*([0-9]+)', title)
    if m:
        return m.group(1)
    m2 = re.search(r'-n([0-9]+)-', url)
    if m2:
        return m2.group(1)
    return "S/N"


def main():
    print("=" * 70)
    print("EXTRACTOR Y VERIFICADOR CRIPTOGRÁFICO SANTIAGO CENTRO (P090)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sitemap_url = "https://documentos.munistgo.cl/wp-sitemap-posts-post-1.xml"
    print(f"Descargando sitemap oficial: {sitemap_url}")
    req = urllib.request.Request(sitemap_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            xml_data = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[FAIL] Error descargando sitemap: {e}")
        sys.exit(1)

    all_urls = re.findall(r'<loc>([^<]+)</loc>', xml_data)
    print(f"[INFO] Total URLs en sitemap: {len(all_urls)}")

    # Filtrar candidatos relevantes
    candidates = []
    for u in all_urls:
        u_lower = u.lower()
        if any(ex in u_lower for ex in PALABRAS_EXCLUSION_PAD):
            continue
        if any(kw in u_lower for kw in ["ordenanza", "decreto", "texto-refundido", "derechos", "aseo", "tendidos", "cierre", "norma"]):
            candidates.append(u)

    print(f"[INFO] Candidatos preliminares tras filtro PAD: {len(candidates)}")

    records = []
    admisibles = 0
    rechazados = 0
    fallidos = 0

    for idx, post_url in enumerate(candidates, 1):
        print(f"[{idx}/{len(candidates)}] Inspeccionando: {post_url}")
        try:
            req_post = urllib.request.Request(post_url, headers=HEADERS)
            with urllib.request.urlopen(req_post, timeout=12) as resp:
                post_html = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"   [WARN] No se pudo leer {post_url}: {e}")
            fallidos += 1
            continue

        # Extraer título
        title_m = re.search(r'<title>(.*?)</title>', post_html)
        raw_title = title_m.group(1) if title_m else ""
        raw_title = html.unescape(raw_title)
        # Limpiar sufijos
        clean_title = re.sub(r'\s*[-–—|]\s*Documentos\s*IMS.*$', '', raw_title, flags=re.I).strip()
        if not clean_title:
            h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', post_html, re.DOTALL)
            clean_title = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else "Ordenanza Municipal"

        title_lower = clean_title.lower()

        # Filtro estricto PAD-P090
        if any(ex in title_lower for ex in PALABRAS_EXCLUSION_PAD):
            print(f"   [SKIP] En cuarentena PAD-P090: {clean_title}")
            rechazados += 1
            continue

        # Solo admitir si explícitamente es ordenanza, reglamento o decreto normativo general
        if not any(kw in title_lower for kw in ["ordenanza", "texto refundido", "modifica ordenanza", "modificaciones a la ordenanza", "reglamento"]):
            if "decreto" in title_lower and not any(kw in title_lower for kw in ["tarifa", "derecho", "aseo", "norma"]):
                print(f"   [SKIP] Decreto no normativo: {clean_title}")
                rechazados += 1
                continue

        # Extraer URL del PDF
        pdf_url = ""
        # 1. Desde iframe PDF.js
        iframe_m = re.search(r'file=([^&#"\'\s]+)', post_html)
        if iframe_m:
            pdf_url = urllib.parse.unquote(iframe_m.group(1))
        # 2. Desde enlaces directos a .pdf
        if not pdf_url:
            pdf_links = re.findall(r'href=["\']([^"\']+\.pdf)["\']', post_html, re.I)
            if pdf_links:
                pdf_url = pdf_links[0]

        if not pdf_url:
            print(f"   [WARN] No se encontró PDF en {post_url}")
            fallidos += 1
            continue

        if pdf_url.startswith("http://"):
            pdf_url = "https://" + pdf_url[7:]

        # Codificar caracteres no ASCII en la URL del PDF (ej. ° o tildes)
        parts = urllib.parse.urlsplit(pdf_url)
        safe_path = urllib.parse.quote(parts.path)
        safe_query = urllib.parse.quote(parts.query, safe="=&")
        encoded_pdf_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, safe_path, safe_query, parts.fragment))

        # Extraer fecha y número
        fecha = parse_date(post_html, post_url)
        numero = extract_numero(clean_title, post_url)

        # Determinar tipo de norma clasif
        if "texto refundido" in title_lower:
            tipo_norma_clasif = "texto_refundido"
        elif "modifica" in title_lower:
            tipo_norma_clasif = "modificacion"
        elif "reglamento" in title_lower:
            tipo_norma_clasif = "reglamento"
        else:
            tipo_norma_clasif = "ordenanza_base"

        # Clasificar materia
        mat_id, mat_nombre = classify_topic(clean_title, post_html[:500])

        # Descarga y verificación SHA-256
        print(f"   Descargando PDF: {encoded_pdf_url}")
        try:
            req_pdf = urllib.request.Request(encoded_pdf_url, headers=HEADERS)
            with urllib.request.urlopen(req_pdf, timeout=20) as r_pdf:
                pdf_bytes = r_pdf.read()
                http_status = r_pdf.status
                content_type = r_pdf.headers.get("Content-Type", "application/pdf")
        except Exception as e:
            print(f"   [WARN] Error descargando PDF {encoded_pdf_url}: {e}")
            fallidos += 1
            continue

        if not pdf_bytes.startswith(b"%PDF-"):
            print(f"   [WARN] Encabezado no válido de PDF para {pdf_url}")
            fallidos += 1
            continue

        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        byte_size = len(pdf_bytes)
        verified_at = datetime.now(timezone.utc).isoformat()

        record = {
            "comuna": "Santiago",
            "region_id": "13",
            "region_nombre": "Metropolitana de Santiago",
            "cplt_code": "MU308",
            "fuente": "Municipalidad",
            "categoria_carpeta": "Documentos Oficiales IMS",
            "tipo_acto": "Ordenanza" if "ordenanza" in title_lower else ("Reglamento" if "reglamento" in title_lower else "Decreto Alcaldicio"),
            "denominacion_acto": clean_title,
            "numero": numero,
            "fecha": fecha,
            "titulo": clean_title,
            "descripcion": clean_title,
            "tipo_norma_clasif": tipo_norma_clasif,
            "materia": mat_nombre,
            "materia_id": mat_id,
            "source_listing_url": post_url,
            "target_url": pdf_url,
            "verification": {
                "status": "verified",
                "http_status": http_status,
                "resolved_url": pdf_url,
                "content_type": content_type,
                "sha256": sha256,
                "bytes": byte_size,
                "verified_at": verified_at
            }
        }
        records.append(record)
        admisibles += 1
        print(f"   [OK] {numero} ({fecha}): {clean_title[:60]}... -> SHA-256: {sha256[:12]} ({byte_size} bytes)")
        time.sleep(0.3)

    # Consolidar JSON final
    output_data = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comuna": "Santiago",
            "cplt_code": "MU308",
            "total_candidatos_analizados": len(candidates),
            "admisibles_verificados": len(records),
            "rechazados_pad": rechazados,
            "fallidos": fallidos,
            "cobertura_anios": f"{min([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}-{max([r['fecha'][:4] for r in records if len(r['fecha'])>=4], default='S/F')}"
        },
        "records": records
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"[EXITO] Extracción completada para Santiago Centro:")
    print(f"  - Documentos admitidos y verificados con SHA-256: {len(records)}")
    print(f"  - Rechazados por PAD-P090: {rechazados}")
    print(f"  - Fallidos técnicos: {fallidos}")
    print(f"  - Archivo guardado: {OUTPUT_JSON}")
    print("=" * 70)


if __name__ == "__main__":
    main()
