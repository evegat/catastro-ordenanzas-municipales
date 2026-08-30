"""Merge local MW-P090-0012 SINIM discovery shards with strict 345/345 checks."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-count", type=int, default=10)
    parser.add_argument("--pattern", default="data/sinim_discovery_shard_{index:02d}.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/sinim_seed_enrichment.json")
    args = parser.parse_args()
    records = []
    for index in range(args.shard_count):
        path = ROOT / args.pattern.format(index=index)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("task_id") != "MW-P090-0012" or payload.get("shard") != {"index": index, "count": args.shard_count}:
            raise AssertionError(f"Contrato de shard inválido: {path}")
        records.extend(payload.get("records", []))
    codes = [row.get("cplt_code") for row in records]
    if len(records) != 345 or len(set(codes)) != 345:
        raise AssertionError(f"Merge SINIM requiere 345 códigos únicos; recibió {len(records)}/{len(set(codes))}")
    states = Counter(row.get("state") for row in records)
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_id": "MW-P090-0012", "policy": "SINIM/SUBDERE institutional seeds; fail closed; coverage_complete=false",
        "sinim_selector_count": 345, "sinim_reconciled_count": 345, "sinim_reconciliation_failures": [],
        "shard": {"index": 0, "count": 1},
        "summary": {
            "records": 345, "sinim_selector_count": 345, "reconciled_municipalities": 345,
            "states": dict(sorted(states.items())),
            "sinim_web_fields": sum(bool((row.get("ficha") or {}).get("web")) for row in records),
            "identity_verified_sites": sum(bool((row.get("discovery") or {}).get("identity_verified")) for row in records),
            "candidate_sources": sum(len((row.get("discovery") or {}).get("candidate_sources") or []) for row in records),
        },
        "records": sorted(records, key=lambda row: row["cplt_code"]),
    }
    if any(row.get("coverage_complete") for row in records):
        raise AssertionError("Discovery no puede declarar cobertura completa")
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
