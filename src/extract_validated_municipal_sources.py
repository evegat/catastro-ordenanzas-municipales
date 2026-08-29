"""Exhaustively traverse validated municipal ordinance source seeds.

MW-P090-0010 operates on institutionally validated municipal sites discovered by
MW-P090-0009. It gathers documentary evidence only; it does not publish records
or certify municipal legal completeness.

Three states are intentionally independent:
- listing_exhausted: every discoverable relevant page of this source was visited;
- documents_resolved: every document candidate discovered from the source was
  successfully downloaded and verified as a PDF;
- coverage_complete: always False here; municipality-level completeness requires
  reconciliation across all official sources and BCN/LeyChile.
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
from bs4 import BeautifulSoup

from cplt_transparencia_crawler import ascii_key, make_session, now_iso

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEEDS = REPO_ROOT / "data" / "validated_municipal_source_seeds.json"
DEFAULT_OUT = REPO_ROOT / "data" / "validated_municipal_extraction.json"
PORTAL_HOST = "portaltransparencia.cl"
PDF_EXTENSIONS = (".pdf", ".pdf/", ".pdf?", ".PDF", ".PDF/")


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
    if any(key in query for key in ("download", "file", "archivo", "document", "id")):
        joined = text_key(url)
        return any(token in joined for token in ("download", "phocadownload", "archivo", "document", "ordenanza"))
    return False


def ordinance_context(text: str) -> bool:
    key = text_key(text)
    return any(token in key for token in ("ordenanza", "ordenanzas", "derechos municipales"))


def navigation_context(text: str, href: str) -> bool:
    key = text_key(f"{text} {href}")
    return any(
        token in key
        for token in (
            "ordenanza", "ordenanzas", "siguiente", "anterior", "next", "previous",
            "pagin", "start=", "page=", "/page/", "phocadownload", "transparencia"
        )
    )


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
    if not years:
        return None
    return int(years[-1])


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
            too_large = False
            for chunk in response.iter_content(128 * 1024):
                if not chunk:
                    continue
                if len(prefix) < 16:
                    prefix += chunk[: 16 - len(prefix)]
                total += len(chunk)
                if total > max_bytes:
                    too_large = True
                    break
                digest.update(chunk)
            if too_large:
                return {
                    "status": "too_large",
                    "http_status": response.status_code,
                    "resolved_url": response.url,
                    "content_type": ctype,
                    "bytes_read": total,
                    "limit_bytes": max_bytes,
                }
            looks_pdf = prefix.startswith(b"%PDF")
            if not looks_pdf:
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
) -> None:
    url = normalized_url(url)
    if not url:
        return
    key = candidate_key(url)
    record = {
        "url": url,
        "label": re.sub(r"\s+", " ", label or "").strip()[:1000],
        "source_page": source_page,
        "preliminary_type": preliminary_act_type(label, url),
        "number_hint": extract_number(label, url),
        "year_hint": extract_year(label, url),
    }
    previous = candidates.get(key)
    if previous is None or len(record["label"]) > len(previous.get("label", "")):
        candidates[key] = record


def crawl_source(
    session: requests.Session,
    *,
    municipality: dict[str, Any],
    source_url: str,
    timeout: float,
    max_pages: int,
    max_pdf_bytes: int,
) -> dict[str, Any]:
    seed_site = municipality["seed_site"]
    source_url = normalized_url(source_url)
    queue: deque[tuple[str, int, bool]] = deque([(source_url, 0, True)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}
    page_failures = 0
    max_pages_hit = False

    # A seed may itself resolve as a document (e.g. a download controller).
    initial_pdfish = is_pdfish_url(source_url)
    if initial_pdfish:
        add_candidate(candidates, url=source_url, label="", source_page=source_url)

    while queue:
        if len(pages) >= max_pages:
            max_pages_hit = True
            break
        page_url, depth, trusted_context = queue.popleft()
        page_url = normalized_url(page_url)
        if not page_url or page_url in visited:
            continue
        visited.add(page_url)

        page = fetch_html(session, page_url, timeout)
        public_page = {k: v for k, v in page.items() if k != "html"}
        pages.append(public_page)
        if not page.get("ok"):
            page_failures += 1
            continue
        html = page.get("html")
        if not html:
            # Non-HTML URLs are handled as document candidates below.
            if page.get("content_type") == "application/pdf" or is_pdfish_url(page.get("resolved_url") or page_url):
                add_candidate(
                    candidates,
                    url=page.get("resolved_url") or page_url,
                    label="",
                    source_page=page_url,
                )
            continue

        soup = BeautifulSoup(html, "html.parser")
        page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        page_is_ordinance_context = trusted_context or ordinance_context(page_title) or ordinance_context(page_url)
        next_pages: list[tuple[int, str, bool]] = []

        for anchor in soup.find_all("a", href=True):
            raw_href = anchor.get("href") or ""
            if raw_href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or page_url, raw_href))
            label = " ".join(anchor.stripped_strings)
            if not href:
                continue
            same_domain = allowed_domain(seed_site, href)
            is_portal = PORTAL_HOST in root_host(href)
            relevant_text = ordinance_context(f"{label} {href}")
            pdfish = is_pdfish_url(href)

            # On a confirmed ordinance listing, PDF/download links are in scope
            # even when the anchor text is only "Enlace" or "Descargar".
            generic_download = text_key(label) in {"enlace", "descargar", "ver", "archivo", "documento", "pdf"}
            if (same_domain or is_portal) and (
                relevant_text
                or pdfish
                or (page_is_ordinance_context and generic_download)
            ):
                if pdfish or generic_download or is_portal:
                    add_candidate(candidates, url=href, label=label, source_page=page.get("resolved_url") or page_url)

            if depth >= 5 or not same_domain:
                continue
            nav = navigation_context(label, href)
            if nav:
                score = 20 if relevant_text else 10
                if any(token in text_key(f"{label} {href}") for token in ("siguiente", "next", "start=", "page=", "/page/", "pagin")):
                    score += 5
                next_pages.append((score, href, page_is_ordinance_context or relevant_text))

        # Some old municipal sites expose PDFs through object/embed/iframe.
        for tag in soup.find_all(["iframe", "embed", "object"]):
            raw = tag.get("src") or tag.get("data") or ""
            if not raw:
                continue
            href = normalized_url(urljoin(page.get("resolved_url") or page_url, raw))
            if (allowed_domain(seed_site, href) or PORTAL_HOST in root_host(href)) and is_pdfish_url(href):
                add_candidate(candidates, url=href, label=page_title, source_page=page.get("resolved_url") or page_url)

        for score, href, context in sorted(next_pages, key=lambda item: (-item[0], item[1])):
            if href not in visited:
                queue.append((href, depth + 1, context))

    # Resolve every candidate. Deduplication is by final PDF hash, while source
    # aliases are retained for traceability.
    verified_by_hash: dict[str, dict[str, Any]] = {}
    resolved_candidates: list[dict[str, Any]] = []
    unresolved = 0
    for candidate in sorted(candidates.values(), key=lambda item: item["url"]):
        evidence = download_pdf(session, candidate["url"], timeout, max_pdf_bytes)
        record = dict(candidate)
        record["verification"] = evidence
        if evidence.get("status") == "verified_pdf":
            sha = evidence["sha256"]
            canonical = verified_by_hash.get(sha)
            if canonical is None:
                verified_by_hash[sha] = record
                record["duplicate_of_sha256"] = None
            else:
                record["duplicate_of_sha256"] = sha
        else:
            record["duplicate_of_sha256"] = None
            unresolved += 1
        resolved_candidates.append(record)

    verified_unique = len(verified_by_hash)
    listing_exhausted = not max_pages_hit and page_failures == 0 and not queue
    documents_resolved = bool(resolved_candidates) and unresolved == 0
    return {
        "source_url": source_url,
        "pages_visited": len(pages),
        "page_failures": page_failures,
        "max_pages_hit": max_pages_hit,
        "listing_exhausted": listing_exhausted,
        "candidate_documents": len(resolved_candidates),
        "verified_document_links": sum(1 for item in resolved_candidates if item["verification"].get("status") == "verified_pdf"),
        "verified_unique_pdfs": verified_unique,
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
        )
        sources.append(source)
        print(
            f"    pages={source['pages_visited']} candidates={source['candidate_documents']} "
            f"unique_pdf={source['verified_unique_pdfs']} unresolved={source['unresolved_documents']} "
            f"listing_exhausted={source['listing_exhausted']}"
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
        "unique_verified_pdfs": len(hashes),
        "unresolved_documents": sum(source["unresolved_documents"] for source in sources),
        "coverage_complete": False,
        "sources": sources,
    }


def summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter()
    unique_hashes: set[str] = set()
    source_count = exhausted = unresolved = 0
    for record in records:
        source_count += record["sources_attempted"]
        exhausted += record["sources_listing_exhausted"]
        unresolved += record["unresolved_documents"]
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
            )
        )

    result = {
        "generated_at": now_iso(),
        "task_id": "MW-P090-0010",
        "policy": "EVIDENCE ONLY; NO SAMPLING; source exhaustion != municipal completeness",
        "shard": {"index": args.shard_index, "count": args.shard_count},
        "summary": summary(records),
        "records": records,
    }
    if any(record.get("coverage_complete") for record in records):
        raise AssertionError("Extraction phase must not mark municipal coverage complete")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("EXTRACTION SUMMARY", json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
