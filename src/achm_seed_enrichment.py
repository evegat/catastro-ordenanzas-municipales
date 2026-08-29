"""Use AChM municipality directory only as a secondary web-site seed source.

The official CPLT directory remains the institutional authority. AChM URLs are
accepted only after the target site's identity is verified against the CPLT
organism name. This module does not publish ordinances or mark coverage complete.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from cplt_transparencia_crawler import ascii_key, load_directory, make_session, now_iso
from national_municipal_discovery import discover_seed_site, strip_municipality_prefix

ACHM_PAGE = "https://bkp.achm.cl/item/page/{page}/"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "achm_seed_enrichment.json"


def external_site(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    reject = (
        "achm.cl", "facebook.com", "twitter.com", "x.com", "instagram.com",
        "youtube.com", "google.com", "goo.gl", "linkedin.com", "mailto:"
    )
    return not any(token in host for token in reject)


def municipality_heading(text: str) -> bool:
    key = ascii_key(text)
    return "municipalidad" in key and len(key) < 180


def scrape_achm_page(session: requests.Session, page: int, timeout: float) -> list[dict[str, str]]:
    url = ACHM_PAGE.format(page=page)
    response = session.get(url, timeout=timeout, allow_redirects=True)
    if response.status_code >= 400:
        return []
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    # The legacy AChM directory renders municipality entries as article/card-like
    # blocks. We intentionally use loose containers so the scraper survives minor
    # template differences.
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "strong"]):
        name = " ".join(heading.stripped_strings)
        if not municipality_heading(name):
            continue
        container = heading
        for _ in range(6):
            parent = container.parent
            if parent is None:
                break
            container = parent
            links = [a.get("href", "").strip() for a in container.find_all("a", href=True)]
            external = [href for href in links if href.startswith(("http://", "https://")) and external_site(href)]
            if external:
                for site in external:
                    key = (strip_municipality_prefix(name), site)
                    if key not in seen:
                        seen.add(key)
                        records.append({"municipality_name": name, "municipality_key": key[0], "site_url": site, "directory_page": url})
                break

    # Fallback: text nodes can contain the municipality name while the web URL is
    # a plain anchor in the same card.
    if not records:
        for block in soup.find_all(["article", "li", "div"]):
            text = " ".join(block.stripped_strings)
            if not municipality_heading(text[:250]):
                continue
            match = re.search(r"(?:I\.?\s*)?Municipalidad\s+de\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{2,80})", text, flags=re.IGNORECASE)
            if not match:
                continue
            name = "Municipalidad de " + match.group(1).strip(" -")
            for anchor in block.find_all("a", href=True):
                site = anchor.get("href", "").strip()
                if site.startswith(("http://", "https://")) and external_site(site):
                    key = (strip_municipality_prefix(name), site)
                    if key not in seen:
                        seen.add(key)
                        records.append({"municipality_name": name, "municipality_key": key[0], "site_url": site, "directory_page": url})
    return records


def scrape_directory(session: requests.Session, *, max_pages: int, timeout: float) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    empty_streak = 0
    for page in range(1, max_pages + 1):
        page_records = scrape_achm_page(session, page, timeout)
        print(f"AChM page {page}: {len(page_records)} seeds")
        if page_records:
            records.extend(page_records)
            empty_streak = 0
        else:
            empty_streak += 1
            if empty_streak >= 3 and page > 5:
                break
    by_pair: dict[tuple[str, str], dict[str, str]] = {}
    for record in records:
        by_pair[(record["municipality_key"], record["site_url"])] = record
    return list(by_pair.values())


def match_seed(organism: dict[str, Any], seeds: list[dict[str, str]]) -> list[dict[str, str]]:
    target = strip_municipality_prefix(organism.get("organism_name", ""))
    exact = [seed for seed in seeds if seed["municipality_key"] == target]
    if exact:
        return exact
    # Minimal aliases for known orthographic variants.
    aliases = {
        "paiguano": {"paihuano"},
        "cabo de hornos": {"cabo de hornos y antartica", "cabo de hornos y antartica chilena"},
        "ohiggins": {"o higgins"},
    }
    allowed = aliases.get(target, set())
    return [seed for seed in seeds if seed["municipality_key"] in allowed]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-achm-pages", type=int, default=25)
    parser.add_argument("--max-site-pages", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard configuration")

    session = make_session()
    achm_seeds = scrape_directory(session, max_pages=args.max_achm_pages, timeout=args.timeout)
    directory = sorted(load_directory(session), key=lambda row: row["cplt_code"])
    selected = [row for idx, row in enumerate(directory) if idx % args.shard_count == args.shard_index]

    records = []
    for organism in selected:
        seeds = match_seed(organism, achm_seeds)
        attempts = []
        for seed in seeds:
            discovery = discover_seed_site(
                session,
                seed["site_url"],
                organism.get("organism_name") or "",
                max_pages=args.max_site_pages,
                timeout=args.timeout,
            )
            attempts.append({"achm_seed": seed, "discovery": discovery})
        verified = [a for a in attempts if a["discovery"].get("identity_verified")]
        candidates = sum(len(a["discovery"].get("candidate_sources") or []) for a in verified)
        state = (
            "verified_candidate_found" if candidates
            else "verified_site_no_candidate" if verified
            else "seed_identity_unverified" if attempts
            else "no_achm_seed"
        )
        records.append({
            "cplt_code": organism["cplt_code"],
            "organism_name": organism.get("organism_name"),
            "state": state,
            "achm_seed_count": len(seeds),
            "verified_site_count": len(verified),
            "candidate_source_count": candidates,
            "attempts": attempts,
            "coverage_complete": False,
        })
        print(f"{organism['cplt_code']} {organism.get('organism_name')}: {state} seeds={len(seeds)} verified={len(verified)} candidates={candidates}")

    counts = Counter(record["state"] for record in records)
    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0011",
        "policy": "AChM is seed-only; CPLT is institutional authority; identity gate required",
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "achm_seed_records": len(achm_seeds),
        "summary": {
            "records": len(records),
            "states": dict(sorted(counts.items())),
            "verified_sites": sum(r["verified_site_count"] for r in records),
            "candidate_sources": sum(r["candidate_source_count"] for r in records),
        },
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Seed enrichment cannot mark municipal coverage complete")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ACHM ENRICHMENT SUMMARY", json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
