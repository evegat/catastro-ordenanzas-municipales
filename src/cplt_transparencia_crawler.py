"""Recover municipal ordinances from verifiable official sources.

This module intentionally does NOT trust the historical ``ALL_CPLT_RECORDS``
manual list. It uses the Consejo para la Transparencia (CPLT) official
organism directory only to identify municipalities and their Portal de
Transparencia publication mode, then crawls configured official municipal
source tables and promotes a document only when the linked file is actually
resolvable as a PDF.

The output is evidence, not a direct mutation of the public dashboard. A
separate promotion step may import only records whose ``verification.status``
is ``verified``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


CPLT_DIRECTORY_URL = (
    "https://www.consejotransparencia.cl/transparencia_activa/"
    "datoabierto/archivos/lista_enlaces_banner_sai.html"
)
DEFAULT_REGISTRY = Path("data/municipal_source_registry.json")
DEFAULT_DIRECTORY_OUT = Path("data/cplt_municipal_directory.json")
DEFAULT_RECOVERY_OUT = Path("data/municipal_recovery_report.json")
DEFAULT_VERIFIED_OUT = Path("data/municipal_verified_records.json")
USER_AGENT = "P090-Ordenanzas-Recovery/1.0 (+https://github.com/evegat/catastro-ordenanzas-municipales)"
TIMEOUT = 30
MAX_DOCUMENT_BYTES = 40 * 1024 * 1024


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", value).strip()


def ascii_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", normalize_text(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def parse_year(value: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", value or "")
    return int(match.group(1)) if match else None


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        }
    )
    return session


@dataclass
class Link:
    href: str
    text: str = ""


@dataclass
class Cell:
    text: str
    links: list[Link]


class TableParser(HTMLParser):
    """Small dependency-free HTML table parser preserving links per cell."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[Cell]] = []
        self._row: list[Cell] | None = None
        self._cell_text: list[str] | None = None
        self._cell_links: list[Link] | None = None
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell_text = []
            self._cell_links = []
        elif tag == "a" and self._cell_text is not None:
            self._anchor_href = attrs_dict.get("href") or ""
            self._anchor_text = []
        elif tag == "img" and self._anchor_href is not None:
            alt = attrs_dict.get("alt") or attrs_dict.get("title") or ""
            if alt:
                self._anchor_text.append(alt)

    def handle_data(self, data: str) -> None:
        if self._cell_text is not None:
            self._cell_text.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor_href is not None and self._cell_links is not None:
            self._cell_links.append(
                Link(href=self._anchor_href, text=normalize_text(" ".join(self._anchor_text)))
            )
            self._anchor_href = None
            self._anchor_text = []
        elif tag in {"td", "th"} and self._row is not None and self._cell_text is not None:
            self._row.append(
                Cell(
                    text=normalize_text(" ".join(self._cell_text)),
                    links=list(self._cell_links or []),
                )
            )
            self._cell_text = None
            self._cell_links = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def fetch_html(session: requests.Session, url: str) -> tuple[str, str, int]:
    response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    return response.text, response.url, response.status_code


def parse_cplt_directory(html: str, base_url: str = CPLT_DIRECTORY_URL) -> list[dict[str, Any]]:
    parser = TableParser()
    parser.feed(html)
    organisms: list[dict[str, Any]] = []

    for row in parser.rows:
        if len(row) < 2:
            continue
        code = normalize_text(row[0].text)
        if not re.fullmatch(r"MU\d{3}", code):
            continue
        name = normalize_text(row[1].text)
        row_text = " | ".join(cell.text for cell in row)
        ta_cell = row[-1] if len(row) >= 4 else Cell("", [])
        sai_cell = row[-2] if len(row) >= 3 else Cell("", [])

        ta_link = next((urljoin(base_url, link.href) for link in ta_cell.links if link.href), None)
        sai_link = next((urljoin(base_url, link.href) for link in sai_cell.links if link.href), None)
        ta_status = "portal" if ta_link else "not_in_portal"
        if "No publica en Portal Transparencia" not in row_text and ta_link is None:
            ta_status = "unknown"

        organisms.append(
            {
                "cplt_code": code,
                "organism_name": name,
                "municipality_key": ascii_key(re.sub(r"^(I\.?\s*)?Municipalidad de\s+", "", name, flags=re.I)),
                "ta_status": ta_status,
                "ta_link": ta_link,
                "sai_link": sai_link,
                "directory_url": CPLT_DIRECTORY_URL,
            }
        )

    return organisms


def load_directory(session: requests.Session) -> list[dict[str, Any]]:
    html, final_url, _ = fetch_html(session, CPLT_DIRECTORY_URL)
    organisms = parse_cplt_directory(html, final_url)
    if len(organisms) < 300:
        raise RuntimeError(f"CPLT directory parse unexpectedly small: {len(organisms)} municipalities")
    return organisms


