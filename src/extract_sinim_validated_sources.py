"""Run MW-P090-0013 extraction from strict SINIM-derived seed input.

This is a thin task-specific wrapper over the scope-safe extractor introduced in
MW-P090-0010. It preserves that extractor's fail-closed behavior while emitting
MW-P090-0013 evidence and never setting municipal coverage complete.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cplt_transparencia_crawler import make_session, now_iso
from extract_validated_municipal_sources import extract_municipality, summary

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEEDS = REPO_ROOT / "data" / "sinim_validated_extraction_seeds.json"
DEFAULT_OUT = REPO_ROOT / "data" / "sinim_validated_extraction.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--max-candidates", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--max-pdf-mb", type=int, default=80)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard configuration")

    seed_payload = json.loads(args.seeds.read_text(encoding="utf-8"))
    if seed_payload.get("task_id") != "MW-P090-0013":
        raise AssertionError("Unexpected seed task id")
    derived = seed_payload.get("derived_from") or {}
    if int(derived.get("sinim_selector_count", 0)) != 345 or int(derived.get("reconciled_municipalities", 0)) != 345:
        raise AssertionError("Extraction requires full 345/345 SINIM↔CPLT seed provenance")

    municipalities = seed_payload.get("municipalities") or []
    if not municipalities:
        raise AssertionError("No municipalities selected for MW-P090-0013")
    if len({row.get("cplt_code") for row in municipalities}) != len(municipalities):
        raise AssertionError("Duplicate CPLT municipality codes in MW-P090-0013 seeds")
    if any(row.get("coverage_complete") for row in municipalities):
        raise AssertionError("Input seeds cannot claim municipal coverage completeness")

    selected = [row for idx, row in enumerate(municipalities) if idx % args.shard_count == args.shard_index]
    session = make_session()
    records = []
    for municipality in selected:
        print(f"MUNICIPALITY {municipality['cplt_code']} {municipality.get('municipality')}")
        records.append(
            extract_municipality(
                session,
                municipality,
                timeout=args.timeout,
                max_pages=args.max_pages,
                max_pdf_bytes=args.max_pdf_mb * 1024 * 1024,
                max_candidates=args.max_candidates,
            )
        )

    result = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0013",
        "derived_from": seed_payload.get("derived_from"),
        "policy": "SINIM+CPLT identity verified; scope-safe evidence only; coverage_complete=false",
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "summary": summary(records),
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("MW-P090-0013 extraction cannot mark coverage complete")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MW-P090-0013 SUMMARY", json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 2 if result["summary"].get("scope_guards_triggered") else 0


if __name__ == "__main__":
    raise SystemExit(main())
