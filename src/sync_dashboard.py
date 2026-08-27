"""
Sincronizador en tiempo real entre la base SQLite de ordenanzas y el dashboard visual.
Actualiza status_data.json y status_data.js.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/catastro_ordenanzas.db")
DASHBOARD_JSON = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.json")
DASHBOARD_JS = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.js")

def sync_dashboard():
    if not DB_PATH.exists():
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get counts by source
    cursor.execute("SELECT fuente, COUNT(*) FROM ordenanzas GROUP BY fuente")
    source_counts = dict(cursor.fetchall())

    # Get counts by commune
    cursor.execute("""
        SELECT comuna_nombre, 
               SUM(CASE WHEN fuente = 'BCN' THEN 1 ELSE 0 END) as bcn_cnt,
               SUM(CASE WHEN fuente = 'CPLT' THEN 1 ELSE 0 END) as cplt_cnt,
               SUM(CASE WHEN pdf_path IS NOT NULL AND pdf_path != '' THEN 1 ELSE 0 END) as pdf_cnt,
               COUNT(*) as total_cnt
        FROM ordenanzas
        GROUP BY comuna_nombre
    """)
    commune_db = {r[0].lower(): {"bcn": r[1], "cplt": r[2], "pdf": r[3], "total": r[4]} for r in cursor.fetchall()}
    conn.close()

    # Read current status data to preserve regions
    if DASHBOARD_JSON.exists():
        with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        return

    # Update communes in data
    total_ordenanzas = 0
    total_pdfs = 0
    comunas_con_datos = 0

    for c in data.get("comunas", []):
        c_norm = c["comuna"].lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
        # match in DB
        db_match = None
        for k, v in commune_db.items():
            k_norm = k.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
            if c_norm in k_norm or k_norm in c_norm:
                db_match = v
                break

        if db_match:
            c["bcn_count"] = max(c["bcn_count"], db_match["bcn"])
            c["cplt_count"] = db_match["cplt"]
            c["pdfs_count"] = db_match["pdf"]
            c["total_count"] = c["bcn_count"] + c["cplt_count"]
            if c["total_count"] > 0:
                c["status"] = "Completado" if c["cplt_count"] > 0 else "Cargado BCN"

        if c["total_count"] > 0:
            comunas_con_datos += 1
            total_ordenanzas += c["total_count"]
            total_pdfs += c["pdfs_count"]

    data["updated_at"] = datetime.now().isoformat()
    data["metrics"]["comunas_con_datos"] = comunas_con_datos
    data["metrics"]["total_ordenanzas"] = total_ordenanzas
    data["metrics"]["ordenanzas_bcn"] = source_counts.get("BCN", data["metrics"]["ordenanzas_bcn"])
    data["metrics"]["ordenanzas_cplt"] = source_counts.get("CPLT", 0)
    data["metrics"]["pdfs_descargados"] = total_pdfs

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(DASHBOARD_JS, "w", encoding="utf-8") as f:
        f.write("window.CATASTRO_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard sincronizado: {total_ordenanzas} ordenanzas, {comunas_con_datos}/346 comunas.")

if __name__ == "__main__":
    sync_dashboard()
