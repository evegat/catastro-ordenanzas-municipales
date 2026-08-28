"""Recover municipal ordinances from verifiable official sources.

Historical ``ALL_CPLT_RECORDS`` are not trusted. The CPLT directory is used only
for organism identity/publication mode. Municipal records are promoted only
when an official document URL resolves and the bytes are verified as PDF and
hashed with SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import unicodedata
from dataclasses import dataclass
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
USER_AGENT = "P090-Ordenanzas-Recovery/1.1 (+https://github.com/evegat/catastro-ordenanzas-municipales)"
TIMEOUT = 30
MAX_DOCUMENT_BYTES = 40 * 1024 * 1024


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\ufeff", "").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def ascii_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", normalize_text(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def parse_year(value: str) -> int | None:
    m = re.search(r"\b(20\d{2})\b", value or "")
    return int(m.group(1)) if m else None


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    })
    return s


@dataclass
class Link:
    href: str
    text: str = ""


@dataclass
class Cell:
    text: str
    links: list[Link]


class TableParser(HTMLParser):
    """Tolerant table parser preserving links in each cell."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[Cell]] = []
        self.row: list[Cell] | None = None
        self.cell_text: list[str] | None = None
        self.cell_links: list[Link] | None = None
        self.anchor_href: str | None = None
        self.anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag.lower() == "tr":
            if self.row:
                self.rows.append(self.row)
            self.row = []
        elif tag.lower() in {"td", "th"}:
            if self.row is None:
                self.row = []
            self.cell_text, self.cell_links = [], []
        elif tag.lower() == "a" and self.cell_text is not None:
            self.anchor_href = attrs_d.get("href") or ""
            self.anchor_text = []
        elif tag.lower() == "img" and self.anchor_href is not None:
            alt = attrs_d.get("alt") or attrs_d.get("title") or ""
            if alt:
                self.anchor_text.append(alt)

    def handle_data(self, data: str) -> None:
        if self.cell_text is not None:
            self.cell_text.append(data)
        if self.anchor_href is not None:
            self.anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self.anchor_href is not None and self.cell_links is not None:
            self.cell_links.append(Link(self.anchor_href, normalize_text(" ".join(self.anchor_text))))
            self.anchor_href, self.anchor_text = None, []
        elif tag in {"td", "th"} and self.cell_text is not None:
            if self.row is None:
                self.row = []
            self.row.append(Cell(normalize_text(" ".join(self.cell_text)), list(self.cell_links or [])))
            self.cell_text, self.cell_links = None, None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

    def close(self) -> None:
        super().close()
        if self.row:
            self.rows.append(self.row)
            self.row = None


def fetch_html(session: requests.Session, url: str) -> tuple[str, str, int]:
    r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding or "utf-8"
    return r.text, r.url, r.status_code


def rows_from_html(text: str) -> list[list[Cell]]:
    parser = TableParser()
    parser.feed(text)
    parser.close()
    return parser.rows


def code_from_cell(value: str) -> str | None:
    m = re.search(r"(?<![A-Z0-9])(MU\d{3})(?!\d)", normalize_text(value), flags=re.I)
    return m.group(1).upper() if m else None


def strip_tags(fragment: str) -> str:
    return normalize_text(html_lib.unescape(re.sub(r"<[^>]+>", " ", fragment)))


