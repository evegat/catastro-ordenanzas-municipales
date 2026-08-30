"""Merge MW-P090-0013 extraction shards without promoting their evidence."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from extract_validated_municipal_sources import summary

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-count", type=int, default=10)
    parser.add_argument("--pattern", default="data/sinim_extraction_shard_{index:02d}.json")
    parser.add_argument("--seeds", type=Path, default=ROOT / "data/sinim_validated_extraction_seeds.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/sinim_validated_extraction.json")
    args = parser.parse_args()
    seed_payload = json.loads(args.seeds.read_text(encoding="utf-8"))
    expected_codes = {row["cplt_code"] for row in seed_payload.get("municipalities", [])}
    records = []
    for index in range(args.shard_count):
        path = ROOT / args.pattern.format(index=index)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("task_id") != "MW-P090-0013" or payload.get("shard") != {"index": index, "count": args.shard_count}:
            raise AssertionError(f"Contrato de shard inválido: {path}")
        records.extend(payload.get("records", []))
    actual_codes = [row.get("cplt_code") for row in records]
    if len(actual_codes) != len(set(actual_codes)) or set(actual_codes) != expected_codes:
        raise AssertionError("Merge de extracción no coincide exactamente con las semillas seleccionadas")
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_id": "MW-P090-0013", "derived_from": seed_payload.get("derived_from"),
        "policy": "SINIM+CPLT identity verified; scope-safe evidence only; coverage_complete=false",
        "shard": {"index": 0, "count": 1}, "summary": summary(records),
        "records": sorted(records, key=lambda row: row["cplt_code"]),
    }
    if any(row.get("coverage_complete") for row in records):
        raise AssertionError("Extracción no puede declarar cobertura completa")
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
