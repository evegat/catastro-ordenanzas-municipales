"""Audit exhaustive municipal ordinance coverage from authoritative official listings.

Completeness rules:
- no municipality is complete because a sample document was found;
- paginated official sources must be exhausted, but source exhaustion is not municipal completeness;
- every in-scope candidate must be resolved and verified;
- related decrees/regulations are preserved but typed separately;
- municipality completeness requires explicit evidence that all relevant official sources are reconciled.
"""
from __future__ import annotations

import argparse
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from pypdf import PdfReader

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


def is_ordinance_text(value: str) -> bool:
    key = ascii_key(value)
    if "ordenanza" not in key:
        return False
    generic = {
        "decretos y ordenanzas",
        "categoria decretos y ordenanzas",
        "fichas ordenanza de artesania",
    }
    return key.strip(" :-") not in generic and not key.startswith("categoria ")


def legal_relation_type(title: str) -> str:
    key = ascii_key(title)
    if not key:
        return "documento_indice"
    if "reglamento" in key and "ordenanza" in key:
        return "acto_relacionado"
    if (
        "modifica" in key
        or "modificacion" in key
        or "agrega un nuevo texto" in key
        or "aprueba nuevo texto" in key
        or "nuevo derecho ordenanza" in key
    ) and "ordenanza" in key:
        return "modificacion"
    if key.startswith("decreto") and "ordenanza" in key:
        return "modificacion"
    if key.startswith("ordenanza") or key.startswith("texto refundido ordenanza"):
        return "ordenanza"
    if "ordenanza" in key:
        return "acto_relacionado"
    return "otro"


def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def pdf_targets(url: str, base_url: str) -> list[str]:
    """Resolve direct PDF links and common viewer query parameters."""
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
    match = re.search(
        r"ordenanza\s+(?:local\s+)?(?:n(?:[°ºo.]|ro\.?|umero)?\s*)?([0-9]+(?:\s*[/.-]\s*[0-9]+)?)",
        normalize_text(title),
        flags=re.I,
    )
    return re.sub(r"\s+", "", match.group(1)) if match else ""


def page_number(url: str) -> int | None:
    match = re.search(r"/page/(\d+)/?", urlparse(url).path, flags=re.I)
    return int(match.group(1)) if match else None


def page_url(index_url: str, page: int) -> str:
    if page == 1:
        return index_url
    return index_url.rstrip("/") + f"/page/{page}/"


def listing_pages(session, index_url: str, max_pages_cap: int) -> tuple[list[tuple[str, str]], list[str]]:
    errors: list[str] = []
    first_text, first_resolved, _ = fetch_html(session, index_url)
    soup = BeautifulSoup(first_text, "html.parser")
    advertised = []
    for a in soup.find_all("a", href=True):
        n = page_number(urljoin(first_resolved, a["href"]))
        if n is not None:
            advertised.append(n)
    max_page = min(max(advertised, default=1), max_pages_cap)

    pages: list[tuple[str, str]] = [(first_resolved, first_text)]
    for n in range(2, max_page + 1):
        try:
            text, resolved, _ = fetch_html(session, page_url(first_resolved, n))
            pages.append((resolved, text))
        except Exception as exc:
            errors.append(f"page_{n}: {type(exc).__name__}: {exc}")
    return pages, errors


