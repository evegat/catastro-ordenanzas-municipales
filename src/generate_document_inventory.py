import json
import sqlite3
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DASHBOARD_DIR = REPO_ROOT / "dashboard"
DOCS_DIR = REPO_ROOT / "docs"
SRC_DIR = REPO_ROOT / "src"
DATASETS_DIR = Path(r"D:\Datasets\P090 - BCN Ordenanzas municipales")

def inspect_status_data(path: Path) -> dict:
    if not path.exists():
        return {"error": "status_data.json no encontrado"}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    metrics = data.get("metrics", {})
    comunas = data.get("comunas", [])
    
    total_records = 0
    fuentes_counter = Counter()
    sha256_records = 0
    densidad_comunas = []

    for c in comunas:
        ords = c.get("ordenanzas", [])
        total_records += len(ords)
        densidad_comunas.append((c.get("comuna", ""), len(ords)))
        for o in ords:
            f = o.get("fuente", "sin_fuente")
            fuentes_counter[f] += 1
            v = o.get("verification")
            if isinstance(v, dict) and v.get("sha256"):
                sha256_records += 1

    low_density = [item for item in densidad_comunas if 1 <= item[1] <= 3]
    one_norm = [item for item in densidad_comunas if item[1] == 1]
    two_norms = [item for item in densidad_comunas if item[1] == 2]
    three_norms = [item for item in densidad_comunas if item[1] == 3]

    return {
        "updated_at": data.get("updated_at"),
        "declared_metrics": metrics,
        "total_comunas": len(comunas),
        "total_records_in_comunas": total_records,
        "fuentes_desglose": dict(fuentes_counter),
        "registros_con_sha256_remoto": sha256_records,
        "comunas_1_norma_count": len(one_norm),
        "comunas_1_norma": [c[0] for c in one_norm],
        "comunas_2_normas_count": len(two_norms),
        "comunas_2_normas": [c[0] for c in two_norms],
        "comunas_3_normas_count": len(three_norms),
        "comunas_3_normas": [c[0] for c in three_norms],
        "comunas_baja_densidad_1_3_count": len(low_density),
    }

