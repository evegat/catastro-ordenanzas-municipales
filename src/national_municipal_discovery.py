"""National discovery pass for municipal ordinance sources (P090).

Discovery is evidence gathering only. It never marks a municipality complete and
never promotes records to the public corpus.

Authoritative identity comes from the official CPLT regulated-organism directory.
`maestro_comunas_chile.csv` is only a seed list: its municipal-site URLs can be
stale or inferred, so a reachable seed must prove municipal identity before links
from that domain can be accepted as official-source candidates.
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

COMMON_PATHS = (
    "/ordenanzas/",
    "/ordenanzas-municipales/",
    "/transparencia/ordenanzas/",
    "/transparencia/ordenanzas.html",
    "/transparencia/",
)
PORTAL_HOSTS = {"portaltransparencia.cl", "www.portaltransparencia.cl"}
MUNICIPALITY_BRANDS = ("municipalidad", "municipio", "ilustre municipalidad")


def normalized_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    p = urlparse(raw)
    if not p.scheme:
        p = urlparse("https://" + raw)
    path = re.sub(r"/{2,}", "/", p.path or "/")
    return urlunparse(((p.scheme or "https").lower(), p.netloc.lower(), path, "", p.query, ""))


def strip_municipality_prefix(value: str) -> str:
    key = ascii_key(value)
    for prefix in (
        "ilustre municipalidad de ",
        "i municipalidad de ",
        "municipalidad de ",
        "ilustre municipalidad ",
        "municipalidad ",
    ):
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


def best_master_match(
    organism: dict[str, Any], master: list[dict[str, str]]
) -> tuple[dict[str, str] | None, float]:
    target = strip_municipality_prefix(organism.get("organism_name", ""))
    if not target:
        return None, 0.0
    for row in master:
        if master_key(row) == target:
            return row, 1.0
    scored = [
        (SequenceMatcher(None, target, master_key(row)).ratio(), row)
        for row in master
        if master_key(row)
    ]
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


def same_seed_domain(base_url: str, candidate_url: str) -> bool:
    base = root_host(base_url)
    host = root_host(candidate_url)
    return bool(base and host and (host == base or host.endswith("." + base)))


def text_key(value: str) -> str:
    return ascii_key(value or "")


def significant_name_tokens(name: str) -> list[str]:
    stop = {"de", "del", "la", "las", "los", "el", "y", "san", "santa"}
    return [token for token in strip_municipality_prefix(name).split() if token not in stop and len(token) >= 3]


def verify_municipal_identity(html: str, resolved_url: str, municipality_name: str) -> dict[str, Any]:
    """Conservatively verify that a seed site identifies as the intended municipality."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    headers = " ".join(node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2"], limit=12))
    body = soup.get_text(" ", strip=True)[:250_000]
    evidence = text_key(f"{title} {headers} {body}")
    host = text_key(root_host(resolved_url))
    name_key = strip_municipality_prefix(municipality_name)
    tokens = significant_name_tokens(municipality_name)

    exact_name = bool(name_key and name_key in evidence)
    token_hits = sum(token in evidence for token in tokens)
    name_match = exact_name or (bool(tokens) and token_hits == len(tokens))
    brand_match = any(brand in evidence for brand in MUNICIPALITY_BRANDS)
    host_match = bool(tokens and any(token in host for token in tokens))

    verified = bool(name_match and (brand_match or host_match))
    return {
        "verified": verified,
        "municipality_key": name_key,
        "exact_name_match": exact_name,
        "name_token_hits": token_hits,
        "name_token_total": len(tokens),
        "municipal_brand_match": brand_match,
        "host_name_match": host_match,
        "reason": (
            "municipality_identity_verified"
            if verified
            else "seed_reachable_but_municipal_identity_not_verified"
        ),
    }


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
    return (
        (20 if "ordenanza" in joined else 0)
        + (10 if "transparencia" in joined else 0)
        + (8 if "actos" in joined and "terceros" in joined else 0)
    )


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