def direct_pdf_candidates(pages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Extract direct PDF links from a repository, keeping their local heading context."""
    candidates: dict[str, dict[str, Any]] = {}
    for listing_url, text in pages:
        soup = BeautifulSoup(text, "html.parser")
        for a in soup.find_all("a", href=True):
            targets = pdf_targets(a["href"], listing_url)
            if not targets:
                continue
            heading = a.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            context = normalize_text(heading.get_text(" ", strip=True) if heading else a.get_text(" ", strip=True))
            if not is_ordinance_text(context):
                continue
            for target in targets:
                candidates[target] = {
                    "titulo": context,
                    "numero": ordinance_number(context),
                    "tipo_acto": legal_relation_type(context),
                    "listing_url": listing_url,
                    "document_url": target,
                    "discovery": "direct_listing_pdf",
                }
    return list(candidates.values())


def archive_entries(listing_url: str, text: str) -> list[dict[str, str]]:
    """Return post-level archive entries without pairing titles with navigation/sidebar links."""
    soup = BeautifulSoup(text, "html.parser")
    entries: dict[str, dict[str, str]] = {}

    containers = soup.find_all("article")
    if not containers:
        containers = [
            node
            for node in soup.find_all(["div", "section"])
            if any(token in " ".join(node.get("class", [])).lower() for token in ("post", "entry"))
        ]

    for container in containers:
        heading = container.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not heading:
            continue
        title = normalize_text(heading.get_text(" ", strip=True))
        if not is_ordinance_text(title):
            continue
        link = heading.find("a", href=True) or container.find("a", href=True)
        if not link:
            continue
        href = urljoin(listing_url, link["href"])
        path = urlparse(href).path.lower()
        if "/category/" in path:
            continue
        if href.split("#", 1)[0].rstrip("/") == listing_url.split("#", 1)[0].rstrip("/"):
            continue
        entries[href] = {"titulo": title, "href": href, "listing_url": listing_url}

    if not entries:
        for a in soup.find_all("a", href=True):
            title = normalize_text(a.get_text(" ", strip=True))
            if not is_ordinance_text(title):
                continue
            href = urljoin(listing_url, a["href"])
            path = urlparse(href).path.lower()
            if "/category/" in path:
                continue
            if href.startswith(listing_url + "#") or href.rstrip("/") == listing_url.rstrip("/"):
                continue
            entries[href] = {"titulo": title, "href": href, "listing_url": listing_url}
    return list(entries.values())


def content_region(text: str):
    soup = BeautifulSoup(text, "html.parser")
    selectors = ["article .entry-content", ".entry-content", "article", ".post-content", "main"]
    for selector in selectors:
        node = soup.select_one(selector)
        if node is not None:
            return node
    return soup.body or soup


def category_post_candidates(session, pages: list[tuple[str, str]]) -> tuple[list[dict[str, Any]], list[str]]:
    entries: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    for listing_url, text in pages:
        for entry in archive_entries(listing_url, text):
            entries[entry["href"]] = entry

    candidates: list[dict[str, Any]] = []
    for href, meta in entries.items():
        title = meta["titulo"]
        direct = pdf_targets(href, href)
        if direct:
            for target in direct:
                candidates.append({
                    "titulo": title,
                    "numero": ordinance_number(title),
                    "tipo_acto": legal_relation_type(title),
                    "listing_url": meta["listing_url"],
                    "document_url": target,
                    "discovery": "archive_direct_pdf",
                })
            continue
        try:
            text, resolved, _ = fetch_html(session, href)
            region = content_region(text)
            pdfs: list[str] = []
            for a in region.find_all("a", href=True):
                pdfs.extend(pdf_targets(a["href"], resolved))
            for raw in re.findall(r"https?[^\"'<>\s]+", str(region)):
                pdfs.extend(pdf_targets(raw.replace("&amp;", "&"), resolved))
            pdfs = list(dict.fromkeys(pdfs))
            if not pdfs:
                candidates.append({
                    "titulo": title,
                    "numero": ordinance_number(title),
                    "tipo_acto": legal_relation_type(title),
                    "listing_url": meta["listing_url"],
                    "detail_url": resolved,
                    "document_url": None,
                    "discovery": "archive_post_no_pdf",
                })
            else:
                for target in pdfs:
                    candidates.append({
                        "titulo": title,
                        "numero": ordinance_number(title),
                        "tipo_acto": legal_relation_type(title),
                        "listing_url": meta["listing_url"],
                        "detail_url": resolved,
                        "document_url": target,
                        "discovery": "archive_post_pdf",
                    })
        except Exception as exc:
            errors.append(f"detail {href}: {type(exc).__name__}: {exc}")
            candidates.append({
                "titulo": title,
                "numero": ordinance_number(title),
                "tipo_acto": legal_relation_type(title),
                "listing_url": meta["listing_url"],
                "detail_url": href,
                "document_url": None,
                "discovery": "archive_post_error",
            })
    return candidates, errors


def pdf_index_candidates(session, source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract every external URI annotation from an official ordinance-index PDF."""
    errors: list[str] = []
    url = source.get("index_document_url") or source["index_url"]
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        if not response.content.startswith(b"%PDF"):
            return [], ["index_document_not_pdf"]
        reader = PdfReader(BytesIO(response.content))
    except Exception as exc:
        return [], [f"pdf_index_fetch: {type(exc).__name__}: {exc}"]

    links: list[str] = []
    for page in reader.pages:
        for ref in page.get("/Annots", []) or []:
            try:
                annot = ref.get_object()
                action = annot.get("/A")
                uri = action.get("/URI") if action else None
                if uri and str(uri).startswith("http"):
                    links.append(str(uri))
            except Exception as exc:
                errors.append(f"annotation: {type(exc).__name__}: {exc}")
    links = list(dict.fromkeys(links))
    records = [
        {
            "titulo": "Documento enlazado desde índice oficial de ordenanzas",
            "numero": "",
            "tipo_acto": "documento_indice",
            "listing_url": source["index_url"],
            "document_url": link,
            "discovery": "pdf_index_annotation",
        }
        for link in links
    ]
    return records, errors


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
        "source_exhausted": False,
        "coverage_complete": False,
        "errors": [],
        "records": [],
    }

    if strategy in {"wordpress_repository", "wordpress_category"}:
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
            candidates, detail_errors = category_post_candidates(session, pages)
        result["errors"].extend(detail_errors)
    elif strategy == "pdf_index":
        candidates, detail_errors = pdf_index_candidates(session, source)
        result["listing_pages"] = 1 if candidates else 0
        result["listing_exhausted"] = not detail_errors and bool(candidates)
        result["errors"].extend(detail_errors)
    else:
        result["errors"].append(f"strategy_not_exhaustive_yet: {strategy}")
        return result

    dedup: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (
            candidate.get("titulo") or "",
            candidate.get("document_url") or candidate.get("detail_url") or "",
        )
        dedup[key] = candidate

    for candidate in dedup.values():
        document_url = candidate.get("document_url")
        verification = (
            verify_pdf(session, document_url)
            if document_url
            else {"status": "unresolved", "reason": "no_document_url", "verified_at": now_iso()}
        )
        result["records"].append({**candidate, "verification": verification})

    result["candidate_count"] = len(result["records"])
    result["verified_count"] = sum(r["verification"].get("status") == "verified" for r in result["records"])
    result["unresolved_count"] = sum(r["verification"].get("status") != "verified" for r in result["records"])
    result["source_exhausted"] = bool(
        result["listing_exhausted"]
        and not detail_errors
        and result["candidate_count"] > 0
        and result["unresolved_count"] == 0
    )

    # Deliberately fail closed. A repository can be fully crawled while still
    # omitting repealed, migrated or historically archived ordinances. Municipal
    # completeness requires an explicit source-registry decision after cross-source
    # reconciliation; it is never inferred from crawl success alone.
    allowed_to_close = bool(source.get("can_define_complete", False))
    result["coverage_complete"] = bool(
        allowed_to_close
        and result["authoritative_listing"]
        and result["source_exhausted"]
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
        exhausted_sources = sum(bool(a.get("source_exhausted")) for a in source_audits)
        status = "complete" if complete else ("partial" if source_audits else "unregistered")
        municipalities.append({
            "cplt_code": code,
            "organism_name": org.get("organism_name"),
            "status": status,
            "registered_sources": len(source_audits),
            "exhausted_sources": exhausted_sources,
            "verified_records": sum(int(a.get("verified_count") or 0) for a in source_audits),
        })

    counts = {
        "municipalities_total": len(municipalities),
        "communes_total": 346,
        "complete": sum(m["status"] == "complete" for m in municipalities),
        "partial": sum(m["status"] == "partial" for m in municipalities),
        "unregistered": sum(m["status"] == "unregistered" for m in municipalities),
        "sources_exhausted": sum(m["exhausted_sources"] for m in municipalities),
    }
    return {
        "generated_at": now_iso(),
        "definition": (
            "source_exhausted = every candidate discoverable from one registered source was processed; "
            "complete = all relevant official sources for that municipality were reconciled and the registry explicitly permits closure"
        ),
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
            f"unresolved={audit['unresolved_count']} source_exhausted={audit['source_exhausted']} "
            f"complete={audit['coverage_complete']}"
        )

    coverage = national_coverage(load_directory(session), audits)
    payload = {
        "generated_at": now_iso(),
        "policy": (
            "NO SAMPLING: all discoverable ordinances and ordinance-modifying acts from each official source must be enumerated; "
            "exhausting one source never proves municipal completeness by itself"
        ),
        "source_audits": audits,
        "national_coverage": coverage,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("NATIONAL COVERAGE", json.dumps(coverage["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