def portal_probe_urls(code: str, official_ta_link: str | None) -> list[str]:
    candidates = []
    if official_ta_link:
        candidates.append(official_ta_link)
    candidates.extend(
        [
            f"https://www.portaltransparencia.cl/PortalPdT/pdtta?codOrganismo={code}",
            f"https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/{code}/PDO/AD",
        ]
    )
    seen: set[str] = set()
    return [url for url in candidates if not (url in seen or seen.add(url))]


def probe_url(session: requests.Session, url: str) -> dict[str, Any]:
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
        return {
            "requested_url": url,
            "status_code": response.status_code,
            "resolved_url": response.url,
            "content_type": (response.headers.get("content-type") or "").split(";", 1)[0].lower(),
            "ok": response.status_code < 400,
        }
    except requests.RequestException as exc:
        return {
            "requested_url": url,
            "status_code": None,
            "resolved_url": None,
            "content_type": None,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def verify_pdf(session: requests.Session, url: str) -> dict[str, Any]:
    try:
        with session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True) as response:
            status = response.status_code
            content_type = (response.headers.get("content-type") or "").split(";", 1)[0].lower()
            if status >= 400:
                return {
                    "status": "rejected",
                    "http_status": status,
                    "resolved_url": response.url,
                    "content_type": content_type,
                    "reason": "http_error",
                }

            digest = hashlib.sha256()
            total = 0
            first = b""
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                if not first:
                    first = chunk[:8]
                total += len(chunk)
                if total > MAX_DOCUMENT_BYTES:
                    return {
                        "status": "rejected",
                        "http_status": status,
                        "resolved_url": response.url,
                        "content_type": content_type,
                        "reason": "document_too_large",
                        "bytes_seen": total,
                    }
                digest.update(chunk)

            is_pdf = content_type == "application/pdf" or first.startswith(b"%PDF")
            if not is_pdf:
                return {
                    "status": "rejected",
                    "http_status": status,
                    "resolved_url": response.url,
                    "content_type": content_type,
                    "reason": "not_pdf",
                    "bytes": total,
                }

            return {
                "status": "verified",
                "http_status": status,
                "resolved_url": response.url,
                "content_type": content_type or "application/pdf",
                "sha256": digest.hexdigest(),
                "bytes": total,
                "verified_at": now_iso(),
            }
    except requests.RequestException as exc:
        return {
            "status": "rejected",
            "http_status": None,
            "resolved_url": None,
            "content_type": None,
            "reason": "request_error",
            "error": f"{type(exc).__name__}: {exc}",
        }


def source_cell(row: list[Cell], index: int | None) -> Cell:
    if index is None or index < 0 or index >= len(row):
        return Cell("", [])
    return row[index]


def cell_text(row: list[Cell], index: int | None) -> str:
    return source_cell(row, index).text


def document_links(row: list[Cell], document_cell_index: int | None, base_url: str) -> list[str]:
    preferred = source_cell(row, document_cell_index).links
    links = preferred or [link for cell in row for link in cell.links]
    results: list[str] = []
    for link in links:
        if not link.href or link.href.startswith(("javascript:", "mailto:", "#")):
            continue
        absolute = urljoin(base_url, link.href)
        host = urlparse(absolute).netloc.lower()
        text = ascii_key(link.text)
        path = urlparse(absolute).path.lower()
        if path.endswith(".pdf") or "pdf" in text or host.startswith("firma.providencia.cl"):
            results.append(absolute)
    return list(dict.fromkeys(results))


def parse_source_rows(html: str) -> list[list[Cell]]:
    parser = TableParser()
    parser.feed(html)
    return parser.rows


