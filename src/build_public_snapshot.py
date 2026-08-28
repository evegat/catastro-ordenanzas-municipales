"""Build the public P090 snapshot from repository data.

Unverified CPLT/municipal references remain preserved in the repository source data,
but they are excluded from the public dashboard and public downloads until each
record has reproducible documentary evidence.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


QUARANTINED_SOURCE = "CPLT"


def quarantine_cplt(data: dict) -> tuple[dict, int]:
    public = copy.deepcopy(data)
    quarantined = 0
    total_bcn = 0
    comunas_con_datos = 0
    topic_counts: dict[str, int] = {}

    for comuna in public.get("comunas", []):
        original = comuna.get("ordenanzas", []) or []
        kept = [o for o in original if o.get("fuente") != QUARANTINED_SOURCE]
        quarantined += len(original) - len(kept)

        comuna["ordenanzas"] = kept
        comuna["cplt_count"] = 0
        comuna["bcn_count"] = sum(1 for o in kept if o.get("fuente") == "BCN")
        comuna["total_count"] = len(kept)
        total_bcn += comuna["bcn_count"]

        if kept:
            comunas_con_datos += 1
            comuna["status"] = "Cargado BCN"
        else:
            comuna["status"] = "Sin registros BCN verificados"

        for ord_ in kept:
            materia = ord_.get("materia") or "Normativa General y Otras Materias"
            topic_counts[materia] = topic_counts.get(materia, 0) + 1

    metrics = public.setdefault("metrics", {})
    metrics["ordenanzas_bcn"] = total_bcn
    metrics["ordenanzas_cplt"] = 0
    metrics["total_ordenanzas"] = total_bcn
    metrics["comunas_con_datos"] = comunas_con_datos
    metrics["cplt_en_cuarentena"] = quarantined

    for topic in public.get("topics", []) or []:
        topic["count"] = topic_counts.get(topic.get("nombre", ""), 0)

    public["public_scope"] = {
        "policy": "verified-only",
        "included_sources": ["BCN"],
        "quarantined_sources": ["CPLT"],
        "quarantined_records": quarantined,
        "reason": (
            "Referencias CPLT/municipales sin evidencia documental reproducible; "
            "se preservan internamente pero no se publican hasta su verificación."
        ),
    }
    return public, quarantined


def iter_public_rows(data: dict):
    for comuna in data.get("comunas", []) or []:
        for ord_ in comuna.get("ordenanzas", []) or []:
            yield {
                "comuna": comuna.get("comuna", ""),
                "region_id": comuna.get("region_id", ""),
                "region_nombre": comuna.get("region_nombre", ""),
                "fuente": ord_.get("fuente", ""),
                "numero": ord_.get("numero", ""),
                "fecha": ord_.get("fecha", ""),
                "titulo": ord_.get("titulo", ""),
                "materia": ord_.get("materia", ""),
                "url": ord_.get("target_url", ""),
                "rdf_url": ord_.get("rdf_url", ""),
            }


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
        "comuna", "region_id", "region_nombre", "fuente", "numero", "fecha",
        "titulo", "materia", "url", "rdf_url",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(rows: list[dict], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Ordenanzas verificadas"
    headers = [
        "Comuna", "Región ID", "Región", "Fuente", "Número", "Fecha",
        "Título", "Materia", "URL oficial", "RDF",
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append([
            row["comuna"], row["region_id"], row["region_nombre"], row["fuente"],
            row["numero"], row["fecha"], row["titulo"], row["materia"],
            row["url"], row["rdf_url"],
        ])

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    widths = {"A": 22, "B": 10, "C": 24, "D": 12, "E": 18, "F": 14,
              "G": 70, "H": 35, "I": 55, "J": 55}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    wb.save(path)


def format_count(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")


def replace_element_text(html: str, element_id: str, value: str) -> str:
    pattern = rf'(<[^>]+id=["\']{re.escape(element_id)}["\'][^>]*>).*?(</[^>]+>)'
    return re.sub(
        pattern,
        lambda m: f"{m.group(1)}{value}{m.group(2)}",
        html,
        count=1,
        flags=re.DOTALL,
    )


def extract_element_text(html: str, element_id: str) -> str:
    pattern = rf'<[^>]+id=["\']{re.escape(element_id)}["\'][^>]*>(.*?)</[^>]+>'
    match = re.search(pattern, html, flags=re.DOTALL)
    if not match:
        raise AssertionError(f"Missing HTML element #{element_id}")
    return re.sub(r"<[^>]+>", "", match.group(1)).strip()


def validate_public_html(index_path: Path, metrics: dict) -> None:
    html = index_path.read_text(encoding="utf-8")
    communes = int(metrics.get("comunas_con_datos", 0))
    pct = round((communes / 346) * 100) if communes else 0
    expected = {
        "metric-total-ordenanzas": format_count(metrics.get("total_ordenanzas", 0)),
        "metric-bcn-count": format_count(metrics.get("ordenanzas_bcn", 0)),
        "metric-cplt-count": format_count(metrics.get("cplt_en_cuarentena", 0)),
        "metric-comunas-con-datos": str(communes),
        "pct-comunas": f"{pct}% cubierto",
    }
    for element_id, expected_text in expected.items():
        actual = extract_element_text(html, element_id)
        if actual != expected_text:
            raise AssertionError(
                f"#{element_id}: expected {expected_text!r}, got {actual!r}"
            )

    if "data.metrics.cplt_en_cuarentena" not in html:
        raise AssertionError("Runtime CPLT metric is not bound to quarantine count")


def patch_public_html(index_path: Path, metrics: dict) -> None:
    html = index_path.read_text(encoding="utf-8-sig")
    total = int(metrics.get("total_ordenanzas", 0))
    total_bcn = int(metrics.get("ordenanzas_bcn", 0))
    quarantined = int(metrics.get("cplt_en_cuarentena", 0))
    communes = int(metrics.get("comunas_con_datos", 0))
    pct = round((communes / 346) * 100) if communes else 0

    replacements = {
        "BCN (Histórico) & Transparencia Activa CPLT (2022–2026)":
            "BCN / LeyChile · corpus público verificable",
        "CPLT (2022-26):": "CPLT en cuarentena:",
        "CPLT (2022–26):": "CPLT en cuarentena:",
        "Listado de ordenanzas oficiales disponibles (BCN & Transparencia Activa CPLT).":
            "Listado público de registros BCN/LeyChile verificables.",
        "Fuentes: BCN LeyChile & Transparencia CPLT":
            "Fuente pública actual: BCN LeyChile",
        "<option value=\"CPLT\">CPLT (2022–26)</option>":
            "<option value=\"CPLT\" disabled>CPLT en cuarentena</option>",
        "Planilla oficial con 1.632 ordenanzas, clasificación en 9 ejes e hipervínculos funcionales.":
            "Planilla pública del corpus BCN/LeyChile verificable, con clasificación temática e hipervínculos oficiales.",
        "Excel maestro, base SQLite, directorio CSV y documentos normativos oficiales.":
            "Paquete público reproducible con Excel, CSV y JSON del corpus BCN/LeyChile verificable.",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    # Align the server-rendered shell with the same metrics used by runtime JS.
    html = replace_element_text(html, "metric-total-ordenanzas", format_count(total))
    html = replace_element_text(html, "metric-bcn-count", format_count(total_bcn))
    html = replace_element_text(html, "metric-cplt-count", format_count(quarantined))
    html = replace_element_text(html, "metric-comunas-con-datos", str(communes))
    html = replace_element_text(html, "pct-comunas", f"{pct}% cubierto")

    html = re.sub(
        r'(id=["\']progress-comunas["\'][^>]*style=["\'][^"\']*width:\s*)\d+(%[^"\']*["\'])',
        rf'\g<1>{pct}\2',
        html,
        count=1,
    )

    # In the public artifact the CPLT metric reports quarantine size, not published rows.
    html = html.replace(
        "Number(data.metrics.ordenanzas_cplt).toLocaleString('es-CL')",
        "Number(data.metrics.cplt_en_cuarentena || 0).toLocaleString('es-CL')",
    )

    # The former runtime CPLT safety shim is not used in the verified-only public build.
    html = html.replace('  <script src="cplt-safety.js"></script>\n', "")
    index_path.write_text(html, encoding="utf-8")
    validate_public_html(index_path, metrics)


def build(dashboard_dir: Path) -> None:
    json_path = dashboard_dir / "status_data.json"
    js_path = dashboard_dir / "status_data.js"
    index_path = dashboard_dir / "index.html"
    downloads = dashboard_dir / "descargas"
    downloads.mkdir(parents=True, exist_ok=True)

    data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    public, quarantined = quarantine_cplt(data)
    rows = list(iter_public_rows(public))

    json_path.write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    js_path.write_text(
        "window.CATASTRO_DATA = " + json.dumps(public, ensure_ascii=False, indent=2) + ";",
        encoding="utf-8",
    )

    csv_path = downloads / "catastro_ordenanzas_nacional_2026.csv"
    xlsx_path = downloads / "catastro_ordenanzas_nacional_2026.xlsx"
    zip_path = downloads / "consolidado_ordenanzas_chile_2026.zip"
    write_csv(rows, csv_path)
    write_xlsx(rows, xlsx_path)

    manifest = downloads / "README_PUBLICO.txt"
    manifest.write_text(
        "P090 — snapshot público verified-only\n"
        f"Registros publicados: {len(rows)} (BCN/LeyChile)\n"
        f"Referencias CPLT en cuarentena: {quarantined}\n"
        "Criterio: un registro complementario vuelve a publicarse solo con evidencia documental reproducible.\n",
        encoding="utf-8",
    )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(xlsx_path, xlsx_path.name)
        zf.write(csv_path, csv_path.name)
        zf.write(json_path, "status_data_public.json")
        zf.write(manifest, manifest.name)

    patch_public_html(index_path, public["metrics"])
    print(
        f"Public snapshot built: {len(rows)} verified BCN records; "
        f"{quarantined} CPLT references quarantined."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dashboard_dir", nargs="?", default="dashboard")
    args = parser.parse_args()
    build(Path(args.dashboard_dir))


if __name__ == "__main__":
    main()
