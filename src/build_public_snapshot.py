"""Build the public P090 snapshot from repository data.

The public corpus contains BCN/LeyChile records plus municipal records that have
passed the documentary evidence contract. Historical manual CPLT references are
kept in quarantine and never published directly.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import unicodedata
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


QUARANTINED_SOURCE = "CPLT"
MUNICIPAL_SOURCE = "Municipalidad"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERIFIED_MUNICIPAL = REPO_ROOT / "data" / "municipal_verified_records.json"


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def load_verified_municipal(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", []) or []
    if payload.get("count") != len(records):
        raise AssertionError("municipal_verified_records count does not match records")

    seen_acts: set[tuple[str, str, str]] = set()
    for record in records:
        verification = record.get("verification") or {}
        if record.get("fuente") != MUNICIPAL_SOURCE:
            raise AssertionError("Verified municipal record has invalid source")
        if verification.get("status") != "verified":
            raise AssertionError("Municipal record is not verified")
        if int(verification.get("http_status") or 999) >= 400:
            raise AssertionError("Municipal record has invalid HTTP verification")
        if len(str(verification.get("sha256") or "")) != 64:
            raise AssertionError("Municipal record has invalid SHA-256")
        if int(verification.get("bytes") or 0) <= 0:
            raise AssertionError("Municipal record has no verified bytes")
        if not str(record.get("target_url") or "").startswith("https://"):
            raise AssertionError("Public municipal target must use HTTPS")
        if not str(record.get("source_listing_url") or "").startswith("https://"):
            raise AssertionError("Municipal record lacks official listing URL")

        key = (
            normalize_key(record.get("comuna", "")),
            normalize_key(record.get("numero", "")),
            str(record.get("fecha") or ""),
        )
        if key in seen_acts:
            raise AssertionError(f"Duplicate canonical municipal legal act: {key}")
        seen_acts.add(key)
    return records


def quarantine_cplt(data: dict) -> tuple[dict, int]:
    public = copy.deepcopy(data)
    quarantined = 0
    for comuna in public.get("comunas", []):
        original = comuna.get("ordenanzas", []) or []
        kept = [o for o in original if o.get("fuente") == "BCN"]
        quarantined += len([o for o in original if o.get("fuente") == QUARANTINED_SOURCE])
        comuna["ordenanzas"] = kept
    return public, quarantined


def promote_verified_municipal(public: dict, records: list[dict]) -> int:
    communes = {
        normalize_key(comuna.get("comuna", "")): comuna
        for comuna in public.get("comunas", [])
    }
    promoted = 0
    for record in records:
        key = normalize_key(record.get("comuna", ""))
        comuna = communes.get(key)
        if comuna is None:
            raise AssertionError(f"Verified municipality not found in master: {record.get('comuna')}")

        ordinance = copy.deepcopy(record)
        ordinance.pop("comuna", None)
        ordinance.pop("region_id", None)
        ordinance.setdefault("materia", "Normativa General y Otras Materias")
        ordinance.setdefault("materia_id", "general")
        ordinance.setdefault("rdf_url", None)
        comuna.setdefault("ordenanzas", []).append(ordinance)
        promoted += 1
    return promoted


def recalculate_metrics(public: dict, quarantined: int) -> None:
    total_bcn = 0
    total_municipal = 0
    comunas_con_datos = 0
    topic_counts: dict[str, int] = {}

    for comuna in public.get("comunas", []):
        ordinances = comuna.get("ordenanzas", []) or []
        bcn_count = sum(1 for o in ordinances if o.get("fuente") == "BCN")
        municipal_count = sum(1 for o in ordinances if o.get("fuente") == MUNICIPAL_SOURCE)
        total_bcn += bcn_count
        total_municipal += municipal_count

        comuna["cplt_count"] = 0
        comuna["bcn_count"] = bcn_count
        comuna["municipal_count"] = municipal_count
        comuna["total_count"] = len(ordinances)

        if ordinances:
            comunas_con_datos += 1
            if bcn_count and municipal_count:
                comuna["status"] = "BCN + Municipalidad verificada"
            elif municipal_count:
                comuna["status"] = "Municipalidad verificada"
            else:
                comuna["status"] = "Cargado BCN"
        else:
            comuna["status"] = "Sin registros verificados"

        for ord_ in ordinances:
            materia = ord_.get("materia") or "Normativa General y Otras Materias"
            topic_counts[materia] = topic_counts.get(materia, 0) + 1

    total = total_bcn + total_municipal
    metrics = public.setdefault("metrics", {})
    metrics["ordenanzas_bcn"] = total_bcn
    metrics["ordenanzas_cplt"] = 0
    metrics["ordenanzas_municipales_verificadas"] = total_municipal
    metrics["total_ordenanzas"] = total
    metrics["comunas_con_datos"] = comunas_con_datos
    metrics["cplt_en_cuarentena"] = quarantined

    for topic in public.get("topics", []) or []:
        topic["count"] = topic_counts.get(topic.get("nombre", ""), 0)

    public["public_scope"] = {
        "policy": "verified-only",
        "included_sources": ["BCN", MUNICIPAL_SOURCE],
        "quarantined_sources": ["CPLT"],
        "quarantined_records": quarantined,
        "verified_municipal_records": total_municipal,
        "reason": (
            "Las referencias CPLT manuales sin evidencia se mantienen en cuarentena. "
            "Solo se publican documentos municipales con listado oficial, PDF resoluble "
            "y huella SHA-256 verificada."
        ),
    }


def iter_public_rows(data: dict):
    for comuna in data.get("comunas", []) or []:
        for ord_ in comuna.get("ordenanzas", []) or []:
            verification = ord_.get("verification") or {}
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
                "source_listing_url": ord_.get("source_listing_url", ""),
                "sha256": verification.get("sha256", ""),
                "rdf_url": ord_.get("rdf_url", ""),
            }


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
        "comuna", "region_id", "region_nombre", "fuente", "numero", "fecha",
        "titulo", "materia", "url", "source_listing_url", "sha256", "rdf_url",
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
        "Título", "Materia", "URL oficial", "Listado fuente", "SHA-256", "RDF",
    ]
    ws.append(headers)
    for cell_ in ws[1]:
        cell_.font = Font(bold=True)

    for row in rows:
        ws.append([
            row["comuna"], row["region_id"], row["region_nombre"], row["fuente"],
            row["numero"], row["fecha"], row["titulo"], row["materia"],
            row["url"], row["source_listing_url"], row["sha256"], row["rdf_url"],
        ])

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    widths = {
        "A": 22, "B": 10, "C": 24, "D": 16, "E": 18, "F": 14,
        "G": 70, "H": 35, "I": 55, "J": 55, "K": 68, "L": 55,
    }
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
        "metric-cplt-count": format_count(metrics.get("ordenanzas_municipales_verificadas", 0)),
        "metric-comunas-con-datos": str(communes),
        "pct-comunas": f"{pct}% cubierto",
    }
    for element_id, expected_text in expected.items():
        actual = extract_element_text(html, element_id)
        if actual != expected_text:
            raise AssertionError(
                f"#{element_id}: expected {expected_text!r}, got {actual!r}"
            )

    if "data.metrics.ordenanzas_municipales_verificadas" not in html:
        raise AssertionError("Runtime municipal metric is not bound to verified count")
    if "MUNICIPAL VERIFICADA" not in html:
        raise AssertionError("Municipal source rendering is not enabled")


def patch_public_html(index_path: Path, metrics: dict) -> None:
    html = index_path.read_text(encoding="utf-8-sig")
    total = int(metrics.get("total_ordenanzas", 0))
    total_bcn = int(metrics.get("ordenanzas_bcn", 0))
    municipal = int(metrics.get("ordenanzas_municipales_verificadas", 0))
    communes = int(metrics.get("comunas_con_datos", 0))
    pct = round((communes / 346) * 100) if communes else 0

    replacements = {
        "BCN (Histórico) & Transparencia Activa CPLT (2022–2026)":
            "BCN / LeyChile + fuentes municipales verificadas",
        "CPLT (2022-26):": "Municipales verificadas:",
        "CPLT (2022–26):": "Municipales verificadas:",
        "Listado de ordenanzas oficiales disponibles (BCN & Transparencia Activa CPLT).":
            "Listado público de registros BCN/LeyChile y documentos municipales verificados.",
        "Fuentes: BCN LeyChile & Transparencia CPLT":
            "Fuentes: BCN LeyChile + sitios municipales oficiales",
        "<option value=\"CPLT\">Con Transparencia CPLT (2022–2026)</option>":
            "<option value=\"MUNICIPAL\">Con fuente municipal verificada</option>",
        "<option value=\"CPLT\">CPLT (2022–26)</option>":
            "<option value=\"Municipalidad\">Municipalidad verificada</option>",
        "CPLT 2022-26": "Municipal verificadas",
        "Pendiente CPLT": "Sin fuente municipal verificada",
        "BCN + CPLT": "BCN + Municipal",
        "CPLT 2022-26": "Municipal verificada",
        "Fase 2 CPLT": "Sin registros verificados",
        "CPLT VIGENTE (2022-2026)": "MUNICIPAL VERIFICADA",
        "Abrir Documento CPLT ↗": "Abrir documento municipal ↗",
        "Planilla oficial con 1.632 ordenanzas, clasificación en 9 ejes e hipervínculos funcionales.":
            "Planilla pública del corpus verificable, con clasificación temática, fuentes y huellas documentales.",
        "Excel maestro, base SQLite, directorio CSV y documentos normativos oficiales.":
            "Paquete público reproducible con Excel, CSV y JSON del corpus verificable.",
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    html = html.replace(" (Vigente CPLT)", "")
    html = html.replace("c.cplt_count", "c.municipal_count")
    html = html.replace(
        "if (status === 'CPLT') matchesStatus = (c.municipal_count > 0);",
        "if (status === 'MUNICIPAL') matchesStatus = (c.municipal_count > 0);",
    )
    html = html.replace(
        "const isCplt = (ord.fuente === 'CPLT');",
        "const isMunicipal = (ord.fuente === 'Municipalidad');",
    )
    html = html.replace("isCplt", "isMunicipal")
    html = html.replace("${commune.municipal_count || 0} CPLT", "${commune.municipal_count || 0} municipal")
    html = html.replace(
        "Number(data.metrics.ordenanzas_cplt).toLocaleString('es-CL')",
        "Number(data.metrics.ordenanzas_municipales_verificadas || 0).toLocaleString('es-CL')",
    )

    html = replace_element_text(html, "metric-total-ordenanzas", format_count(total))
    html = replace_element_text(html, "metric-bcn-count", format_count(total_bcn))
    html = replace_element_text(html, "metric-cplt-count", format_count(municipal))
    html = replace_element_text(html, "metric-comunas-con-datos", str(communes))
    html = replace_element_text(html, "pct-comunas", f"{pct}% cubierto")

    html = re.sub(
        r'(id=["\']progress-comunas["\'][^>]*style=["\'][^"\']*width:\s*)\d+(%[^"\']*["\'])',
        rf'\g<1>{pct}\2',
        html,
        count=1,
    )

    html = html.replace('  <script src="cplt-safety.js"></script>\n', "")
    index_path.write_text(html, encoding="utf-8")
    validate_public_html(index_path, metrics)


def build(dashboard_dir: Path, verified_municipal_path: Path = DEFAULT_VERIFIED_MUNICIPAL) -> None:
    json_path = dashboard_dir / "status_data.json"
    js_path = dashboard_dir / "status_data.js"
    index_path = dashboard_dir / "index.html"
    downloads = dashboard_dir / "descargas"
    downloads.mkdir(parents=True, exist_ok=True)

    data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    public, quarantined = quarantine_cplt(data)
    municipal_records = load_verified_municipal(verified_municipal_path)
    promoted = promote_verified_municipal(public, municipal_records)
    recalculate_metrics(public, quarantined)
    rows = list(iter_public_rows(public))

    if promoted != public["metrics"]["ordenanzas_municipales_verificadas"]:
        raise AssertionError("Municipal promotion count mismatch")

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
        f"Registros publicados: {len(rows)}\n"
        f"BCN/LeyChile: {public['metrics']['ordenanzas_bcn']}\n"
        f"Municipales verificadas: {public['metrics']['ordenanzas_municipales_verificadas']}\n"
        f"Referencias CPLT manuales en cuarentena: {quarantined}\n"
        "Criterio municipal: listado oficial + PDF resoluble + SHA-256 verificada.\n",
        encoding="utf-8",
    )

    nb_path = downloads / "analisis_ordenanzas_chile_estudiantes.ipynb"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(xlsx_path, xlsx_path.name)
        zf.write(csv_path, csv_path.name)
        zf.write(json_path, "status_data_public.json")
        zf.write(manifest, manifest.name)
        if nb_path.exists():
            zf.write(nb_path, nb_path.name)

    patch_public_html(index_path, public["metrics"])
    print(
        f"Public snapshot built: {public['metrics']['ordenanzas_bcn']} BCN + "
        f"{public['metrics']['ordenanzas_municipales_verificadas']} municipal verified; "
        f"{quarantined} CPLT references quarantined."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dashboard_dir", nargs="?", default="dashboard")
    parser.add_argument(
        "--verified-municipal",
        type=Path,
        default=DEFAULT_VERIFIED_MUNICIPAL,
    )
    args = parser.parse_args()
    build(Path(args.dashboard_dir), args.verified_municipal)


if __name__ == "__main__":
    main()
