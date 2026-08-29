"""Scope-safe extraction of municipal ordinance evidence.

MW-P090-0010 consumes institutionally validated municipal source seeds. It
collects documentary evidence only; it never certifies municipality-level legal
completeness or promotes records to the public dashboard.

Safety invariants:
- traversal must remain inside the ordinance source family;
- generic transparency/category links never expand crawl scope;
- document candidates need ordinance context or a source-family match;
- large candidate explosions fail closed for review;
- listing exhaustion and municipal coverage are separate states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, deque
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag

from cplt_transparencia_crawler import ascii_key, make_session, now_iso

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEEDS = REPO_ROOT / "data" / "validated_municipal_source_seeds.json"
DEFAULT_OUT = REPO_ROOT / "data" / "validated_municipal_extraction.json"
PORTAL_HOST = "portaltransparencia.cl"
GENERIC_DOWNLOAD_LABELS = {"enlace", "descargar", "ver", "archivo", "documento", "pdf", "ver archivo"}


def normalized_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if not parsed.scheme:
        parsed = urlparse("https://" + raw)
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunparse(((parsed.scheme or "https").lower(), parsed.netloc.lower(), path, "", parsed.query, ""))


def root_host(url: str) -> str:
    host = urlparse(url).netloc.lower().split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host


def allowed_domain(seed_site: str, url: str) -> bool:
    seed = root_host(seed_site)
    host = root_host(url)
    if not seed or not host:
        return False
    return host == seed or host.endswith("." + seed) or seed.endswith("." + host)


def text_key(value: str) -> str:
    return ascii_key(value or "")


def is_pdfish_url(url: str) -> bool:
    lower = url.lower()
    if ".pdf" in lower:
        return True
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if any(key in query for key in ("download", "file", "archivo", "document")):
        joined = text_key(url)
        return any(token in joined for token in ("download", "phocadownload", "archivo", "document", "ordenanza"))
    return False


def ordinance_context(text: str) -> bool:
    key = text_key(text)
    return any(
        token in key
        for token in (
            "ordenanza",
            "ordenanzas",
            "derechos municipales",
            "ord municipal",
            "ord. municipal",
        )
    )


def pagination_context(text: str, href: str) -> bool:
    key = text_key(f"{text} {href}")
    return any(
        token in key
        for token in (
            "siguiente",
            "anterior",
            "next",
            "previous",
            "pagina",
            "paginacion",
            "start=",
            "page=",
            "paged=",
            "/page/",
        )
    )


def query_value_head(value: str) -> str:
    value = text_key(value)
    match = re.match(r"([0-9]+)", value)
    return match.group(1) if match else value


def source_scope_match(source_url: str, href: str) -> bool:
    """Return True only when href still belongs to the source's ordinance family."""
    source = urlparse(normalized_url(source_url))
    target = urlparse(normalized_url(href))
    if not source.netloc or not target.netloc or root_host(source_url) != root_host(href):
        return False

    if ordinance_context(href):
        return True

    source_q = parse_qs(source.query)
    target_q = parse_qs(target.query)

    if "id" in source_q and "id" in target_q:
        if query_value_head(source_q["id"][0]) == query_value_head(target_q["id"][0]):
            return True

    for key in ("vartipo", "vartipo2", "catid", "category"):
        if key in source_q and key in target_q:
            if text_key(source_q[key][0]) == text_key(target_q[key][0]):
                return True

    src_path = source.path.lower()
    tgt_path = target.path.lower()
    if "ordenanz" in src_path:
        if "ordenanz" in tgt_path:
            return True
        base = src_path if src_path.endswith("/") else src_path.rsplit("/", 1)[0] + "/"
        if "/ordenanzas/" in base and tgt_path.startswith(base):
            return True

    return False


def local_anchor_context(anchor: Tag) -> str:
    """Use nearby row/card text to interpret generic labels such as 'Enlace'."""
    parts = [" ".join(anchor.stripped_strings)]
    node: Tag | None = anchor
    for _ in range(5):
        parent = node.parent if isinstance(node, Tag) else None
        if not isinstance(parent, Tag):
            break
        node = parent
        if node.name in {"tr", "li", "article", "section", "div"}:
            text = " ".join(node.stripped_strings)
            if text:
                parts.append(text[:1800])
                break
    return " ".join(parts)


