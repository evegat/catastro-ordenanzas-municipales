"""Enrich P090 municipal-site discovery from public SINIM/SUBDERE fichas.

SINIM supplies municipality codes/names and a `Web` field. CPLT remains the
primary institutional identity universe. A SINIM URL is accepted as a crawl seed
only after the commune is reconciled to one CPLT municipality and the target site
passes the same municipal identity gate used by national discovery.

This stage never marks municipal coverage complete and never publishes records.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from cplt_transparencia_crawler import load_directory, make_session, now_iso
from national_municipal_discovery import discover_seed_site, strip_municipality_prefix

SINIM_INDEX = "https://datos.sinim.gov.cl/ficha_comunal.php"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "sinim_seed_enrichment.json"


def normalize_web(value: str) -> str | None:
    raw = re.sub(r"\s+", "", value or "").strip("-–—;,")
    if not raw or raw.lower() in {"sinweb", "s/i", "s/i.", "noinforma", "noinformado"}:
        return None
    if raw.startswith("//"):
        return "https:" + raw
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def fetch_index(session: requests.Session, timeout: float) -> list[dict[str, str]]:
    response = session.get(SINIM_INDEX, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for option in soup.find_all("option"):
        text = " ".join(option.stripped_strings).strip()
        value = (option.get("value") or "").strip()
        match = re.match(r"^(.+?)\s*-\s*(\d{5})$", text)
        code = None
        name = None
        if match:
            name = match.group(1).strip()
            code = match.group(2)
        elif re.fullmatch(r"\d{5}", value):
            code = value
            name = re.sub(r"\s*-\s*\d{5}\s*$", "", text).strip()
        if not code or not name or code in seen:
            continue
        seen.add(code)
        records.append({"sinim_code": code, "commune_name": name})
    if len(records) != 345:
        raise AssertionError(f"Expected 345 SINIM municipalities, got {len(records)}")
    return records


def extract_web_from_ficha(session: requests.Session, code: str, timeout: float) -> dict[str, Any]:
    url = f"{SINIM_INDEX}?municipio={code}"
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        ctype = (response.headers.get("content-type") or "").split(";", 1)[0].lower()
        result: dict[str, Any] = {
            "ficha_url": url,
            "status_code": response.status_code,
            "resolved_url": response.url,
            "content_type": ctype,
            "ok": response.status_code < 400,
            "web": None,
        }
        if response.status_code >= 400:
            return result
        response.encoding = response.apparent_encoding or response.encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text("\n", strip=True)
        patterns = (
            r"(?:^|\n)Web\s*:\s*\n?\s*([^\n]+)",
            r"(?:^|\n)Web\s*\n\s*([^\n]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                result["web_raw"] = match.group(1).strip()
                result["web"] = normalize_web(match.group(1))
                break
        if not result.get("web"):
            web_label = soup.find(string=lambda s: bool(s and re.fullmatch(r"\s*Web\s*:?\s*", s, flags=re.IGNORECASE)))
            if web_label:
                parent = web_label.parent
                container = parent.parent if parent and parent.parent else parent
                if container:
                    anchor = container.find("a", href=True)
                    if anchor:
                        href = urljoin(response.url, anchor.get("href", ""))
                        result["web_raw"] = href
                        result["web"] = normalize_web(href)
                    else:
                        local_text = " ".join(container.stripped_strings)
                        match = re.search(r"Web\s*:?\s*(\S+)", local_text, flags=re.IGNORECASE)
                        if match:
                            result["web_raw"] = match.group(1)
                            result["web"] = normalize_web(match.group(1))
        return result
    except requests.RequestException as exc:
        return {
            "ficha_url": url,
            "status_code": None,
            "resolved_url": None,
            "content_type": None,
            "ok": False,
            "web": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def reconcile_sinim_to_cplt(
    sinim: list[dict[str, str]], directory: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cplt_by_key: dict[str, list[dict[str, Any]]] = {}
    for organism in directory:
        key = strip_municipality_prefix(organism.get("organism_name", ""))
        cplt_by_key.setdefault(key, []).append(organism)

    aliases = {
        "paihuano": "paiguano",
        "la calera": "calera",
        "o higgins": "ohiggins",
        "cabo de hornos": "cabo de hornos",
        "isla de pascua": "isla de pascua rapa nui",
        "llaillay": "llay llay",
        "marchihue": "marchige",
        "natales": "puerto natales",
        "san vicente": "san vicente de tagua tagua",
    }
    matches: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for row in sinim:
        key = strip_municipality_prefix(row["commune_name"])
        lookup = aliases.get(key, key)
        candidates = cplt_by_key.get(lookup, [])
        if len(candidates) == 1:
            matches.append({**row, "cplt": candidates[0]})
        else:
            unresolved.append({**row, "normalized_key": lookup, "candidate_count": len(candidates)})
    return matches, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-site-pages", type=int, default=8)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard configuration")

    session = make_session()
    sinim = fetch_index(session, args.timeout)
    directory = sorted(load_directory(session), key=lambda row: row["cplt_code"])
    if len(directory) != 345:
        raise AssertionError(f"Expected 345 CPLT municipalities, got {len(directory)}")
    reconciled, reconciliation_failures = reconcile_sinim_to_cplt(sinim, directory)
    if len(reconciled) + len(reconciliation_failures) != len(sinim):
        raise AssertionError("SINIM reconciliation accounting mismatch")
    if reconciliation_failures:
        raise AssertionError(f"Unresolved SINIM↔CPLT municipalities: {reconciliation_failures}")
    if len(reconciled) != 345:
        raise AssertionError(f"Expected full SINIM↔CPLT reconciliation, got {len(reconciled)}")

    selected = [row for idx, row in enumerate(reconciled) if idx % args.shard_count == args.shard_index]
    records: list[dict[str, Any]] = []
    for row in selected:
        organism = row["cplt"]
        ficha = extract_web_from_ficha(session, row["sinim_code"], args.timeout)
        seed = ficha.get("web")
        if seed:
            discovery = discover_seed_site(
                session,
                seed,
                organism.get("organism_name") or row["commune_name"],
                max_pages=args.max_site_pages,
                timeout=args.timeout,
            )
        else:
            discovery = {
                "seed_url": None,
                "seed_reachable": False,
                "identity_verified": False,
                "identity": {"verified": False, "reason": "sinim_has_no_web"},
                "pages_attempted": 0,
                "pages": [],
                "candidate_sources": [],
                "candidate_count": 0,
            }
        candidates = discovery.get("candidate_sources") or []
        if candidates:
            state = "verified_candidate_found"
        elif discovery.get("identity_verified"):
            state = "verified_site_no_candidate"
        elif seed and discovery.get("seed_reachable"):
            state = "sinim_seed_identity_unverified"
        elif seed:
            state = "sinim_seed_unreachable"
        else:
            state = "sinim_no_web"
        record = {
            "cplt_code": organism["cplt_code"],
            "organism_name": organism.get("organism_name"),
            "sinim_code": row["sinim_code"],
            "sinim_commune_name": row["commune_name"],
            "ficha": ficha,
            "state": state,
            "discovery": discovery,
            "coverage_complete": False,
        }
        records.append(record)
        print(
            f"{record['cplt_code']} {record['sinim_commune_name']}: {state} "
            f"web={seed or '-'} candidates={len(candidates)}"
        )

    counts = Counter(record["state"] for record in records)
    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0012",
        "policy": "SINIM/SUBDERE is institutional seed source; CPLT identity + site identity gate required; fail closed",
        "sinim_selector_count": len(sinim),
        "sinim_reconciled_count": len(reconciled),
        "sinim_reconciliation_failures": reconciliation_failures,
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "summary": {
            "records": len(records),
            "states": dict(sorted(counts.items())),
            "sinim_web_fields": sum(bool((record.get("ficha") or {}).get("web")) for record in records),
            "identity_verified_sites": sum(bool((record.get("discovery") or {}).get("identity_verified")) for record in records),
            "candidate_sources": sum(len((record.get("discovery") or {}).get("candidate_sources") or []) for record in records),
        },
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("SINIM seed enrichment cannot mark coverage complete")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SINIM SUMMARY", json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
