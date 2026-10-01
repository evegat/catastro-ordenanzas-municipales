"""Build scope-safe extraction seeds from a completed MW-P090-0012 ledger.

Only municipalities whose SINIM-derived site passed institutional identity
verification and yielded candidate ordinance sources are admitted. This adapter
is intentionally strict: it rejects incomplete territorial ledgers, duplicate
CPLT codes, identity inconsistencies, and any record claiming legal completeness.

The output is compatible with ``extract_validated_municipal_sources.py`` and is
evidence input only; it does not publish records or certify municipal coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "sinim_seed_enrichment.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "sinim_validated_extraction_seeds.json"


def normalized_url(url: str) -> str:
    """Normalize URLs without importing the network-enabled discovery stack."""
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if not parsed.scheme:
        parsed = urlparse("https://" + raw)
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunparse(
        ((parsed.scheme or "https").lower(), parsed.netloc.lower(), path, "", parsed.query, "")
    )


def load_payload(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def candidate_urls(record: dict[str, Any]) -> list[str]:
    discovery = record.get("discovery") or {}
    if not discovery.get("identity_verified"):
        return []
    candidates = discovery.get("candidate_sources") or []
    unique: dict[str, None] = {}
    for candidate in candidates:
        url = normalized_url(str((candidate or {}).get("url") or ""))
        if url:
            unique[url] = None
    return sorted(unique)


def validate_ledger(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records") or []
    summary = payload.get("summary") or {}
    if int(summary.get("sinim_selector_count", 0)) != 345:
        raise AssertionError("MW-P090-0012 ledger must contain the 345-municipality SINIM universe")
    if int(summary.get("reconciled_municipalities", 0)) != 345:
        raise AssertionError("MW-P090-0012 ledger must reconcile all 345 municipalities to CPLT")
    if int(summary.get("reconciliation_failures", 0)) != 0:
        raise AssertionError("MW-P090-0012 ledger has unresolved SINIM↔CPLT records")
    if len(records) != 345:
        raise AssertionError(f"Expected 345 ledger records, got {len(records)}")
    codes = [str(record.get("cplt_code") or "") for record in records]
    if len(set(codes)) != 345 or any(not code.startswith("MU") for code in codes):
        raise AssertionError("Ledger CPLT codes are missing or duplicated")
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Discovery ledger must not claim municipal coverage completeness")
    return records


def build_seed_record(record: dict[str, Any]) -> dict[str, Any] | None:
    discovery = record.get("discovery") or {}
    urls = candidate_urls(record)
    if record.get("state") != "verified_candidate_found":
        return None
    if not discovery.get("identity_verified") or not urls:
        raise AssertionError(
            f"Inconsistent verified_candidate_found state for {record.get('cplt_code')}"
        )
    seed_site = normalized_url(
        str(discovery.get("seed_url") or (record.get("ficha") or {}).get("web") or "")
    )
    if not seed_site:
        raise AssertionError(f"Missing verified seed site for {record.get('cplt_code')}")
    return {
        "cplt_code": record["cplt_code"],
        "municipality": record.get("sinim_commune_name") or record.get("organism_name"),
        "organism_name": record.get("organism_name"),
        "sinim_code": record.get("sinim_code"),
        "seed_site": seed_site,
        "sources": urls,
        "coverage_complete": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload, input_sha256 = load_payload(args.input)
    records = validate_ledger(payload)
    seeds = [seed for record in records if (seed := build_seed_record(record)) is not None]
    if not seeds:
        raise AssertionError("No identity-verified candidate sources found")

    seed_codes = [seed["cplt_code"] for seed in seeds]
    if len(seed_codes) != len(set(seed_codes)):
        raise AssertionError("Duplicate municipalities in extraction seed set")

    excluded = Counter(
        record.get("state") or "unknown"
        for record in records
        if record.get("state") != "verified_candidate_found"
    )
    source_count = sum(len(seed["sources"]) for seed in seeds)
    output = {
        "task_id": "MW-P090-0013",
        "derived_from": {
            "task_id": payload.get("task_id"),
            "input_sha256": input_sha256,
            "sinim_selector_count": 345,
            "reconciled_municipalities": 345,
        },
        "policy": "identity-verified candidate sources only; extraction evidence only; coverage_complete=false",
        "summary": {
            "municipalities_selected": len(seeds),
            "candidate_sources_selected": source_count,
            "municipalities_excluded": 345 - len(seeds),
            "excluded_states": dict(sorted(excluded.items())),
        },
        "municipalities": sorted(seeds, key=lambda row: row["cplt_code"]),
    }
    if any(row.get("coverage_complete") for row in seeds):
        raise AssertionError("MW-P090-0013 seeds cannot claim coverage completeness")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SINIM EXTRACTION SEEDS", json.dumps(output["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
