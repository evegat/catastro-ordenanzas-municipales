"""Audit exhaustive municipal ordinance coverage from authoritative official listings.

This module is deliberately stricter than the historical seed-based recovery:
- a municipality is never considered covered because one document was found;
- paginated official listings must be exhausted;
- every ordinance-like candidate must resolve to a verifiable PDF;
- national completeness is reported separately from the verified partial corpus.

Supported exhaustive strategies currently:
- wordpress_repository: listing pages expose ordinance headings and direct PDF links;
- wordpress_category: listing pages expose ordinance posts which are followed to PDFs.

Other strategies remain explicitly partial until an exhaustive parser is implemented.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from cplt_transparencia_crawler import (
    ascii_key,
    fetch_html,
    load_directory,
    make_session,
    normalize_text,
    now_iso,
    verify_pdf,
)

DEFAULT_REGISTRY = Path("data/municipal_source_registry.json")
DEFAULT_OUT = Path("data/municipal_exhaustive_coverage.json")


@dataclass
class Anchor:
    href: str
    text: str
    heading: str


class ContextLinkParser(HTMLParser):
    """Capture anchors together with the nearest preceding heading."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[Anchor] = []
        self.current_heading_tag: str | None = None
        self.current_heading_parts: list[str] = []
        self.last_heading = ""
        self.anchor_href: str | None = None
        self.anchor_parts: list[str] = []
        self.anchor_heading = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_d = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading_tag = tag
            self.current_heading_parts = []
        elif tag == "a":
            self.anchor_href = attrs_d.get("href") or ""
            self.anchor_parts = []
            self.anchor_heading = self.last_heading
        elif tag == "img" and self.anchor_href is not None:
            alt = attrs_d.get("alt") or attrs_d.get("title") or ""
            if alt:
                self.anchor_parts.append(alt)

    def handle_data(self, data: str) -> None:
        if self.current_heading_tag is not None:
            self.current_heading_parts.append(data)
        if self.anchor_href is not None:
            self.anchor_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.current_heading_tag == tag:
            self.last_heading = normalize_text(" ".join(self.current_heading_parts))
            self.current_heading_tag = None
            self.current_heading_parts = []
        elif tag == "a" and self.anchor_href is not None:
            self.anchors.append(
                Anchor(
                    href=self.anchor_href,
                    text=normalize_text(" ".join(self.anchor_parts)),
                    heading=self.anchor_heading,
                )
            )
            self.anchor_href = None
            self.anchor_parts = []
            self.anchor_heading = ""


def parse_links(text: str) -> list[Anchor]:
    parser = ContextLinkParser()
    parser.feed(text)
    parser.close()
    return parser.anchors


def is_ordinance_text(value: str) -> bool:
    return "ordenanza" in ascii_key(value)


def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def pdf_targets(url: str, base_url: str) -> list[str]:
    """Return direct PDFs, including PDFs wrapped by common viewer query params."""
    absolute = urljoin(base_url, url)
    out: list[str] = []
    if is_pdf_url(absolute):
        out.append(absolute)
    query = parse_qs(urlparse(absolute).query)
    for key in ("file", "pdf", "url", "document"):
        for value in query.get(key, []):
            candidate = urljoin(absolute, value)
            if is_pdf_url(candidate):
                out.append(candidate)
    return list(dict.fromkeys(out))


def ordinance_number(title: str) -> str:
    key = normalize_text(title)
    match = re.search(
        r"ordenanza\s+(?:local\s+)?(?:n(?:[°ºo.]|ro\.?|umero)?\s*)?([0-9]+(?:\s*[/.-]\s*[0-9]+)?)",
        key,
        flags=re.I,
    )
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(1))


def page_number(url: str) -> int | None:
    match = re.search(r"/page/(\d+)/?", urlparse(url).path, flags=re.I)
    return int(match.group(1)) if match else None


def page_url(index_url: str, page: int) -> str:
    if page == 1:
        return index_url
    return index_url.rstrip("/") + f"/page/{page}/"


