"""Integrate Tier 3 rescued batch into municipal_verified_records.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCH_PATH = REPO_ROOT / "data" / "tier3_rescued_batch.json"
VERIFIED_PATH = REPO_ROOT / "data" / "municipal_verified_records.json"


def main() -> None:
    batch = json.loads(BATCH_PATH.read_text(encoding="utf-8"))
    mv = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))

    existing_hashes = {r.get("verification", {}).get("sha256") for r in mv["records"]}
    to_add = []
    for r in batch["records"]:
        h = r.get("verification", {}).get("sha256")
        if h and h not in existing_hashes:
            to_add.append(r)
            existing_hashes.add(h)

    print(f"Adding {len(to_add)} records to municipal_verified_records.json")
    mv["records"].extend(to_add)
    mv["count"] = len(mv["records"])
    mv["generated_at"] = datetime.now(timezone.utc).isoformat()

    VERIFIED_PATH.write_text(json.dumps(mv, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"New total count in municipal_verified_records.json: {mv['count']}")


if __name__ == "__main__":
    main()
