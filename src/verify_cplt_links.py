"""Verifica las URLs históricas de los registros CPLT/municipales de P090.

Este script NO certifica vigencia normativa. Solo comprueba accesibilidad HTTP y
si la URL parece apuntar directamente a un documento o a una página/portal.

Uso:
    python src/verify_cplt_links.py
    python src/verify_cplt_links.py --output data/cplt_link_status.csv
    python src/verify_cplt_links.py --strict
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests

from ingest_cplt_records import ALL_CPLT_RECORDS

DEFAULT_OUTPUT = Path("data/cplt_link_status.csv")
DEFAULT_SUMMARY = Path("data/cplt_link_status_summary.json")
USER_AGENT = "P090-CPLT-LinkVerifier/1.0 (+https://github.com/evegat/catastro-ordenanzas-municipales)"
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods", ".zip"}


@dataclass
class LinkResult:
    comuna: str
    numero: str
    fecha: str
    source_url: str
    final_url: str
    http_status: int | None
    status: str
    resource_type: str
    content_type: str
    redirected: bool
    error: str


def _looks_like_document(url: str, content_type: str) -> bool:
    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in DOCUMENT_EXTENSIONS):
        return True
    ctype = (content_type or "").lower()
    return any(
        token in ctype
        for token in (
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats",
            "application/vnd.ms-excel",
            "application/zip",
        )
    )


def verify_one(record: dict, session: requests.Session, timeout: float) -> LinkResult:
    url = (record.get("url") or "").strip()
    if not url:
        return LinkResult(
            comuna=record.get("comuna", ""),
            numero=record.get("numero", ""),
            fecha=record.get("fecha", ""),
            source_url="",
            final_url="",
            http_status=None,
            status="missing_url",
            resource_type="unknown",
            content_type="",
            redirected=False,
            error="URL vacía",
        )

    try:
        response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
        final_url = response.url or url
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        redirected = final_url.rstrip("/") != url.rstrip("/")
        is_document = _looks_like_document(final_url, content_type)
        resource_type = "document" if is_document else "page_or_portal"

        if 200 <= response.status_code < 300:
            status = "ok_document" if is_document else "ok_page_or_portal"
        elif 300 <= response.status_code < 400:
            status = "redirect"
        elif response.status_code == 404:
            status = "broken_404"
        else:
            status = f"http_{response.status_code}"

        response.close()
        return LinkResult(
            comuna=record.get("comuna", ""),
            numero=record.get("numero", ""),
            fecha=record.get("fecha", ""),
            source_url=url,
            final_url=final_url,
            http_status=response.status_code,
            status=status,
            resource_type=resource_type,
            content_type=content_type,
            redirected=redirected,
            error="",
        )
    except requests.Timeout as exc:
        return LinkResult(
            comuna=record.get("comuna", ""),
            numero=record.get("numero", ""),
            fecha=record.get("fecha", ""),
            source_url=url,
            final_url="",
            http_status=None,
            status="timeout",
            resource_type="unknown",
            content_type="",
            redirected=False,
            error=str(exc),
        )
    except requests.RequestException as exc:
        return LinkResult(
            comuna=record.get("comuna", ""),
            numero=record.get("numero", ""),
            fecha=record.get("fecha", ""),
            source_url=url,
            final_url="",
            http_status=None,
            status="request_error",
            resource_type="unknown",
            content_type="",
            redirected=False,
            error=str(exc),
        )


def verify_all(records: Iterable[dict], timeout: float = 12.0) -> list[LinkResult]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    return [verify_one(record, session, timeout) for record in records]


def write_csv(results: list[LinkResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(results[0]).keys()) if results else list(LinkResult.__annotations__.keys())
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def build_summary(results: list[LinkResult]) -> dict:
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
        type_counts[result.resource_type] = type_counts.get(result.resource_type, 0) + 1

    return {
        "total": len(results),
        "status_counts": dict(sorted(status_counts.items())),
        "resource_type_counts": dict(sorted(type_counts.items())),
        "verified_direct_documents": sum(1 for result in results if result.status == "ok_document"),
        "not_directly_verified": sum(1 for result in results if result.status != "ok_document"),
        "note": "Accesibilidad HTTP no equivale a vigencia ni autenticidad normativa.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica las URLs históricas CPLT/municipales de P090")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV de resultados")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY, help="JSON resumen")
    parser.add_argument("--timeout", type=float, default=12.0, help="Timeout por URL en segundos")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Retorna código 1 si existe algún registro que no sea un documento directo HTTP 2xx",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = verify_all(ALL_CPLT_RECORDS, timeout=args.timeout)
    write_csv(results, args.output)

    summary = build_summary(results)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.strict and summary["not_directly_verified"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