def listing_pages(session, index_url: str, max_pages_cap: int) -> tuple[list[tuple[str, str]], list[str]]:
    """Exhaust WordPress-style numeric pagination, detecting the advertised maximum."""
    errors: list[str] = []
    first_text, first_resolved, _ = fetch_html(session, index_url)
    first_links = parse_links(first_text)
    advertised = [page_number(urljoin(first_resolved, a.href)) for a in first_links]
    advertised = [n for n in advertised if n is not None]
    max_page = max(advertised, default=1)
    max_page = min(max_page, max_pages_cap)

    pages: list[tuple[str, str]] = [(first_resolved, first_text)]
    for n in range(2, max_page + 1):
        url = page_url(first_resolved, n)
        try:
            text, resolved, _ = fetch_html(session, url)
            pages.append((resolved, text))
        except Exception as exc:
            errors.append(f"page_{n}: {type(exc).__name__}: {exc}")
    return pages, errors


def direct_pdf_candidates(pages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for listing_url, text in pages:
        for anchor in parse_links(text):
            context = anchor.heading or anchor.text
            if not is_ordinance_text(context):
                continue
            targets = pdf_targets(anchor.href, listing_url)
            if not targets and "pdf" in ascii_key(anchor.text):
                targets = [urljoin(listing_url, anchor.href)]
            for href in targets:
                candidates[href] = {
                    "titulo": context,
                    "numero": ordinance_number(context),
                    "listing_url": listing_url,
                    "document_url": href,
                    "discovery": "direct_listing_pdf",
                }
    return list(candidates.values())


def category_post_candidates(session, pages: list[tuple[str, str]], index_host: str) -> tuple[list[dict[str, Any]], list[str]]:
    posts: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for listing_url, text in pages:
        for anchor in parse_links(text):
            href = urljoin(listing_url, anchor.href)
            title = anchor.text or anchor.heading
            if not is_ordinance_text(title):
                continue
            if urlparse(href).netloc.lower() != index_host:
                continue
            posts[href] = {"titulo": title, "numero": ordinance_number(title), "listing_url": listing_url}

    candidates: list[dict[str, Any]] = []
    for post_url, meta in posts.items():
        direct_targets = pdf_targets(post_url, post_url)
        if direct_targets:
            for target in direct_targets:
                candidates.append({**meta, "document_url": target, "discovery": "category_direct_pdf"})
            continue
        try:
            text, resolved, _ = fetch_html(session, post_url)
            pdfs: list[str] = []
            for anchor in parse_links(text):
                pdfs.extend(pdf_targets(anchor.href, resolved))
            # Some WordPress/PDF.js integrations store the viewer URL in raw HTML
            # without presenting the PDF itself as an anchor. Capture those too.
            for raw in re.findall(r"https?[^\"'<>\s]+", text):
                pdfs.extend(pdf_targets(raw.replace("&amp;", "&"), resolved))
            pdfs = list(dict.fromkeys(pdfs))
            if not pdfs:
                candidates.append({**meta, "detail_url": resolved, "document_url": None, "discovery": "category_post_no_pdf"})
            else:
                for pdf in pdfs:
                    candidates.append({**meta, "detail_url": resolved, "document_url": pdf, "discovery": "category_post_pdf"})
        except Exception as exc:
            errors.append(f"detail {post_url}: {type(exc).__name__}: {exc}")
            candidates.append({**meta, "detail_url": post_url, "document_url": None, "discovery": "category_post_error"})
    return candidates, errors


def audit_source(session, source: dict[str, Any]) -> dict[str, Any]:
    strategy = source.get("coverage_strategy") or "partial_seed"
    result: dict[str, Any] = {
        "source_id": source["id"],
        "municipality": source["municipality"],
        "cplt_code": source.get("cplt_code"),
        "index_url": source["index_url"],
        "authoritative_listing": bool(source.get("authoritative_listing")),
        "coverage_strategy": strategy,
        "audited_at": now_iso(),
        "listing_pages": 0,
        "candidate_count": 0,
        "verified_count": 0,
        "unresolved_count": 0,
        "listing_exhausted": False,
        "coverage_complete": False,
        "errors": [],
        "records": [],
    }
    if strategy not in {"wordpress_repository", "wordpress_category"}:
        result["errors"].append(f"strategy_not_exhaustive_yet: {strategy}")
        return result

    cap = int(source.get("max_pages", 250))
    try:
        pages, page_errors = listing_pages(session, source["index_url"], cap)
    except Exception as exc:
        result["errors"].append(f"listing_fetch: {type(exc).__name__}: {exc}")
        return result

    result["listing_pages"] = len(pages)
    result["errors"].extend(page_errors)
    result["listing_exhausted"] = not page_errors

    if strategy == "wordpress_repository":
        candidates = direct_pdf_candidates(pages)
        detail_errors: list[str] = []
    else:
        host = urlparse(source["index_url"]).netloc.lower()
        candidates, detail_errors = category_post_candidates(session, pages, host)
    result["errors"].extend(detail_errors)

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (
            candidate.get("numero") or candidate.get("titulo") or "",
            candidate.get("document_url") or candidate.get("detail_url") or "",
        )
        dedup[key] = candidate
    candidates = list(dedup.values())

    for candidate in candidates:
        document_url = candidate.get("document_url")
        if document_url:
            verification = verify_pdf(session, document_url)
        else:
            verification = {"status": "unresolved", "reason": "no_document_url", "verified_at": now_iso()}
        result["records"].append({**candidate, "verification": verification})

    result["candidate_count"] = len(result["records"])
    result["verified_count"] = sum(r["verification"].get("status") == "verified" for r in result["records"])
    result["unresolved_count"] = sum(r["verification"].get("status") != "verified" for r in result["records"])
    result["coverage_complete"] = bool(
        result["authoritative_listing"]
        and result["listing_exhausted"]
        and not detail_errors
        and result["candidate_count"] > 0
        and result["unresolved_count"] == 0
    )
    return result


def national_coverage(directory: list[dict[str, Any]], audits: list[dict[str, Any]]) -> dict[str, Any]:
    by_code: dict[str, list[dict[str, Any]]] = {}
    for audit in audits:
        if audit.get("cplt_code"):
            by_code.setdefault(audit["cplt_code"], []).append(audit)

    municipalities = []
    for org in directory:
        code = org["cplt_code"]
        source_audits = by_code.get(code, [])
        complete = any(a.get("coverage_complete") for a in source_audits)
        status = "complete" if complete else ("partial" if source_audits else "unregistered")
        municipalities.append({
            "cplt_code": code,
            "organism_name": org.get("organism_name"),
            "status": status,
            "registered_sources": len(source_audits),
            "verified_records": sum(int(a.get("verified_count") or 0) for a in source_audits),
        })

    counts = {
        "municipalities_total": len(municipalities),
        "complete": sum(m["status"] == "complete" for m in municipalities),
        "partial": sum(m["status"] == "partial" for m in municipalities),
        "unregistered": sum(m["status"] == "unregistered" for m in municipalities),
    }
    return {
        "generated_at": now_iso(),
        "definition": "complete = authoritative official ordinance listing exhausted and every discovered ordinance candidate verified as PDF",
        "counts": counts,
        "national_complete": counts["complete"] == counts["municipalities_total"],
        "municipalities": municipalities,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source", action="append", default=[])
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    sources = registry.get("sources", [])
    if args.source:
        wanted = set(args.source)
        sources = [s for s in sources if s["id"] in wanted]

    session = make_session()
    audits = []
    for source in sources:
        audit = audit_source(session, source)
        audits.append(audit)
        print(
            f"{source['id']}: strategy={audit['coverage_strategy']} pages={audit['listing_pages']} "
            f"candidates={audit['candidate_count']} verified={audit['verified_count']} "
            f"unresolved={audit['unresolved_count']} complete={audit['coverage_complete']}"
        )

    directory = load_directory(session)
    coverage = national_coverage(directory, audits)
    payload = {
        "generated_at": now_iso(),
        "policy": "NO SAMPLING: all discoverable ordinances from each authoritative official listing must be enumerated and verified",
        "source_audits": audits,
        "national_coverage": coverage,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("NATIONAL COVERAGE", json.dumps(coverage["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