def recover_source(
    session: requests.Session,
    source: dict[str, Any],
    directory_by_code: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    index_url = source["index_url"]
    result: dict[str, Any] = {
        "source_id": source["id"],
        "municipality": source["municipality"],
        "cplt_code": source.get("cplt_code"),
        "index_url": index_url,
        "fetched_at": now_iso(),
        "records": [],
        "errors": [],
    }
    directory_entry = directory_by_code.get(source.get("cplt_code", ""))
    if directory_entry:
        result["cplt_directory"] = directory_entry

    try:
        html, resolved_index_url, status = fetch_html(session, index_url)
        result["index_http_status"] = status
        result["resolved_index_url"] = resolved_index_url
    except Exception as exc:  # keep other sources recoverable
        result["errors"].append(f"index_fetch: {type(exc).__name__}: {exc}")
        return result

    rows = parse_source_rows(html)
    cmap = source.get("column_map", {})
    start_year = int(source.get("start_year", 2022))
    end_year = int(source.get("end_year", datetime.now().year))
    required_term = ascii_key(source.get("required_term", "ordenanza"))

    for row in rows:
        row_text = " | ".join(cell.text for cell in row)
        row_key = ascii_key(row_text)
        if required_term and required_term not in row_key:
            continue

        year_text = cell_text(row, cmap.get("year")) or row_text
        year = parse_year(year_text)
        if year is None or not (start_year <= year <= end_year):
            continue

        links = document_links(row, cmap.get("document"), resolved_index_url)
        record = {
            "municipality": source["municipality"],
            "region_id": source.get("region_id"),
            "cplt_code": source.get("cplt_code"),
            "source_type": source.get("source_type", "municipal_transparency"),
            "source_listing_url": resolved_index_url,
            "year": year,
            "numero": cell_text(row, cmap.get("number")),
            "fecha": cell_text(row, cmap.get("date")),
            "titulo": cell_text(row, cmap.get("title")) or cell_text(row, cmap.get("description")),
            "raw_row": row_text,
            "candidate_document_urls": links,
            "verification": {"status": "no_document_link", "verified_at": now_iso()},
        }

        for link in links:
            verification = verify_pdf(session, link)
            if verification["status"] == "verified":
                record["document_url"] = link
                record["verification"] = verification
                break
            record.setdefault("rejected_document_urls", []).append({"url": link, **verification})

        result["records"].append(record)

    result["verified_count"] = sum(
        1 for record in result["records"] if record["verification"]["status"] == "verified"
    )
    result["candidate_count"] = len(result["records"])
    return result


def verified_public_record(record: dict[str, Any]) -> dict[str, Any]:
    """Narrow canonical shape used by the later promotion step."""
    return {
        "comuna": record["municipality"],
        "region_id": record.get("region_id"),
        "cplt_code": record.get("cplt_code"),
        "fuente": "Municipalidad",
        "numero": record.get("numero") or "",
        "fecha": record.get("fecha") or "",
        "titulo": record.get("titulo") or "",
        "source_listing_url": record["source_listing_url"],
        "target_url": record["verification"].get("resolved_url") or record.get("document_url"),
        "verification": record["verification"],
    }


def command_directory(args: argparse.Namespace) -> int:
    session = make_session()
    organisms = load_directory(session)
    payload = {
        "source": CPLT_DIRECTORY_URL,
        "generated_at": now_iso(),
        "count": len(organisms),
        "municipalities": organisms,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    portal_count = sum(1 for item in organisms if item["ta_status"] == "portal")
    print(f"CPLT directory OK: {len(organisms)} municipalities; {portal_count} publish TA in Portal")
    return 0


def command_probe(args: argparse.Namespace) -> int:
    session = make_session()
    organisms = load_directory(session)
    wanted = set(args.codes or [])
    if wanted:
        organisms = [item for item in organisms if item["cplt_code"] in wanted]
    elif args.limit:
        organisms = organisms[: args.limit]

    report = []
    for organism in organisms:
        probes = [probe_url(session, url) for url in portal_probe_urls(organism["cplt_code"], organism["ta_link"])]
        report.append({**organism, "probes": probes})
        ok = [probe for probe in probes if probe["ok"]]
        print(f"{organism['cplt_code']} {organism['organism_name']}: {len(ok)}/{len(probes)} portal URLs reachable")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"generated_at": now_iso(), "results": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def command_recover(args: argparse.Namespace) -> int:
    session = make_session()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    organisms = load_directory(session)
    directory_by_code = {item["cplt_code"]: item for item in organisms}

    reports = []
    verified: list[dict[str, Any]] = []
    for source in registry.get("sources", []):
        report = recover_source(session, source, directory_by_code)
        reports.append(report)
        for record in report.get("records", []):
            if record.get("verification", {}).get("status") == "verified":
                verified.append(verified_public_record(record))
        print(
            f"{source['id']}: {report.get('candidate_count', 0)} candidates, "
            f"{report.get('verified_count', 0)} verified PDFs"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.verified_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"generated_at": now_iso(), "sources": reports}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.verified_out.write_text(
        json.dumps(
            {
                "generated_at": now_iso(),
                "policy": "official-source + resolvable-pdf + sha256",
                "count": len(verified),
                "records": verified,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"RECOVERY VERIFIED TOTAL: {len(verified)}")
    if args.print_verified:
        print(json.dumps(verified, ensure_ascii=False, indent=2))
    if args.require_verified and not verified:
        raise SystemExit("No verified municipal PDF recovered")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    directory = sub.add_parser("directory", help="Download and normalize the official CPLT municipality directory")
    directory.add_argument("--out", type=Path, default=DEFAULT_DIRECTORY_OUT)
    directory.set_defaults(func=command_directory)

    probe = sub.add_parser("probe", help="Probe current/legacy Portal de Transparencia URLs")
    probe.add_argument("--out", type=Path, default=Path("data/cplt_portal_probe.json"))
    probe.add_argument("--limit", type=int, default=0)
    probe.add_argument("--codes", nargs="*")
    probe.set_defaults(func=command_probe)

    recover = sub.add_parser("recover", help="Recover verified PDFs from configured official municipal sources")
    recover.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    recover.add_argument("--out", type=Path, default=DEFAULT_RECOVERY_OUT)
    recover.add_argument("--verified-out", type=Path, default=DEFAULT_VERIFIED_OUT)
    recover.add_argument("--print-verified", action="store_true")
    recover.add_argument("--require-verified", action="store_true")
    recover.set_defaults(func=command_recover)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
