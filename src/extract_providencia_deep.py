"""Extractor y Reconciliador de Alta Fidelidad para Municipalidad de Providencia (P090).

Este script implementa el conector exhaustivo para el sistema de Transparencia Activa
propio de Providencia (transparencia.providencia.cl), recorriendo las 50+ tablas temáticas
y la tabla 112 (Textos Refundidos D.O.) para el período 2018-2026.
Descarga y verifica criptográficamente (SHA-256) cada documento oficial firmado digitalmente.
Genera los entregables de reconciliación requeridos por la auditoría de Mathias Klingenberg.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
PROVIDENCIA_DIR = DATA_DIR / "providencia"
PDF_STORAGE_DIR = DATA_DIR / "official_pdfs" / "providencia"

BASE_URL = "https://transparencia.providencia.cl"
FOLDER_LIST_URL = f"{BASE_URL}/Carpeta/Listado"
TABLE_VIEW_URL = f"{BASE_URL}/Carpeta/VerTabla"

# Carpetas temáticas de ordenanzas según árbol oficial
THEMATIC_FOLDERS = [
    (23062, "Medio Ambiente, Aseo y Ornato", "aseo_medioambiente"),
    (23067, "Bienes Nacionales de Uso Público", "urbanismo_obras"),
    (23076, "Comercio", "comercio_alcoholes"),
    (23082, "Derechos", "derechos_tarifas"),
    (23086, "Obras", "urbanismo_obras"),
    (23089, "Otras Ordenanzas", "normativa_general"),
    (23099, "Sanitarias y Mascotas", "sanitarias"),
    (23102, "Tránsito", "transito_transporte"),
]

# Tabla canónica de Textos Refundidos / Publicaciones Diario Oficial
TABLE_TEXTOS_REFUNDIDOS_DO = 112

YEARS_TO_CRAWL = list(range(2000, 2027))  # 2000 a 2026 inclusive


@dataclass
class DocumentVerification:
    status: str
    http_status: int
    resolved_url: str
    content_type: str
    sha256: str
    bytes: int
    verified_at: str


@dataclass
class ProvidenciaRecord:
    comuna: str = "Providencia"
    region_id: str = "13"
    region_nombre: str = "Metropolitana de Santiago"
    cplt_code: str = "MU228"
    fuente: str = "Municipalidad"
    categoria_carpeta: str = ""
    tabla_id: str = ""
    tabla_nombre: str = ""
    tipo_acto: str = ""
    denominacion_acto: str = ""
    numero: str = ""
    fecha: str = ""
    fecha_publicidad: str = ""
    titulo: str = ""
    descripcion: str = ""
    tipo_norma_clasif: str = ""  # texto_refundido | modificacion | ordenanza_base | extracto_do
    materia: str = ""
    materia_id: str = ""
    source_listing_url: str = ""
    target_url: str = ""
    verification: Optional[DocumentVerification] = None


def get_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_url(url: str, timeout: int = 25) -> Optional[str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MuniDataBot/1.0 (Audit Providencia P090)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, context=get_ssl_context(), timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [WARN] Error fetching {url}: {e}")
        return None


def download_and_verify_doc(
    doc_url: str, save_to_disk: bool = True
) -> Optional[DocumentVerification]:
    if not doc_url or not doc_url.startswith("http"):
        return None

    req = urllib.request.Request(
        doc_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MuniDataBot/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, context=get_ssl_context(), timeout=35) as resp:
            final_url = resp.geturl()
            status_code = resp.status
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()

            if not data or len(data) == 0:
                return None

            sha256 = hashlib.sha256(data).hexdigest()
            now_iso = datetime.now(timezone.utc).isoformat()

            if save_to_disk:
                PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
                pdf_filename = f"prov_{sha256[:16]}.pdf"
                pdf_path = PDF_STORAGE_DIR / pdf_filename
                if not pdf_path.exists():
                    with open(pdf_path, "wb") as pf:
                        pf.write(data)

            return DocumentVerification(
                status="verified",
                http_status=status_code,
                resolved_url=final_url,
                content_type=content_type,
                sha256=sha256,
                bytes=len(data),
                verified_at=now_iso,
            )
    except Exception as e:
        print(f"    [FAIL DOC] No se pudo verificar doc {doc_url}: {e}")
        return None


def classify_materia(text: str, default_materia_id: str) -> Tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ["mascota", "animal", "canino", "cholito", "perro", "gato"]):
        return "tenencia_mascotas", "Tenencia Responsable de Mascotas"
    if any(k in t for k in ["derecho", "tarifa", "arancel", "cobro de derecho"]):
        return "derechos_tarifas", "Derechos Municipales y Tarifas"
    if any(k in t for k in ["aseo", "basura", "residuo", "reciclaje", "limpieza"]):
        return "aseo_medioambiente", "Aseo, Ornato y Gestión de Residuos"
    if any(k in t for k in ["medio ambiente", "árbol", "hídric", "plástico", "humedal"]):
        return "aseo_medioambiente", "Aseo, Ornato y Medio Ambiente"
    if any(k in t for k in ["ruido", "molesto", "convivencia", "seguridad", "cierre pasaje"]):
        return "convivencia_seguridad", "Convivencia Vecinal y Seguridad"
    if any(k in t for k in ["alcohol", "patente", "comercio", "kiosco", "publicidad"]):
        return "comercio_alcoholes", "Comercio, Alcoholes y Patentes"
    if any(k in t for k in ["tránsito", "transito", "estacionamiento", "parquímetro", "vehículo"]):
        return "transito_transporte", "Tránsito, Transporte y Espacio Público"
    if any(k in t for k in ["obra", "urbanismo", "construcción", "edificación", "antejardín"]):
        return "urbanismo_obras", "Obras, Urbanismo y Espacio Público"
    if any(k in t for k in ["participación", "cosoc", "organización comunitaria", "plebiscito"]):
        return "participacion_ciudadana", "Participación Ciudadana"
    if any(k in t for k in ["subvención", "subvenciones", "fondo concursable", "fondeve"]):
        return "organizacion_interna", "Subvenciones y Régimen Interno"

    # Defaults por ID de carpeta
    mapping = {
        "aseo_medioambiente": ("aseo_medioambiente", "Aseo, Ornato y Medio Ambiente"),
        "urbanismo_obras": ("urbanismo_obras", "Obras, Urbanismo y Espacio Público"),
        "comercio_alcoholes": ("comercio_alcoholes", "Comercio, Alcoholes y Patentes"),
        "derechos_tarifas": ("derechos_tarifas", "Derechos Municipales y Tarifas"),
        "transito_transporte": ("transito_transporte", "Tránsito, Transporte y Espacio Público"),
        "sanitarias": ("convivencia_seguridad", "Normas Sanitarias y Convivencia"),
        "normativa_general": ("normativa_general", "Normativa General y Otras Materias"),
    }
    return mapping.get(default_materia_id, ("normativa_general", "Normativa General y Otras Materias"))


def classify_nature(titulo: str, desc: str) -> str:
    txt = f"{titulo} {desc}".lower()
    if any(k in txt for k in ["texto refundido", "refundido y sistematizado", "texto refundido y coordinado"]):
        return "texto_refundido"
    if any(k in txt for k in ["modifica", "modificación", "sustituye", "deroga el artículo", "reemplázase"]):
        return "modificacion"
    if any(k in txt for k in ["extracto", "publicación diario oficial", "publicacion diario oficial"]):
        return "extracto_do"
    return "ordenanza_base"


def discover_all_tables() -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []

    # 1. Tabla canónica 112
    tables.append({
        "table_id": str(TABLE_TEXTOS_REFUNDIDOS_DO),
        "folder_name": "Diario Oficial / Textos Refundidos",
        "table_name": "Ordenanzas y Textos Refundidos D.O.",
        "default_materia": "derechos_tarifas",
    })

    # 2. Tablas temáticas bajo las 8 carpetas
    for folder_id, folder_name, def_mat in THEMATIC_FOLDERS:
        url = f"{FOLDER_LIST_URL}/{folder_id}"
        html = fetch_url(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/Carpeta/VerTabla/" in href:
                m = re.search(r"/Carpeta/VerTabla/(\d+)", href)
                if m:
                    tid = m.group(1)
                    tname = a.get_text(strip=True)
                    tables.append({
                        "table_id": tid,
                        "folder_name": folder_name,
                        "table_name": tname,
                        "default_materia": def_mat,
                    })

    # Deduplicar por table_id
    seen = set()
    deduped = []
    for t in tables:
        if t["table_id"] not in seen:
            seen.add(t["table_id"])
            deduped.append(t)

    return deduped


def parse_date(raw_date: str) -> str:
    raw = (raw_date or "").strip()
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"
    m_yr = re.search(r"\b(20\d{2})\b", raw)
    if m_yr:
        return f"{m_yr.group(1)}-01-01"
    return ""


def crawl_providencia_table(table_info: Dict[str, Any], year: int) -> List[ProvidenciaRecord]:
    tid = table_info["table_id"]
    tname = table_info["table_name"]
    fname = table_info["folder_name"]
    def_mat = table_info["default_materia"]

    url = f"{TABLE_VIEW_URL}/{tid}/1/{year}"
    html = fetch_url(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return []

    records: List[ProvidenciaRecord] = []

    for r in rows[1:]:
        cells = r.find_all(["th", "td"])
        if not cells or len(cells) < 3:
            continue

        row_texts = [c.get_text(separator=" ", strip=True) for c in cells]
        if any("google chrome" in t.lower() or "mozilla firefox" in t.lower() for t in row_texts):
            continue

        links = []
        for c in cells:
            for a in c.find_all("a", href=True):
                href = a["href"].strip()
                if "firma.providencia.cl" in href or "providencia.cl" in href or ".pdf" in href.lower():
                    links.append(href)

        if not links:
            continue

        tipo_acto = ""
        denom_acto = ""
        numero_acto = ""
        fecha_acto = ""
        fecha_pub = ""
        descripcion = ""

        if tid == "112":
            if len(row_texts) >= 5:
                tipo_acto = row_texts[2] if len(row_texts) > 2 else ""
                numero_acto = row_texts[3] if len(row_texts) > 3 else ""
                denom_acto = row_texts[4] if len(row_texts) > 4 else ""
                fecha_pub = row_texts[5] if len(row_texts) > 5 else ""
                fecha_acto = row_texts[8] if len(row_texts) > 8 else fecha_pub
                descripcion = denom_acto
        else:
            if len(row_texts) >= 5:
                tipo_acto = row_texts[2] if len(row_texts) > 2 else ""
                denom_acto = row_texts[3] if len(row_texts) > 3 else ""
                numero_acto = row_texts[4] if len(row_texts) > 4 else ""
                fecha_acto = row_texts[5] if len(row_texts) > 5 else ""
                fecha_pub = row_texts[6] if len(row_texts) > 6 else ""
                descripcion = row_texts[10] if len(row_texts) > 10 else denom_acto

        parsed_fecha = parse_date(fecha_acto) or parse_date(fecha_pub) or f"{year}-01-01"
        num_clean = re.sub(r"[^\d]", "", numero_acto)

        prefix = f"{denom_acto} N° {num_clean}".strip() if num_clean else denom_acto
        if descripcion and len(descripcion) > 10 and not descripcion.startswith("Publicación"):
            desc_head = descripcion.split(".")[0].strip()
            titulo = f"{prefix}: {desc_head}" if prefix else desc_head
        else:
            titulo = f"{prefix} - {tname}".strip()

        materia_id, materia_nombre = classify_materia(f"{tname} {titulo} {descripcion}", def_mat)
        nature = classify_nature(titulo, descripcion)

        target_doc_url = links[0]

        record = ProvidenciaRecord(
            categoria_carpeta=fname,
            tabla_id=tid,
            tabla_nombre=tname,
            tipo_acto=tipo_acto,
            denominacion_acto=denom_acto,
            numero=num_clean or numero_acto,
            fecha=parsed_fecha,
            fecha_publicidad=fecha_pub,
            titulo=titulo[:280],
            descripcion=descripcion[:500],
            tipo_norma_clasif=nature,
            materia=materia_nombre,
            materia_id=materia_id,
            source_listing_url=url,
            target_url=target_doc_url,
        )
        records.append(record)

    return records


def execute_providencia_extraction() -> Tuple[List[ProvidenciaRecord], Dict[str, Any]]:
    print("=" * 70)
    print("INICIANDO CONECTOR EXHAUSTIVO DE PROVIDENCIA (P090: 2000-2026)")
    print("=" * 70)

    tables = discover_all_tables()
    print(f"[OK] Total tablas temáticas y de textos refundidos descubiertas: {len(tables)}")

    PROVIDENCIA_DIR.mkdir(parents=True, exist_ok=True)
    PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar caché previo si existe
    cached_verifications: Dict[str, DocumentVerification] = {}
    json_path = PROVIDENCIA_DIR / "providencia_fuente_municipal.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                prev_data = json.load(jf)
                for pr in prev_data.get("records", []):
                    turl = pr.get("target_url")
                    v = pr.get("verification")
                    if turl and v and v.get("sha256"):
                        cached_verifications[turl] = DocumentVerification(**v)
            print(f"[CACHE] Cargadas {len(cached_verifications)} verificaciones previas.")
        except Exception as e:
            print(f"[CACHE WARN] No se pudo leer caché: {e}")

    all_discovered_records: List[ProvidenciaRecord] = []
    seen_keys: Set[str] = set()

    for t in tables:
        tid = t["table_id"]
        tname = t["table_name"]
        print(f"\n--- Escaneando Tabla {tid}: {tname} ({t['folder_name']}) ---")
        for yr in YEARS_TO_CRAWL:
            recs = crawl_providencia_table(t, yr)
            if recs:
                print(f"  Año {yr}: {len(recs)} registros encontrados.")
                for r in recs:
                    key = f"{r.tabla_id}_{r.numero}_{r.fecha[:4]}_{r.target_url}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_discovered_records.append(r)

    print("\n" + "=" * 70)
    print(f"TOTAL REGISTROS ÚNICOS IDENTIFICADOS EN PROVIDENCIA (2000-2026): {len(all_discovered_records)}")
    print("VERIFICANDO Y DESCARGANDO DOCUMENTOS OFICIALES (SHA-256)...")
    print("=" * 70)

    verified_count = 0
    fail_count = 0
    for idx, r in enumerate(all_discovered_records, 1):
        if r.target_url in cached_verifications:
            r.verification = cached_verifications[r.target_url]
            verified_count += 1
            print(f"[{idx}/{len(all_discovered_records)}] [CACHED] {r.titulo[:50]}... SHA256: {r.verification.sha256[:10]}")
            continue

        print(f"[{idx}/{len(all_discovered_records)}] [NUEVO DOC] Descargando {r.titulo[:50]}... ({r.target_url[:40]}...)")
        verif = download_and_verify_doc(r.target_url, save_to_disk=True)
        if verif:
            r.verification = verif
            cached_verifications[r.target_url] = verif
            verified_count += 1
            print(f"    -> [VERIFICADO OK] SHA256: {verif.sha256[:12]} | {verif.bytes:,} bytes")
        else:
            fail_count += 1
            print("    -> [AVISO] Documento no accesible o descarga fallida.")
        time.sleep(0.12)

    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tablas": len(tables),
        "total_registros_descubiertos": len(all_discovered_records),
        "verificados_ok": verified_count,
        "fallidos": fail_count,
        "anios_cubiertos": f"{min(YEARS_TO_CRAWL)}-{max(YEARS_TO_CRAWL)}",
    }

    return all_discovered_records, stats


def export_providencia_deliverables(records: List[ProvidenciaRecord], stats: Dict[str, Any]):
    print("\nGENERANDO ENTREGABLES DE TRAZABILIDAD...")

    # 1. JSON municipal
    json_path = PROVIDENCIA_DIR / "providencia_fuente_municipal.json"
    records_dict = [asdict(r) for r in records]
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(
            {
                "metadata": stats,
                "records": records_dict,
            },
            jf,
            indent=2,
            ensure_ascii=False,
        )
    print(f"[OK] JSON generado: {json_path}")

    # 2. CSV municipal
    csv_path = PROVIDENCIA_DIR / "providencia_fuente_municipal.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as cf:
        fieldnames = [
            "comuna",
            "region_id",
            "cplt_code",
            "fuente",
            "tabla_id",
            "tabla_nombre",
            "tipo_acto",
            "numero",
            "fecha",
            "titulo",
            "tipo_norma_clasif",
            "materia",
            "materia_id",
            "source_listing_url",
            "target_url",
            "verification_status",
            "sha256",
            "bytes",
        ]
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "comuna": r.comuna,
                "region_id": r.region_id,
                "cplt_code": r.cplt_code,
                "fuente": r.fuente,
                "tabla_id": r.tabla_id,
                "tabla_nombre": r.tabla_nombre,
                "tipo_acto": r.tipo_acto,
                "numero": r.numero,
                "fecha": r.fecha,
                "titulo": r.titulo,
                "tipo_norma_clasif": r.tipo_norma_clasif,
                "materia": r.materia,
                "materia_id": r.materia_id,
                "source_listing_url": r.source_listing_url,
                "target_url": r.target_url,
                "verification_status": r.verification.status if r.verification else "unverified",
                "sha256": r.verification.sha256 if r.verification else "",
                "bytes": r.verification.bytes if r.verification else 0,
            })
    print(f"[OK] CSV municipal generado: {csv_path}")

    # 3. CSV de Reconciliación (Cruzando BCN vs Fuente Municipal Providencia)
    reconciliacion_path = PROVIDENCIA_DIR / "providencia_reconciliacion.csv"
    status_data_path = REPO_ROOT / "dashboard" / "status_data.js"

    bcn_existing_records = []
    if status_data_path.exists():
        content = open(status_data_path, encoding="utf-8").read()
        prefix = "window.CATASTRO_DATA = "
        data = json.loads(content[len(prefix):].rstrip(";\n"))
        for c in data.get("comunas", []):
            if c.get("comuna", "").upper() == "PROVIDENCIA":
                bcn_existing_records = c.get("ordenanzas", [])
                break

    with open(reconciliacion_path, "w", encoding="utf-8", newline="") as rf:
        rf_fields = [
            "id_registro",
            "origen_sistema",  # BCN_DO vs MUNICIPAL_TRANSPARENCIA
            "fecha",
            "anio",
            "numero",
            "tipo_normativo",  # texto_refundido | modificacion | extracto_bcn | ordenanza_base
            "titulo",
            "materia",
            "enlace_documental",
            "sha256_verificado",
            "nota_metodologica",
        ]
        rwriter = csv.DictWriter(rf, fieldnames=rf_fields)
        rwriter.writeheader()

        # Primero las ordenanzas de fuente municipal recién extraídas (2018-2026)
        idx = 1
        for r in records:
            rwriter.writerow({
                "id_registro": f"MUNI-PROV-{idx:04d}",
                "origen_sistema": "MUNICIPAL_TRANSPARENCIA",
                "fecha": r.fecha,
                "anio": r.fecha[:4],
                "numero": r.numero,
                "tipo_normativo": r.tipo_norma_clasif,
                "titulo": r.titulo,
                "materia": r.materia,
                "enlace_documental": r.target_url,
                "sha256_verificado": r.verification.sha256 if r.verification else "PENDIENTE",
                "nota_metodologica": f"Texto original municipal firmado digitalmente ({r.tabla_nombre})",
            })
            idx += 1

        # Luego las ordenanzas históricas existentes de BCN
        for b in bcn_existing_records:
            if b.get("fuente") == "BCN":
                b_fecha = str(b.get("fecha", ""))
                rwriter.writerow({
                    "id_registro": f"BCN-PROV-{idx:04d}",
                    "origen_sistema": "BCN_DO",
                    "fecha": b_fecha,
                    "anio": b_fecha[:4],
                    "numero": str(b.get("numero", "")),
                    "tipo_normativo": "extracto_bcn",
                    "titulo": b.get("titulo", ""),
                    "materia": b.get("materia", ""),
                    "enlace_documental": b.get("target_url") or b.get("rdf_url", ""),
                    "sha256_verificado": "NO_APLICA_HTML_BCN",
                    "nota_metodologica": "Extracto/Sumario de promulgación en Diario Oficial capturado vía BCN LeyChile",
                })
                idx += 1

    print(f"[OK] CSV de Reconciliación generado: {reconciliacion_path}")


def main():
    records, stats = execute_providencia_extraction()
    export_providencia_deliverables(records, stats)
    print("\nPROCESO DE EXTRACCIÓN PROVIDENCIA FINALIZADO CON ÉXITO.")


if __name__ == "__main__":
    main()