def parse_cplt_flat_fallback(text: str, base_url: str) -> list[dict[str, Any]]:
    """Fallback for old/Excel-generated malformed HTML where table events fail."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for m in re.finditer(r"MU\d{3}", text, flags=re.I):
        code = m.group(0).upper()
        if code in seen:
            continue
        start = text.rfind("<tr", max(0, m.start() - 3000), m.start())
        end = text.find("</tr", m.end(), min(len(text), m.end() + 8000))
        if start < 0 or end < 0:
            start, end = max(0, m.start() - 300), min(len(text), m.end() + 2500)
        else:
            end = text.find(">", end) + 1
        chunk = text[start:end]
        plain = strip_tags(chunk)
        pos = plain.upper().find(code)
        after = plain[pos + len(code):].strip(" |:-") if pos >= 0 else plain
        name = re.split(r"Enlace\s+banner|No\s+usa\s+Portal|No\s+publica\s+en\s+Portal", after, maxsplit=1, flags=re.I)[0]
        name = normalize_text(name).strip(" |:-")
        hrefs = [urljoin(base_url, html_lib.unescape(h)) for h in re.findall(r'href=["\']([^"\']+)', chunk, flags=re.I)]
        ta_status = "not_in_portal" if re.search(r"No\s+publica\s+en\s+Portal", plain, flags=re.I) else ("portal" if len(hrefs) >= 2 else "unknown")
        out.append({
            "cplt_code": code,
            "organism_name": name or f"Municipalidad {code}",
            "municipality_key": ascii_key(re.sub(r"^(I\.?\s*)?Municipalidad de\s+", "", name, flags=re.I)),
            "ta_status": ta_status,
            "ta_link": hrefs[-1] if ta_status == "portal" and hrefs else None,
            "sai_link": hrefs[0] if hrefs else None,
            "directory_url": CPLT_DIRECTORY_URL,
        })
        seen.add(code)
    return out


def parse_cplt_directory(text: str, base_url: str = CPLT_DIRECTORY_URL) -> list[dict[str, Any]]:
    organisms: list[dict[str, Any]] = []
    seen: set[str] = set()
    rows = rows_from_html(text)
    for row in rows:
        if not row:
            continue
        code = next((code_from_cell(c.text) for c in row if code_from_cell(c.text)), None)
        if not code or code in seen:
            continue
        code_index = next((i for i, c in enumerate(row) if code_from_cell(c.text) == code), 0)
        name = row[code_index + 1].text if code_index + 1 < len(row) else ""
        row_text = " | ".join(c.text for c in row)
        all_links = [urljoin(base_url, link.href) for c in row for link in c.links if link.href]
        ta_status = "not_in_portal" if re.search(r"No\s+publica\s+en\s+Portal", row_text, flags=re.I) else ("portal" if len(all_links) >= 2 else "unknown")
        organisms.append({
            "cplt_code": code,
            "organism_name": normalize_text(name),
            "municipality_key": ascii_key(re.sub(r"^(I\.?\s*)?Municipalidad de\s+", "", name, flags=re.I)),
            "ta_status": ta_status,
            "ta_link": all_links[-1] if ta_status == "portal" and all_links else None,
            "sai_link": all_links[0] if all_links else None,
            "directory_url": CPLT_DIRECTORY_URL,
        })
        seen.add(code)
    if len(organisms) < 300:
        fallback = parse_cplt_flat_fallback(text, base_url)
        by_code = {x["cplt_code"]: x for x in organisms}
        for item in fallback:
            by_code.setdefault(item["cplt_code"], item)
        organisms = list(by_code.values())
    return organisms


def load_directory(session: requests.Session) -> list[dict[str, Any]]:
    text, final_url, _ = fetch_html(session, CPLT_DIRECTORY_URL)
    organisms = parse_cplt_directory(text, final_url)
    raw_mu = len(set(re.findall(r"MU\d{3}", text, flags=re.I)))
    if len(organisms) < 300:
        raise RuntimeError(f"CPLT directory parse unexpectedly small: parsed={len(organisms)}, raw_MU_codes={raw_mu}, bytes={len(text.encode('utf-8', errors='ignore'))}")
    return organisms


def portal_probe_urls(code: str, official_ta_link: str | None) -> list[str]:
    urls = []
    if official_ta_link:
        urls.append(official_ta_link)
    urls += [
        f"https://www.portaltransparencia.cl/PortalPdT/pdtta?codOrganismo={code}",
        f"https://www.portaltransparencia.cl/PortalPdT/pdtta/-/ta/{code}/PDO/AD",
    ]
    return list(dict.fromkeys(urls))


def probe_url(session: requests.Session, url: str) -> dict[str, Any]:
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
        return {"requested_url": url, "status_code": r.status_code, "resolved_url": r.url,
                "content_type": (r.headers.get("content-type") or "").split(";", 1)[0].lower(),
                "ok": r.status_code < 400}
    except requests.RequestException as exc:
        return {"requested_url": url, "status_code": None, "resolved_url": None,
                "content_type": None, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def verify_pdf(session: requests.Session, url: str) -> dict[str, Any]:
    try:
        with session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True) as r:
            ct = (r.headers.get("content-type") or "").split(";", 1)[0].lower()
            if r.status_code >= 400:
                return {"status": "rejected", "http_status": r.status_code, "resolved_url": r.url, "content_type": ct, "reason": "http_error"}
            digest, total, first = hashlib.sha256(), 0, b""
            for chunk in r.iter_content(65536):
                if not chunk:
                    continue
                if not first:
                    first = chunk[:8]
                total += len(chunk)
                if total > MAX_DOCUMENT_BYTES:
                    return {"status": "rejected", "http_status": r.status_code, "resolved_url": r.url, "content_type": ct, "reason": "document_too_large", "bytes_seen": total}
                digest.update(chunk)
            if not (ct == "application/pdf" or first.startswith(b"%PDF")):
                return {"status": "rejected", "http_status": r.status_code, "resolved_url": r.url, "content_type": ct, "reason": "not_pdf", "bytes": total}
            return {"status": "verified", "http_status": r.status_code, "resolved_url": r.url,
                    "content_type": ct or "application/pdf", "sha256": digest.hexdigest(),
                    "bytes": total, "verified_at": now_iso()}
    except requests.RequestException as exc:
        return {"status": "rejected", "http_status": None, "resolved_url": None, "content_type": None,
                "reason": "request_error", "error": f"{type(exc).__name__}: {exc}"}


def cell(row: list[Cell], idx: int | None) -> Cell:
    return row[idx] if idx is not None and 0 <= idx < len(row) else Cell("", [])


def document_links(row: list[Cell], idx: int | None, base_url: str) -> list[str]:
    preferred = cell(row, idx).links
    links = preferred or [link for c in row for link in c.links]
    out = []
    for link in links:
        if not link.href or link.href.startswith(("javascript:", "mailto:", "#")):
            continue
        url = urljoin(base_url, link.href)
        host, path, label = urlparse(url).netloc.lower(), urlparse(url).path.lower(), ascii_key(link.text)
        if path.endswith(".pdf") or "pdf" in label or host.startswith("firma.providencia.cl"):
            out.append(url)
    return list(dict.fromkeys(out))


def canonical_verified(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "comuna": record["municipality"], "region_id": record.get("region_id"),
        "cplt_code": record.get("cplt_code"), "fuente": "Municipalidad",
        "numero": record.get("numero") or "", "fecha": record.get("fecha") or "",
        "titulo": record.get("titulo") or "", "source_listing_url": record["source_listing_url"],
        "target_url": record["verification"].get("resolved_url") or record.get("document_url"),
        "verification": record["verification"],
    }


def recover_seed(session: requests.Session, source: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    verification = verify_pdf(session, seed["document_url"])
    return {
        "municipality": source["municipality"], "region_id": source.get("region_id"),
        "cplt_code": source.get("cplt_code"), "source_type": source.get("source_type", "municipal_transparency"),
        "source_listing_url": source["index_url"], "year": seed.get("year") or parse_year(seed.get("fecha", "")),
        "numero": seed.get("numero", ""), "fecha": seed.get("fecha", ""), "titulo": seed.get("titulo", ""),
        "document_url": seed["document_url"], "verification": verification, "evidence_mode": "official_listing_seed",
    }


def recover_source(session: requests.Session, source: dict[str, Any], directory: dict[str, dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"source_id": source["id"], "municipality": source["municipality"],
        "cplt_code": source.get("cplt_code"), "index_url": source["index_url"], "fetched_at": now_iso(),
        "records": [], "errors": []}
    if source.get("cplt_code") in directory:
        result["cplt_directory"] = directory[source["cplt_code"]]

    try:
        text, resolved, status = fetch_html(session, source["index_url"])
        result.update({"index_http_status": status, "resolved_index_url": resolved})
        rows = rows_from_html(text)
        cmap, required = source.get("column_map", {}), ascii_key(source.get("required_term", "ordenanza"))
        start_year, end_year = int(source.get("start_year", 2022)), int(source.get("end_year", 2026))
        for row in rows:
            raw = " | ".join(c.text for c in row)
            if required and required not in ascii_key(raw):
                continue
            year = parse_year(cell(row, cmap.get("year")).text or raw)
            if year is None or not (start_year <= year <= end_year):
                continue
            links = document_links(row, cmap.get("document"), resolved)
            record = {"municipality": source["municipality"], "region_id": source.get("region_id"),
                "cplt_code": source.get("cplt_code"), "source_type": source.get("source_type", "municipal_transparency"),
                "source_listing_url": resolved, "year": year, "numero": cell(row, cmap.get("number")).text,
                "fecha": cell(row, cmap.get("date")).text,
                "titulo": cell(row, cmap.get("title")).text or cell(row, cmap.get("description")).text,
                "raw_row": raw, "candidate_document_urls": links,
                "verification": {"status": "no_document_link", "verified_at": now_iso()}}
            for url in links:
                v = verify_pdf(session, url)
                if v["status"] == "verified":
                    record.update({"document_url": url, "verification": v})
                    break
                record.setdefault("rejected_document_urls", []).append({"url": url, **v})
            result["records"].append(record)
    except Exception as exc:
        result["errors"].append(f"index_fetch_or_parse: {type(exc).__name__}: {exc}")

    existing_keys = {(r.get("numero"), r.get("document_url")) for r in result["records"]}
    for seed in source.get("verified_seeds", []):
        key = (seed.get("numero", ""), seed.get("document_url"))
        if key not in existing_keys:
            result["records"].append(recover_seed(session, source, seed))

    result["candidate_count"] = len(result["records"])
    result["verified_count"] = sum(1 for r in result["records"] if r.get("verification", {}).get("status") == "verified")
    return result


def cmd_directory(args: argparse.Namespace) -> int:
    organisms = load_directory(make_session())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"source": CPLT_DIRECTORY_URL, "generated_at": now_iso(), "count": len(organisms), "municipalities": organisms}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CPLT directory OK: {len(organisms)} municipality codes; {sum(x['ta_status']=='portal' for x in organisms)} publish TA in Portal")
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    s, organisms = make_session(), load_directory(make_session())
    if args.codes:
        organisms = [x for x in organisms if x["cplt_code"] in set(args.codes)]
    elif args.limit:
        organisms = organisms[:args.limit]
    results = []
    for org in organisms:
        probes = [probe_url(s, u) for u in portal_probe_urls(org["cplt_code"], org["ta_link"])]
        results.append({**org, "probes": probes})
        print(f"{org['cplt_code']} {org['organism_name']}: {sum(p['ok'] for p in probes)}/{len(probes)} reachable")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"generated_at": now_iso(), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def cmd_recover(args: argparse.Namespace) -> int:
    s = make_session()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    directory = {x["cplt_code"]: x for x in load_directory(s)}
    reports, verified = [], []
    for source in registry.get("sources", []):
        report = recover_source(s, source, directory)
        reports.append(report)
        for record in report["records"]:
            if record.get("verification", {}).get("status") == "verified":
                verified.append(canonical_verified(record))
        print(f"{source['id']}: {report['candidate_count']} candidates, {report['verified_count']} verified PDFs")
    dedup = {}
    for record in verified:
        dedup[(record["comuna"], record["numero"], record["target_url"])] = record
    verified = list(dedup.values())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.verified_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"generated_at": now_iso(), "sources": reports}, ensure_ascii=False, indent=2), encoding="utf-8")
    args.verified_out.write_text(json.dumps({"generated_at": now_iso(), "policy": "official-listing + resolvable-pdf + sha256", "count": len(verified), "records": verified}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"RECOVERY VERIFIED TOTAL: {len(verified)}")
    if args.print_verified:
        print(json.dumps(verified, ensure_ascii=False, indent=2))
    if args.require_verified and not verified:
        raise SystemExit("No verified municipal PDF recovered")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("directory"); d.add_argument("--out", type=Path, default=DEFAULT_DIRECTORY_OUT); d.set_defaults(func=cmd_directory)
    q = sub.add_parser("probe"); q.add_argument("--out", type=Path, default=Path("data/cplt_portal_probe.json")); q.add_argument("--limit", type=int, default=0); q.add_argument("--codes", nargs="*"); q.set_defaults(func=cmd_probe)
    r = sub.add_parser("recover"); r.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY); r.add_argument("--out", type=Path, default=DEFAULT_RECOVERY_OUT); r.add_argument("--verified-out", type=Path, default=DEFAULT_VERIFIED_OUT); r.add_argument("--print-verified", action="store_true"); r.add_argument("--require-verified", action="store_true"); r.set_defaults(func=cmd_recover)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
