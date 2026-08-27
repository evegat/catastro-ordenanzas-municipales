"""
Módulo de ingesta masiva de textos y metadatos BCN (1.572 registros).
Guarda en SQLite y sincroniza el dashboard en tiempo real.
"""

import os
import csv
import json
import sqlite3
import logging
from pathlib import Path
from anti_blocking import PoliteSession
from sync_dashboard import sync_dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BCNFetcher")

DB_PATH = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/catastro_ordenanzas.db")
CATALOGO_CSV = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/ordenanzas_municipales_bcn_catalogo.csv")
TEXTOS_DIR = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/bcn_textos")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEXTOS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordenanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fuente TEXT,
            norma_uri TEXT UNIQUE,
            municipalidad_slug TEXT,
            comuna_nombre TEXT,
            fecha_publicacion TEXT,
            numero TEXT,
            titulo TEXT,
            materia TEXT,
            texto_completo TEXT,
            rdf_json_url TEXT,
            rdf_xml_url TEXT,
            pdf_url TEXT,
            pdf_path TEXT,
            estado TEXT,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def run_bcn_ingest(batch_size: int = None):
    conn = init_db()
    cursor = conn.cursor()
    session = PoliteSession(min_delay=0.8, max_delay=1.8)

    if not CATALOGO_CSV.exists():
        logger.error(f"No se encontró {CATALOGO_CSV}")
        return

    with open(CATALOGO_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Total registros en catálogo BCN: {len(rows)}")
    
    # Check already completed in DB
    cursor.execute("SELECT norma_uri FROM ordenanzas WHERE fuente = 'BCN'")
    existing_uris = set(r[0] for r in cursor.fetchall())
    logger.info(f"Registros ya existentes en SQLite: {len(existing_uris)}")

    pending_rows = [r for r in rows if r.get("norma") not in existing_uris]
    logger.info(f"Registros pendientes por procesar: {len(pending_rows)}")

    if batch_size:
        pending_rows = pending_rows[:batch_size]

    processed = 0
    for r in pending_rows:
        norma_uri = r.get("norma", "")
        slug = r.get("municipalidad_slug", "")
        fecha = r.get("fecha_publicacion_uri", "")
        num = r.get("numero_uri", "")
        rdf_json = r.get("rdf_json", "")
        rdf_xml = r.get("rdf_xml", "")

        comuna_nombre = slug.replace("municipalidad-de-", "").replace("municipalidad-", "").replace("-", " ").title()
        titulo = f"Ordenanza Municipal N° {num} - {comuna_nombre}"

        # Fetch RDF JSON
        resp = session.get(rdf_json)
        if resp and resp.status_code == 200:
            try:
                data = resp.json()
                safe_slug = f"{slug}_{fecha}_{num}".replace("/", "_").replace("\\", "_")
                json_file = TEXTOS_DIR / f"{safe_slug}.json"
                with open(json_file, "w", encoding="utf-8") as jf:
                    json.dump(data, jf, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Error parsing JSON for {norma_uri}: {e}")

        cursor.execute("""
            INSERT OR REPLACE INTO ordenanzas 
            (fuente, norma_uri, municipalidad_slug, comuna_nombre, fecha_publicacion, numero, titulo, rdf_json_url, rdf_xml_url, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("BCN", norma_uri, slug, comuna_nombre, fecha, num, titulo, rdf_json, rdf_xml, "PROCESADO_BCN"))
        conn.commit()

        processed += 1
        if processed % 20 == 0:
            logger.info(f"Progreso BCN: {processed}/{len(pending_rows)} procesados...")
            sync_dashboard()

    conn.close()
    sync_dashboard()
    logger.info(f"Ingesta BCN finalizada exitosamente ({processed} nuevos procesados).")

if __name__ == "__main__":
    run_bcn_ingest()