def discover_seed_site(
    session: requests.Session,
    seed_url: str,
    municipality_name: str,
    *,
    max_pages: int,
    timeout: float,
) -> dict[str, Any]:
    """Probe a master-list seed and crawl it only after institutional identity verification."""
    seed_url = normalized_url(seed_url)
    if not seed_url:
        return {
            "seed_url": None,
            "seed_reachable": False,
            "identity_verified": False,
            "identity": {"verified": False, "reason": "no_seed_url"},
            "pages_attempted": 0,
            "pages": [],
            "candidate_sources": [],
            "candidate_count": 0,
        }

    first = fetch_page(session, seed_url, timeout)
    first_public = {k: v for k, v in first.items() if k != "html"}
    html = first.get("html") or ""
    identity = (
        verify_municipal_identity(html, first.get("resolved_url") or seed_url, municipality_name)
        if html
        else {"verified": False, "reason": "seed_unreachable_or_non_html"}
    )
    verified_identity = bool(identity.get("verified"))

    if not verified_identity:
        return {
            "seed_url": seed_url,
            "seed_reachable": bool(first.get("ok")),
            "identity_verified": False,
            "identity": identity,
            "pages_attempted": 1,
            "pages": [first_public],
            "candidate_sources": [],
            "candidate_count": 0,
        }

    queue: deque[tuple[str, int, int]] = deque([(first.get("resolved_url") or seed_url, 0, 100)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}
    cached_first_url = normalized_url(first.get("resolved_url") or seed_url)

    while queue and len(pages) < max_pages:
        url, depth, _priority = queue.popleft()
        url = normalized_url(url)
        if url in visited:
            continue
        visited.add(url)
        page = first if url == cached_first_url else fetch_page(session, url, timeout)
        page_public = {k: v for k, v in page.items() if k != "html"}
        pages.append(page_public)
        page_html = page.get("html")
        if not page_html:
            continue
        soup = BeautifulSoup(page_html, "html.parser")
        next_links: list[tuple[int, str]] = []
        for anchor in soup.find_all("a", href=True):
            raw_href = anchor.get("href") or ""
            if raw_href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or url, raw_href))
            label = " ".join(anchor.stripped_strings)
            signal = ordinance_signal(label, href)
            same_domain = same_seed_domain(seed_url, href)
            portal = "portaltransparencia.cl" in urlparse(href).netloc.lower()
            if signal >= 5 and (same_domain or portal):
                current = candidate_record(label, href, page.get("resolved_url") or url, page.get("family"))
                previous = candidates.get(current["url"])
                if previous is None or current["signal"] > previous["signal"]:
                    candidates[current["url"]] = current
            if depth >= 2 or not same_domain or urlparse(href).path.lower().endswith(".pdf"):
                continue
            priority = crawl_priority(label, href)
            if priority > 0 and href not in visited:
                next_links.append((priority, href))
        for priority, href in sorted(next_links, reverse=True)[:20]:
            queue.append((href, depth + 1, priority))

    if not candidates and len(pages) < max_pages:
        for path in COMMON_PATHS:
            if len(pages) >= max_pages:
                break
            url = normalized_url(urljoin(seed_url.rstrip("/") + "/", path.lstrip("/")))
            if url in visited:
                continue
            visited.add(url)
            page = fetch_page(session, url, timeout)
            pages.append({k: v for k, v in page.items() if k != "html"})
            page_html = page.get("html") or ""
            if page.get("ok") and (
                "ordenanza" in text_key(page_html[:100_000])
                or ordinance_signal(urlparse(page.get("resolved_url") or url).path, page.get("resolved_url") or url) >= 5
            ):
                record = candidate_record(
                    urlparse(page.get("resolved_url") or url).path or "ruta candidata de ordenanzas",
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
        "seed_url": seed_url,
        "seed_reachable": any(page.get("ok") for page in pages),
        "identity_verified": True,
        "identity": identity,
        "pages_attempted": len(pages),
        "pages": pages,
        "candidate_sources": ranked[:15],
        "candidate_count": len(ranked),
    }


def portal_ordinance_url(code: str) -> str:
    return f"https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/{code}/PDO/AD"


def discovery_state(item: dict[str, Any]) -> str:
    seed = item.get("municipal_site_seed") or {}
    if item.get("existing_sources"):
        return "known_partial"
    if seed.get("candidate_sources"):
        return "candidate_found"
    if seed.get("seed_reachable") and not seed.get("identity_verified"):
        return "seed_reachable_identity_unverified"
    if seed.get("identity_verified"):
        return "validated_site_no_candidate"
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
    master_seed = (matched or {}).get("web_municipal") or ""
    seed_result = discover_seed_site(
        session,
        master_seed,
        organism.get("organism_name") or (matched or {}).get("comuna_nombre") or "",
        max_pages=max_pages,
        timeout=timeout,
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
            "seed_web_municipal": master_seed or None,
            "match_score": round(match_score, 3),
            "authority": "seed_only_not_authoritative",
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
        "municipal_site_seed": seed_result,
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
    candidates_muni = candidates_total = reachable = identity_verified = master_matched = 0
    for record in records:
        match = record.get("master_match") or {}
        if match.get("seed_web_municipal"):
            master_matched += 1
        seed = record.get("municipal_site_seed") or {}
        if seed.get("seed_reachable"):
            reachable += 1
        if seed.get("identity_verified"):
            identity_verified += 1
        candidates = seed.get("candidate_sources") or []
        if candidates:
            candidates_muni += 1
        candidates_total += len(candidates)
        for candidate in candidates:
            family_counts[str(candidate.get("family") or "unknown")] += 1
    return {
        "records": len(records),
        "states": dict(sorted(state_counts.items())),
        "ta_status": dict(sorted(ta_counts.items())),
        "master_seed_matched": master_matched,
        "seed_sites_reachable": reachable,
        "seed_sites_identity_verified": identity_verified,
        "municipalities_with_candidate_sources": candidates_muni,
        "candidate_sources": candidates_total,
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
    selected = [item for idx, item in enumerate(directory) if idx % args.shard_count == args.shard_index]

    records: list[dict[str, Any]] = []
    for organism in selected:
        record = discover_one(
            session, organism, master, registry,
            max_pages=args.max_site_pages, timeout=args.timeout,
        )
        records.append(record)
        seed = record["municipal_site_seed"]
        print(
            f"{record['cplt_code']} {record.get('organism_name')}: state={record['state']} "
            f"identity={seed.get('identity_verified')} candidates={seed.get('candidate_count')} "
            f"reachable={seed.get('seed_reachable')}"
        )

    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0009",
        "policy": "DISCOVERY ONLY; NO SAMPLING; FAIL CLOSED; master municipal URLs are seeds until identity-verified",
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
            if shard_count is None:
                shard_count = shard["count"]
            elif shard["count"] != shard_count:
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
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Discovery stage must not mark municipalities complete")
    payload = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0009",
        "policy": "DISCOVERY ONLY; NO SAMPLING; FAIL CLOSED; no municipality is complete at this stage",
        "municipalities_total": 345,
        "communes_total": 346,
        "summary": build_summary(records),
        "records": records,
    }
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
    return build_parser().parse_args().func(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