def preliminary_act_type(label: str, url: str) -> str:
    key = text_key(f"{label} {url}")
    if any(token in key for token in ("modifica", "modificacion", "modificase", "reemplaza", "incorpora")):
        return "modificacion"
    if "ordenanza" in key:
        return "ordenanza"
    return "acto_relacionado"


def extract_number(label: str, url: str) -> str | None:
    text = f"{label} {url}"
    patterns = (
        r"(?:ordenanza|ord)[^0-9]{0,12}(?:n(?:ro|°|º|o)?\.?\s*)?([0-9]{1,6}(?:\s*[-/]\s*[0-9]{2,4})?)",
        r"(?:n(?:ro|°|º|o)?\.?\s*)([0-9]{1,6}(?:\s*[-/]\s*[0-9]{2,4})?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", "", match.group(1))
    return None


def extract_year(label: str, url: str) -> int | None:
    years = re.findall(r"\b(19[8-9][0-9]|20[0-2][0-9])\b", f"{label} {url}")
    return int(years[-1]) if years else None


def fetch_html(session: requests.Session, url: str, timeout: float) -> dict[str, Any]:
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
        if response.status_code < 400 and ("html" in ctype or ctype in ("", "text/plain")):
            response.encoding = response.apparent_encoding or response.encoding or "utf-8"
            result["html"] = response.text[:3_000_000]
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