def inspect_municipal_verified(path: Path) -> dict:
    if not path.exists():
        return {"error": "municipal_verified_records.json no encontrado"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    comunas = set(r.get("comuna") for r in records)
    shas = {r["verification"]["sha256"] for r in records if r.get("verification", {}).get("sha256")}
    return {
        "generated_at": payload.get("generated_at"),
        "declared_count": payload.get("count"),
        "actual_records_count": len(records),
        "unique_comunas_count": len(comunas),
        "unique_sha256_count": len(shas),
    }

def inspect_physical_pdfs(path: Path) -> dict:
    if not path.exists():
        return {"count": 0, "files": []}
    files = sorted(path.rglob("*.pdf"))
    items = []
    for f in files:
        if not f.is_file():
            continue
        with f.open("rb") as stream:
            valid_pdf = stream.read(5) == b"%PDF-"
        if valid_pdf:
            items.append({
                "filename": f.relative_to(path).as_posix(),
                "bytes": f.stat().st_size,
            })
    return {
        "path": str(path),
        "count": len(items),
        "files": sorted(items, key=lambda x: x["filename"]),
    }

def inspect_datasets(path: Path) -> dict:
    result = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result

    bcn_textos_dir = path / "bcn_textos"
    textos = list(bcn_textos_dir.glob("*")) if bcn_textos_dir.exists() else []
    result["bcn_textos_count"] = len(textos)
    result["bcn_textos_sample"] = [t.name for t in textos[:5]]

    db_file = path / "catastro_ordenanzas.db"
    if db_file.exists():
        conn = sqlite3.connect(db_file.resolve().as_uri() + "?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        table_counts = {}
        for t in tables:
            cur.execute(f'SELECT count(*) FROM "{t}"')
            table_counts[t] = cur.fetchone()[0]
        conn.close()
        result["sqlite_db"] = {
            "path": str(db_file),
            "bytes": db_file.stat().st_size,
            "tables": table_counts,
        }
    return result

def run():
    parser = argparse.ArgumentParser(description="Inventario local; no acredita publicación ni vigencia jurídica.")
    parser.add_argument("--datasets-dir", type=Path, default=DATASETS_DIR)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    sd = inspect_status_data(DASHBOARD_DIR / "status_data.json")
    mv = inspect_municipal_verified(DATA_DIR / "municipal_verified_records.json")
    if "error" in sd or "error" in mv:
        raise ValueError(f"Fuentes requeridas ausentes: {sd.get('error')}, {mv.get('error')}")
    pdfs = inspect_physical_pdfs(DATA_DIR / "official_pdfs")
    ds = inspect_datasets(args.datasets_dir)
    snapshot = json.loads((DASHBOARD_DIR / "status_data.json").read_text(encoding="utf-8-sig"))
    represented = sum(bool(c.get("ordenanzas")) for c in snapshot["comunas"])
    total = sd["total_records_in_comunas"]
    municipal = sum(sd["fuentes_desglose"].get(source, 0) for source in
                    ("Municipalidad", "Diario Oficial / BCN", "Diario Oficial", "BCN / LeyChile"))
    bcn = sd["fuentes_desglose"].get("BCN", 0)
    discrepancies = []
    if total != bcn + municipal:
        discrepancies.append("Hay fuentes sin clasificación en el contrato del pipeline")
    expected = {"total_ordenanzas": total, "comunas_con_datos": represented,
                "total_comunas": sd["total_comunas"], "ordenanzas_bcn": bcn,
                "ordenanzas_municipales_verificadas": municipal}
    for key, actual in expected.items():
        if sd["declared_metrics"].get(key) != actual:
            discrepancies.append(f"{key}: declarado {sd['declared_metrics'].get(key)}, contado {actual}")
    if municipal != mv["actual_records_count"]:
        discrepancies.append("El total municipal del snapshot difiere del registro municipal")
    markdown_count = sum(1 for p in (DATA_DIR / "markdown_corpus").rglob("*.md") if p.is_file())
    conclusions = {
        "canonical_total_records": total, "bcn_records": bcn,
        "municipal_verified_remote_records": municipal,
        "physical_local_pdfs_count": pdfs["count"],
        "physical_local_text_files_count": ds.get("bcn_textos_count", 0),
        "local_markdown_files_count": markdown_count,
        "territorial_communes_total": sd["total_comunas"],
        "territorial_communes_represented": represented,
        "discrepancies": discrepancies,
        "critical_gap_for_rag": "Los recuentos físicos no prueban texto completo, calidad de extracción, citas ni funcionamiento de un asistente. Se requiere validar el corpus y el piloto documental.",
    }
    manifest = {"task_id": "P090-20260920-cierre", "generated_at": datetime.now(timezone.utc).isoformat(),
                "status_data": sd, "municipal_verified": mv, "physical_pdfs": pdfs,
                "datasets_external": ds, "conclusions": conclusions}
    for folder in ("data", "docs"):
        (args.output_dir / folder).mkdir(parents=True, exist_ok=True)
    (args.output_dir / "data/document_inventory_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Inventario documental y conciliación de cifras — P090", "",
             "Task ID: `P090-20260920-cierre`. Corte UTC: " + manifest["generated_at"], "",
             "Inspección local. No verifica disponibilidad pública, URLs remotas, vigencia, exhaustividad ni igualdad de exportaciones.", "",
             "| Medida | Recuento |", "| --- | ---: |",
             f"| Registros del snapshot | {total} |", f"| BCN (fuente BCN del pipeline) | {bcn} |",
             f"| Municipales con verificación registrada | {municipal} |",
             f"| Comunas representadas / incluidas | {represented} / {sd['total_comunas']} |",
             f"| PDF con cabecera válida en data/official_pdfs | {pdfs['count']} |",
             f"| Archivos Markdown locales (calidad no validada) | {markdown_count} |",
             f"| Textos externos declarados por inspección | {ds.get('bcn_textos_count', 0)} |", "",
             "## Conciliación", "", "La categoría municipal conserva el contrato del pipeline: Municipalidad, Diario Oficial / BCN, Diario Oficial y BCN / LeyChile. El desglose literal de fuentes está en el manifiesto.", "", *(discrepancies or ["Sin diferencias en los recuentos contrastados."]), "",
             "## Comunas con pocos registros", ""]
    for n in (1, 2, 3):
        lines.append(f"- {n} registros ({sd[f'comunas_{n}_norma_count' if n == 1 else f'comunas_{n}_normas_count']} comunas): " + ", ".join(sd[f"comunas_{n}_norma" if n == 1 else f"comunas_{n}_normas"]))
    lines += ["", "## Límites documentales", "", conclusions["critical_gap_for_rag"], "",
              "Directorio externo inspeccionado: `" + str(args.datasets_dir) + "`.",
              "Presencia territorial no equivale a exhaustividad. Los originales se conservan."]
    (args.output_dir / "docs/INVENTARIO-DOCUMENTAL-P090.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(conclusions, ensure_ascii=False))
    return 1 if discrepancies else 0


if __name__ == "__main__":
    raise SystemExit(run())
