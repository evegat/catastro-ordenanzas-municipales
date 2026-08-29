"""National discovery pass for municipal ordinance sources (P090).

This stage discovers official source candidates. It deliberately does NOT mark a
municipality complete and does NOT promote records to the public corpus.

Inputs:
- official CPLT regulated-organism directory (345 municipalities);
- repository commune master, used only to seed official municipal websites;
- existing municipal source registry, used to preserve already-known sources.

Outputs are evidence ledgers suitable for later exhaustive adapters.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, deque
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from cplt_transparencia_crawler import ascii_key, load_directory, make_session, now_iso

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MASTER = REPO_ROOT / "data" / "maestro_comunas_chile.csv"
DEFAULT_REGISTRY = REPO_ROOT / "data" / "municipal_source_registry.json"
DEFAULT_OUT = REPO_ROOT / "data" / "national_municipal_discovery.json"

ORDINANCE_TERMS = (
    "ordenanza",
    "ordenanzas",
    "ordenance",
)
TRANSPARENCY_TERMS = (
    "transparencia",
    "actos y resoluciones",
    "efectos sobre terceros",
    "actos con efectos sobre terceros",
)
COMMON_PATHS = (
    "/ordenanzas/",
    "/ordenanzas-municipales/",
    "/transparencia/ordenanzas/",
    "/transparencia/ordenanzas.html",
    "/transparencia/",
)
PORTAL_HOSTS = {"portaltransparencia.cl", "www.portaltransparencia.cl"}


def normalized_url(url: str) -> str:
    p = urlparse((url or "").strip())
    if not p.scheme:
        p = urlparse("https://" + (url or "").strip())
    scheme = p.scheme.lower() if p.scheme else "https"
    netloc = p.netloc.lower()
    path = re.sub(r"/{2,}", "/", p.path or "/")
    return urlunparse((scheme, netloc, path, "", p.query, ""))


def strip_municipality_prefix(value: str) -> str:
    key = ascii_key(value)
    prefixes = (
        "ilustre municipalidad de ",
        "i municipalidad de ",
        "municipalidad de ",
        "ilustre municipalidad ",
        "municipalidad ",
    )
    for prefix in prefixes:
        if key.startswith(prefix):
            key = key[len(prefix):]
            break
    aliases = {
        "paihuano": "paiguano",
        "la calera": "calera",
        "cabo de hornos y antartica": "cabo de hornos",
        "cabo de hornos y antartica chilena": "cabo de hornos",
        "o higgins": "ohiggins",
    }
    return aliases.get(key, key)


def load_master(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def master_key(row: dict[str, str]) -> str:
    return strip_municipality_prefix(row.get("comuna_nombre", ""))


def best_master_match(organism: dict[str, Any], master: list[dict[str, str]]) -> tuple[dict[str, str] | None, float]:
    target = strip_municipality_prefix(organism.get("organism_name", ""))
    if not target:
        return None, 0.0

    exact = [row for row in master if master_key(row) == target]
    if exact:
        return exact[0], 1.0

    scored: list[tuple[float, dict[str, str]]] = []
    for row in master:
        key = master_key(row)
        if not key:
            continue
        score = SequenceMatcher(None, target, key).ratio()
        scored.append((score, row))
    if not scored:
        return None, 0.0
    score, row = max(scored, key=lambda item: item[0])
    return (row, score) if score >= 0.72 else (None, score)


def load_registry(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_code: dict[str, list[dict[str, Any]]] = {}
    for source in payload.get("sources", []) or []:
        code = str(source.get("cplt_code") or "").upper()
        if code:
            by_code.setdefault(code, []).append(source)
    return by_code


def root_host(url: str) -> str:
    host = urlparse(url).netloc.lower().split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host


def same_official_domain(base_url: str, candidate_url: str) -> bool:
    base = root_host(base_url)
    host = urlparse(candidate_url).netloc.lower().split(":", 1)[0]
    return bool(base and host and (host == base or host.endswith("." + base)))


def text_key(value: str) -> str:
    return ascii_key(value or "")


def ordinance_signal(text: str, href: str) -> int:
    joined = text_key(f"{text} {href}")
    score = 0
    if "ordenanza" in joined:
        score += 10
    if "actos y resoluciones" in joined or "efectos sobre terceros" in joined:
        score += 5
    if "transparencia" in joined:
        score += 2
    if urlparse(href).path.lower().endswith(".pdf"):
        score += 2
    return score


def crawl_priority(text: str, href: str) -> int:
    joined = text_key(f"{text} {href}")
    score = 0
    if "ordenanza" in joined:
        score += 20
    if "transparencia" in joined:
        score += 10
    if "actos" in joined and "terceros" in joined:
        score += 8
    return score


def cms_family(html: str, url: str) -> str:
    key = html.lower()
    host = urlparse(url).netloc.lower()
    if host in PORTAL_HOSTS or "portaltransparencia.cl" in host:
        return "portal_transparencia"
    if "wp-content/" in key or "wp-includes/" in key:
        return "wordpress"
    if "joomla" in key or "/components/com_" in key:
        return "joomla"
    if "drupal-settings-json" in key or "/sites/default/files/" in key:
        return "drupal"
    return "custom_or_static"


def fetch_page(session: requests.Session, url: str, timeout: float) -> dict[str, Any]:
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        ctype = (response.headers.get("content-type") or "").split(";", 1)[0].lower()
        result: dict[str, Any] = {
            "requested_url": url,
            "status_code": response.status_code,
            "resolved_url": response.url,
            "content_type": ctype,
            "ok": response.status_code < 400,
        }
        if response.status_code < 400 and ("html" in ctype or not ctype):
            response.encoding = response.apparent_encoding or response.encoding or "utf-8"
            result["html"] = response.text[:2_000_000]
            result["family"] = cms_family(result["html"], response.url)
        return result
    except requests.RequestException as exc:
        return {
            "requested_url": url,
            "status_code": None,
            "resolved_url": None,
            "content_type": None,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def probe_resource(session: requests.Session, url: str, timeout: float) -> dict[str, Any]:
    try:
        with session.get(url, timeout=timeout, allow_redirects=True, stream=True) as response:
            ctype = (response.headers.get("content-type") or "").split(";", 1)[0].lower()
            first = b""
            if response.status_code < 400:
                try:
                    first = next(response.iter_content(32), b"")
                except Exception:
                    first = b""
            return {
                "requested_url": url,
                "status_code": response.status_code,
                "resolved_url": response.url,
                "content_type": ctype,
                "ok": response.status_code < 400,
                "looks_pdf": ctype == "application/pdf" or first.startswith(b"%PDF"),
            }
    except requests.RequestException as exc:
        return {
            "requested_url": url,
            "status_code": None,
            "resolved_url": None,
            "content_type": None,
            "ok": False,
            "looks_pdf": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def candidate_record(text: str, href: str, source_page: str, family: str | None) -> dict[str, Any]:
    return {
        "label": re.sub(r"\s+", " ", text or "").strip()[:500],
        "url": normalized_url(href),
        "source_page": source_page,
        "signal": ordinance_signal(text, href),
        "kind": "document" if urlparse(href).path.lower().endswith(".pdf") else "listing",
        "family": family,
    }


def discover_official_site(
    session: requests.Session,
    base_url: str,
    *,
    max_pages: int,
    timeout: float,
) -> dict[str, Any]:
    base_url = normalized_url(base_url)
    queue: deque[tuple[str, int, int]] = deque([(base_url, 0, 100)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}

    while queue and len(pages) < max_pages:
        url, depth, _priority = queue.popleft()
        url = normalized_url(url)
        if url in visited:
            continue
        visited.add(url)
        page = fetch_page(session, url, timeout)
        page_public = {k: v for k, v in page.items() if k != "html"}
        pages.append(page_public)
        html = page.get("html")
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")
        next_links: list[tuple[int, str]] = []
        for anchor in soup.find_all("a", href=True):
            raw_href = anchor.get("href") or ""
            if raw_href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or url, raw_href))
            label = " ".join(anchor.stripped_strings)
            signal = ordinance_signal(label, href)
            official = same_official_domain(base_url, href)
            portal = urlparse(href).netloc.lower() in PORTAL_HOSTS or "portaltransparencia.cl" in urlparse(href).netloc.lower()
            if signal >= 5 and (official or portal):
                current = candidate_record(label, href, page.get("resolved_url") or url, page.get("family"))
                previous = candidates.get(current["url"])
                if previous is None or current["signal"] > previous["signal"]:
                    candidates[current["url"]] = current

            if depth >= 2 or not official or urlparse(href).path.lower().endswith(".pdf"):
                continue
            priority = crawl_priority(label, href)
            if priority > 0 and href not in visited:
                next_links.append((priority, href))

        for priority, href in sorted(next_links, reverse=True)[:20]:
            queue.append((href, depth + 1, priority))

    # Conservative fallback for sites whose home page does not expose the
    # transparency navigation. These are probes, never evidence of absence.
    if not candidates and len(pages) < max_pages:
        for path in COMMON_PATHS:
            if len(pages) >= max_pages:
                break
            url = normalized_url(urljoin(base_url.rstrip("/") + "/", path.lstrip("/")))
            if url in visited:
                continue
            visited.add(url)
            page = fetch_page(session, url, timeout)
            page_public = {k: v for k, v in page.items() if k != "html"}
            pages.append(page_public)
            if page.get("ok"):
                html = page.get("html") or ""
                label = urlparse(page.get("resolved_url") or url).path
                signal = ordinance_signal(label, page.get("resolved_url") or url)
                if signal >= 5 or "ordenanza" in text_key(html[:50_000]):
                    record = candidate_record(
                        label or "ruta candidata de ordenanzas",
                        page.get("resolved_url") or url,
                        page.get("resolved_url") or url,
                        page.get("family"),
                    )
                    record["signal"] = max(record["signal"], 5)
                    candidates[record["url"]] = record

    ranked = sorted(candidates.values(), key=lambda item: (-int(item["signal"]), item["url"]))
    for candidate in ranked[:5]:
        candidate["probe"] = probe_resource(session, candidate["url"], timeout)

    return {
        "base_url": base_url,
        "pages_attempted": len(pages),
        "site_reachable": any(page.get("ok") for page in pages),
        "pages": pages,
        "candidate_sources": ranked[:15],
        "candidate_count": len(ranked),
    }


def portal_ordinance_url(code: str) -> str:
    return f"https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/{code}/PDO/AD"


def discovery_state(item: dict[str, Any]) -> str:
    site = item.get("official_site") or {}
    candidates = site.get("candidate_sources") or []
    if candidates:
        return "candidate_found"
    if item.get("existing_sources"):
        return "known_partial"
    if site.get("site_reachable"):
        return "site_reachable_no_candidate"
    if item.get("ta_status") == "portal":
        return "portal_candidate_unverified"
    return "unresolved"


def discover_one(
    session: requests.Session,
    organism: dict[str, Any],
    master: list[dict[str, str]],
    registry_by_code: dict[str, list[dict[str, Any]]],
    *,
    max_pages: int,
    timeout: float,
) -> dict[str, Any]:
    code = organism["cplt_code"]
    matched, match_score = best_master_match(organism, master)
    municipal_web = (matched or {}).get("web_municipal") or ""

    official_site = (
        discover_official_site(session, municipal_web, max_pages=max_pages, timeout=timeout)
        if municipal_web
        else {
            "base_url": None,
            "pages_attempted": 0,
            "site_reachable": False,
            "pages": [],
            "candidate_sources": [],
            "candidate_count": 0,
        }
    )

    item: dict[str, Any] = {
        "cplt_code": code,
        "organism_name": organism.get("organism_name"),
        "municipality_key": organism.get("municipality_key"),
        "ta_status": organism.get("ta_status"),
        "ta_link": organism.get("ta_link"),
        "sai_link": organism.get("sai_link"),
        "portal_ordinance_candidate": portal_ordinance_url(code) if organism.get("ta_status") == "portal" else None,
        "master_match": {
            "comuna_nombre": (matched or {}).get("comuna_nombre"),
            "region_id": (matched or {}).get("region_id"),
            "region_nombre": (matched or {}).get("region_nombre"),
            "web_municipal": municipal_web or None,
            "match_score": round(match_score, 3),
        },
        "existing_sources": [
            {
                "id": source.get("id"),
                "index_url": source.get("index_url"),
                "coverage_strategy": source.get("coverage_strategy"),
                "authoritative_listing": source.get("authoritative_listing"),
            }
            for source in registry_by_code.get(code, [])
        ],
        "official_site": official_site,
        "coverage_complete": False,
        "source_exhausted": False,
        "discovered_at": now_iso(),
    }
    item["state"] = discovery_state(item)
    return item


def build_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts = Counter(record.get("state") for record in records)
    ta_counts = Counter(record.get("ta_status") for record in records)
    family_counts: Counter[str] = Counter()
    candidate_municipalities = 0
    candidate_sources = 0
    site_reachable = 0
    master_matched = 0

    for record in records:
        match = record.get("master_match") or {}
        if match.get("web_municipal"):
            master_matched += 1
        site = record.get("official_site") or {}
        if site.get("site_reachable"):
            site_reachable += 1
        candidates = site.get("candidate_sources") or []
        if candidates:
            candidate_municipalities += 1
        candidate_sources += len(candidates)
        for candidate in candidates:
            family_counts[str(candidate.get("family") or "unknown")] += 1

    return {
        "records": len(records),
        "states": dict(sorted(state_counts.items())),
        "ta_status": dict(sorted(ta_counts.items())),
        "master_matched": master_matched,
        "site_reachable": site_reachable,
        "municipalities_with_candidate_sources": candidate_municipalities,
        "candidate_sources": candidate_sources,
        "candidate_families": dict(family_counts.most_common()),
    }


def cmd_discover(args: argparse.Namespace) -> int:
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard configuration")

    session = make_session()
    directory = sorted(load_directory(session), key=lambda item: item["cplt_code"])
    if len(directory) != 345:
        raise AssertionError(f"Expected 345 municipalities from CPLT directory, got {len(directory)}")

    master = load_master(args.master)
    registry = load_registry(args.registry)
    selected = [
        organism
        for idx, organism in enumerate(directory)
        if idx % args.shard_count == args.shard_index
    ]

    records: list[dict[str, Any]] = []
    for organism in selected:
        record = discover_one(
            session,
            organism,
            master,
            registry,
            max_pages=args.max_site_pages,
            timeout=args.timeout,
        )
        records.append(record)
        print(
            f"{record['cplt_code']} {record.get('organism_name')}: "
            f"state={record['state']} candidates={record['official_site']['candidate_count']} "
            f"reachable={record['official_site']['site_reachable']}"
        )

    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0009",
        "policy": "DISCOVERY ONLY; NO SAMPLING; FAIL CLOSED; absence of a hit is never evidence of no ordinances",
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "summary": build_summary(records),
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SHARD SUMMARY", json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    paths = sorted(args.input_dir.glob("national-discovery-*.json"))
    if not paths:
        raise AssertionError(f"No shard files in {args.input_dir}")

    by_code: dict[str, dict[str, Any]] = {}
    shards: set[int] = set()
    shard_count: int | None = None
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        shard = payload.get("shard") or {}
        if isinstance(shard.get("index"), int):
            shards.add(shard["index"])
        if isinstance(shard.get("count"), int):
            shard_count = shard["count"] if shard_count is None else shard_count
            if shard["count"] != shard_count:
                raise AssertionError("Inconsistent shard count")
        for record in payload.get("records", []) or []:
            code = record.get("cplt_code")
            if not code:
                raise AssertionError(f"Record without CPLT code in {path}")
            if code in by_code:
                raise AssertionError(f"Duplicate CPLT code across shards: {code}")
            by_code[code] = record

    if shard_count is not None and shards != set(range(shard_count)):
        raise AssertionError(f"Missing shards: expected {shard_count}, got {sorted(shards)}")
    if len(by_code) != 345:
        raise AssertionError(f"National discovery must contain 345 municipalities, got {len(by_code)}")

    records = [by_code[code] for code in sorted(by_code)]
    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0009",
        "policy": "DISCOVERY ONLY; NO SAMPLING; FAIL CLOSED; no municipality is complete at this stage",
        "municipalities_total": 345,
        "communes_total": 346,
        "summary": build_summary(records),
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Discovery stage must not mark municipalities complete")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("NATIONAL SUMMARY", json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover")
    discover.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    discover.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    discover.add_argument("--out", type=Path, default=DEFAULT_OUT)
    discover.add_argument("--shard-index", type=int, default=0)
    discover.add_argument("--shard-count", type=int, default=1)
    discover.add_argument("--max-site-pages", type=int, default=8)
    discover.add_argument("--timeout", type=float, default=8.0)
    discover.set_defaults(func=cmd_discover)

    merge = sub.add_parser("merge")
    merge.add_argument("--input-dir", type=Path, required=True)
    merge.add_argument("--out", type=Path, default=DEFAULT_OUT)
    merge.set_defaults(func=cmd_merge)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