def download_pdf(session: requests.Session, url: str, timeout: float, max_bytes: int) -> dict[str, Any]:
    try:
        with session.get(url, timeout=timeout, allow_redirects=True, stream=True) as response:
            ctype = (response.headers.get("content-type") or "").split(";", 1)[0].lower()
            if response.status_code >= 400:
                return {
                    "status": "blocked_or_missing",
                    "http_status": response.status_code,
                    "resolved_url": response.url,
                    "content_type": ctype,
                }
            digest = hashlib.sha256()
            total = 0
            prefix = b""
            for chunk in response.iter_content(128 * 1024):
                if not chunk:
                    continue
                if len(prefix) < 16:
                    prefix += chunk[: 16 - len(prefix)]
                total += len(chunk)
                if total > max_bytes:
                    return {
                        "status": "too_large",
                        "http_status": response.status_code,
                        "resolved_url": response.url,
                        "content_type": ctype,
                        "bytes_read": total,
                        "limit_bytes": max_bytes,
                    }
                digest.update(chunk)
            if not prefix.startswith(b"%PDF"):
                return {
                    "status": "not_pdf",
                    "http_status": response.status_code,
                    "resolved_url": response.url,
                    "content_type": ctype,
                    "bytes": total,
                }
            return {
                "status": "verified_pdf",
                "http_status": response.status_code,
                "resolved_url": response.url,
                "content_type": ctype,
                "bytes": total,
                "sha256": digest.hexdigest(),
                "verified_at": now_iso(),
            }
    except requests.RequestException as exc:
        return {
            "status": "request_error",
            "http_status": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def candidate_key(url: str) -> str:
    parsed = urlparse(normalized_url(url))
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", parsed.query, ""))


def add_candidate(
    candidates: dict[str, dict[str, Any]],
    *,
    url: str,
    label: str,
    source_page: str,
    scope_reason: str,
) -> None:
    url = normalized_url(url)
    if not url:
        return
    key = candidate_key(url)
    clean_label = re.sub(r"\s+", " ", label or "").strip()[:1800]
    record = {
        "url": url,
        "label": clean_label,
        "source_page": source_page,
        "scope_reason": scope_reason,
        "preliminary_type": preliminary_act_type(clean_label, url),
        "number_hint": extract_number(clean_label, url),
        "year_hint": extract_year(clean_label, url),
    }
    previous = candidates.get(key)
    if previous is None or len(clean_label) > len(previous.get("label", "")):
        candidates[key] = record


def crawl_source(
    session: requests.Session,
    *,
    municipality: dict[str, Any],
    source_url: str,
    timeout: float,
    max_pages: int,
    max_pdf_bytes: int,
    max_candidates: int,
) -> dict[str, Any]:
    seed_site = municipality["seed_site"]
    source_url = normalized_url(source_url)
    queue: deque[tuple[str, int]] = deque([(source_url, 0)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}
    page_failures = 0
    max_pages_hit = False
    scope_guard_triggered = False
    scope_rejected_links = 0

    if is_pdfish_url(source_url):
        add_candidate(candidates, url=source_url, label="", source_page=source_url, scope_reason="seed_document")

    while queue:
        if len(pages) >= max_pages:
            max_pages_hit = True
            break
        if len(candidates) > max_candidates:
            scope_guard_triggered = True
            break

        page_url, depth = queue.popleft()
        page_url = normalized_url(page_url)
        if not page_url or page_url in visited:
            continue
        visited.add(page_url)

        page = fetch_html(session, page_url, timeout)
        pages.append({k: v for k, v in page.items() if k != "html"})
        if not page.get("ok"):
            page_failures += 1
            continue

        html = page.get("html")
        if not html:
            resolved = page.get("resolved_url") or page_url
            if page.get("content_type") == "application/pdf" or is_pdfish_url(resolved):
                add_candidate(
                    candidates,
                    url=resolved,
                    label="",
                    source_page=page_url,
                    scope_reason="resolved_seed_or_scoped_document",
                )
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        page_in_scope = (
            depth == 0
            or ordinance_context(page_title)
            or ordinance_context(page_url)
            or source_scope_match(source_url, page_url)
        )
        next_pages: list[tuple[int, str]] = []

        for anchor in soup.find_all("a", href=True):
            raw_href = anchor.get("href") or ""
            if raw_href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or page_url, raw_href))
            if not href:
                continue

            label = " ".join(anchor.stripped_strings)
            context = local_anchor_context(anchor)
            same_domain = allowed_domain(seed_site, href)
            is_portal = PORTAL_HOST in root_host(href)
            pdfish = is_pdfish_url(href)
            generic_download = text_key(label) in GENERIC_DOWNLOAD_LABELS
            relevant_context = ordinance_context(f"{context} {href}")
            scoped_family = source_scope_match(source_url, href) or source_scope_match(page_url, href)

            candidate_reason = ""
            if relevant_context:
                candidate_reason = "ordinance_context"
            elif scoped_family:
                candidate_reason = "source_family"
            elif depth == 0 and page_in_scope and generic_download and ordinance_context(context):
                candidate_reason = "ordinance_row"

            if (same_domain or is_portal) and candidate_reason and (pdfish or generic_download):
                add_candidate(
                    candidates,
                    url=href,
                    label=context or label,
                    source_page=page.get("resolved_url") or page_url,
                    scope_reason=candidate_reason,
                )
            elif (same_domain or is_portal) and (pdfish or generic_download):
                scope_rejected_links += 1

            if depth >= 5 or not same_domain or pdfish:
                continue

            nav_relevant = ordinance_context(f"{context} {href}")
            pager = pagination_context(label, href)
            if nav_relevant:
                next_pages.append((30, href))
            elif pager and (source_scope_match(source_url, href) or source_scope_match(page_url, href)):
                next_pages.append((20, href))

        for tag in soup.find_all(["iframe", "embed", "object"]):
            raw = tag.get("src") or tag.get("data") or ""
            if not raw:
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or page_url, raw))
            if not (allowed_domain(seed_site, href) or PORTAL_HOST in root_host(href)) or not is_pdfish_url(href):
                continue
            if ordinance_context(f"{page_title} {page_url}") or source_scope_match(source_url, href):
                add_candidate(
                    candidates,
                    url=href,
                    label=page_title,
                    source_page=page.get("resolved_url") or page_url,
                    scope_reason="embedded_scoped_document",
                )
            else:
                scope_rejected_links += 1

        for _, href in sorted(next_pages, key=lambda item: (-item[0], item[1])):
            if href not in visited:
                queue.append((href, depth + 1))

    if len(candidates) > max_candidates:
        scope_guard_triggered = True

    resolved_candidates: list[dict[str, Any]] = []
    verified_by_hash: dict[str, dict[str, Any]] = {}
    unresolved = 0
    if not scope_guard_triggered:
        for candidate in sorted(candidates.values(), key=lambda item: item["url"]):
            evidence = download_pdf(session, candidate["url"], timeout, max_pdf_bytes)
            record = dict(candidate)
            record["verification"] = evidence
            if evidence.get("status") == "verified_pdf":
                sha = evidence["sha256"]
                if sha not in verified_by_hash:
                    verified_by_hash[sha] = record
                    record["duplicate_of_sha256"] = None
                else:
                    record["duplicate_of_sha256"] = sha
            else:
                record["duplicate_of_sha256"] = None
                unresolved += 1
            resolved_candidates.append(record)

    listing_exhausted = not scope_guard_triggered and not max_pages_hit and page_failures == 0 and not queue
    documents_resolved = bool(resolved_candidates) and unresolved == 0

    return {
        "source_url": source_url,
        "pages_visited": len(pages),
        "page_failures": page_failures,
        "max_pages_hit": max_pages_hit,
        "scope_guard_triggered": scope_guard_triggered,
        "scope_rejected_links": scope_rejected_links,
        "listing_exhausted": listing_exhausted,
        "candidate_documents": len(candidates),
        "verified_document_links": sum(
            1 for item in resolved_candidates if (item.get("verification") or {}).get("status") == "verified_pdf"
        ),
        "verified_unique_pdfs": len(verified_by_hash),
        "unresolved_documents": unresolved,
        "documents_resolved": documents_resolved,
        "pages": pages,
        "documents": resolved_candidates,
    }


