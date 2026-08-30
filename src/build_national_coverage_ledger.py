"""Build a fail-closed 345-municipality evidence and gap ledger for P090."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=ROOT / "data/cplt_municipal_directory.json")
    parser.add_argument("--discovery", type=Path, default=ROOT / "data/sinim_seed_enrichment.json")
    parser.add_argument("--extraction", type=Path, default=ROOT / "data/sinim_validated_extraction.json")
    parser.add_argument("--verified", type=Path, default=ROOT / "data/municipal_verified_records.json")
    parser.add_argument("--classification", type=Path, default=ROOT / "data/sinim_llm_classification.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/national_coverage_ledger.json")
    args = parser.parse_args()
    directory = read(args.directory, {})
    if directory.get("count") != 345 or len(directory.get("municipalities", [])) != 345:
        raise AssertionError("El ledger exige el universo CPLT 345/345")
    discovery = read(args.discovery, {})
    extraction = read(args.extraction, {})
    verified = read(args.verified, {})
    classification = read(args.classification, {})
    discovery_by = {row.get("cplt_code"): row for row in discovery.get("records", [])}
    extraction_by = {row.get("cplt_code"): row for row in extraction.get("records", [])}
    verified_by = Counter(row.get("cplt_code") for row in verified.get("records", []) if row.get("cplt_code"))
    classified_by = classification.get("municipalities", {})
    rows = []
    for municipality in directory["municipalities"]:
        code = municipality["cplt_code"]
        found = discovery_by.get(code)
        extracted = extraction_by.get(code)
        source_rows = (extracted or {}).get("sources", [])
        verified_pdfs = int((extracted or {}).get("unique_verified_pdfs", 0) or 0)
        unresolved = sum(int(source.get("unresolved_documents", 0) or 0) for source in source_rows)
        legal = classified_by.get(code, {})
        decisions = legal.get("decisions", [])
        classified_ordinances = sum(bool(row.get("is_ordinance")) for row in decisions)
        pending_classification = sum(row.get("status") != "classified" for row in decisions)
        exhausted = bool(source_rows) and all(source.get("listing_exhausted") for source in source_rows)
        gaps = []
        if not found:
            gaps.append("sin_discovery_sinim")
        elif not (found.get("discovery") or {}).get("identity_verified"):
            gaps.append("sitio_institucional_no_verificado")
        if not (found or {}).get("discovery", {}).get("candidate_sources"):
            gaps.append("sin_fuente_candidata")
        if found and not extracted:
            gaps.append("sin_extraccion")
        if extracted and not exhausted:
            gaps.append("listado_no_agotado")
        if unresolved:
            gaps.append("documentos_sin_resolver")
        if verified_pdfs == 0 and verified_by.get(code, 0) == 0:
            gaps.append("sin_documento_municipal_verificado")
        if verified_pdfs and legal.get("status") != "done":
            gaps.append("sin_clasificacion_juridica_local")
        if pending_classification:
            gaps.append("clasificacion_juridica_pendiente")
        rows.append({
            "cplt_code": code, "organism_name": municipality.get("organism_name"),
            "discovery_state": (found or {}).get("state", "missing"),
            "candidate_sources": len((found or {}).get("discovery", {}).get("candidate_sources", []) or []),
            "sources_attempted": len(source_rows), "sources_exhausted": sum(bool(s.get("listing_exhausted")) for s in source_rows),
            "extracted_verified_pdfs": verified_pdfs, "lm_classified_ordinances": classified_ordinances,
            "lm_rejected_documents": sum(row.get("status") == "classified" and not row.get("is_ordinance") for row in decisions),
            "existing_verified_records": verified_by.get(code, 0),
            "unresolved_documents": unresolved, "gaps": gaps, "coverage_complete": False,
        })
    gap_counts = Counter(gap for row in rows for gap in row["gaps"])
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_id": "MW-P090-0014", "policy": "FAIL CLOSED; completeness requires explicit source reconciliation",
        "summary": {
            "municipalities_total": 345, "municipalities_with_no_gaps": sum(not row["gaps"] for row in rows),
            "municipalities_with_verified_documents": sum(row["extracted_verified_pdfs"] + row["existing_verified_records"] > 0 for row in rows),
            "gap_counts": dict(sorted(gap_counts.items())), "coverage_complete": False,
        },
        "municipalities": rows,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