def extract_municipality(
    session: requests.Session,
    municipality: dict[str, Any],
    *,
    timeout: float,
    max_pages: int,
    max_pdf_bytes: int,
    max_candidates: int,
) -> dict[str, Any]:
    sources = []
    for source_url in municipality.get("sources", []) or []:
        print(f"  SOURCE {source_url}")
        source = crawl_source(
            session,
            municipality=municipality,
            source_url=source_url,
            timeout=timeout,
            max_pages=max_pages,
            max_pdf_bytes=max_pdf_bytes,
            max_candidates=max_candidates,
        )
        sources.append(source)
        print(
            f"    pages={source['pages_visited']} candidates={source['candidate_documents']} "
            f"unique_pdf={source['verified_unique_pdfs']} unresolved={source['unresolved_documents']} "
            f"listing_exhausted={source['listing_exhausted']} guard={source['scope_guard_triggered']}"
        )

    hashes: set[str] = set()
    for source in sources:
        for doc in source.get("documents", []):
            verification = doc.get("verification") or {}
            if verification.get("status") == "verified_pdf":
                hashes.add(verification["sha256"])

    return {
        "cplt_code": municipality["cplt_code"],
        "municipality": municipality["municipality"],
        "region_id": municipality.get("region_id"),
        "seed_site": municipality["seed_site"],
        "sources_attempted": len(sources),
        "sources_listing_exhausted": sum(1 for source in sources if source["listing_exhausted"]),
        "scope_guards_triggered": sum(1 for source in sources if source["scope_guard_triggered"]),
        "scope_rejected_links": sum(source["scope_rejected_links"] for source in sources),
        "unique_verified_pdfs": len(hashes),
        "unresolved_documents": sum(source["unresolved_documents"] for source in sources),
        "coverage_complete": False,
        "sources": sources,
    }


def summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter()
    unique_hashes: set[str] = set()
    source_count = exhausted = unresolved = guards = rejected = 0
    for record in records:
        source_count += record["sources_attempted"]
        exhausted += record["sources_listing_exhausted"]
        unresolved += record["unresolved_documents"]
        guards += record.get("scope_guards_triggered", 0)
        rejected += record.get("scope_rejected_links", 0)
        for source in record.get("sources", []):
            for doc in source.get("documents", []):
                verification = doc.get("verification") or {}
                status_counts[verification.get("status") or "unknown"] += 1
                if verification.get("status") == "verified_pdf":
                    unique_hashes.add(verification["sha256"])
    return {
        "municipalities": len(records),
        "sources_attempted": source_count,
        "sources_listing_exhausted": exhausted,
        "scope_guards_triggered": guards,
        "scope_rejected_links": rejected,
        "unique_verified_pdfs": len(unique_hashes),
        "unresolved_document_links": unresolved,
        "verification_status": dict(sorted(status_counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=250)
    parser.add_argument("--max-candidates", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--max-pdf-mb", type=int, default=80)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("Invalid shard configuration")

    payload = json.loads(args.seeds.read_text(encoding="utf-8"))
    municipalities = payload.get("municipalities", []) or []
    selected = [row for idx, row in enumerate(municipalities) if idx % args.shard_count == args.shard_index]
    session = make_session()
    records = []
    for municipality in selected:
        print(f"MUNICIPALITY {municipality['cplt_code']} {municipality['municipality']}")
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
        "task_id": "MW-P090-0010",
        "policy": "EVIDENCE ONLY; SCOPE-SAFE; source exhaustion != municipal completeness",
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "summary": summary(records),
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Extraction phase must not mark municipal coverage complete")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("EXTRACTION SUMMARY", json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 2 if result["summary"]["scope_guards_triggered"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
