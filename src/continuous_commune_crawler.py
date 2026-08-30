"""Crawler local reanudable de candidatos municipales (MW-P090-0014).

Usa la API OpenAI-compatible de LM Studio. Descubre candidatos y los deja en
cuarentena: nunca modifica el corpus verificado, el dashboard ni la cobertura.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from cplt_transparencia_crawler import ascii_key
from national_municipal_discovery import verify_municipal_identity

TASK_ID = "MW-P090-0014"
ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/crawler_state.json"
OUTPUT = ROOT / "data/local_crawler_candidates.json"
LOG = ROOT / "logs/continuous_crawler.log"
MASTER = ROOT / "data/maestro_comunas_chile.csv"
STATUS = ROOT / "dashboard/status_data.json"
DIRECTORY = ROOT / "data/cplt_municipal_directory.json"
PATHS = (
    "/ordenanzas", "/ordenanzas-municipales", "/transparencia/ordenanzas",
    "/transparencia-activa/ordenanzas", "/normativa-municipal", "/reglamentos",
    "/actos-y-resoluciones-con-efectos-sobre-terceros",
)
# Denominaciones institucionales CPLT que difieren del nombre territorial del
# maestro. El código oficial evita emparejamientos difusos o ambiguos.
CPLT_NAME_OVERRIDES = {
    "MU017": "Cabo de Hornos", "MU064": "Constitución",
    "MU114": "Isla de Pascua", "MU116": "Calera", "MU143": "Llaillay",
    "MU165": "Marchihue", "MU187": "O'Higgins", "MU188": "Olivar",
    "MU195": "Paiguano", "MU234": "Natales", "MU303": "San Vicente",
    "MU328": "Treguaco",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def available_models(base_url: str) -> set[str]:
    response = requests.get(f"{base_url}/models", timeout=5)
    response.raise_for_status()
    return {str(item.get("id")) for item in response.json().get("data", [])}


def ask_model(base_url: str, model: str, commune: str, links: list[dict], timeout: float) -> list[dict]:
    prompt = (
        f"Clasifica documentos del portal oficial de la Municipalidad de {commune}. "
        "No inventes datos ni URLs. Incluye sólo ordenanzas, modificaciones o textos refundidos; "
        "excluye actas, contratos, concursos, bases y resoluciones no normativas. Devuelve sólo JSON "
        "con forma {\"candidatos\":[{\"url\":...,\"titulo\":...,\"numero\":null,"
        "\"fecha\":null,\"materia_id\":\"otros\",\"tipo_acto\":\"ordenanza\"}]}. "
        "Usa exclusivamente estas entradas:\n" + json.dumps(links, ensure_ascii=False)
    )
    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": model, "temperature": 0, "max_tokens": 3000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"].get("content", "").strip()
    if not content:
        raise ValueError("LM Studio devolvió contenido vacío")
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        raise ValueError("LM Studio no devolvió un objeto JSON")
    parsed = json.loads(match.group())
    return parsed.get("candidatos", []) if isinstance(parsed, dict) else []


def fetch_html(session: requests.Session, url: str, timeout: float):
    response = session.get(url, timeout=timeout, allow_redirects=True)
    if response.status_code == 200 and "html" in response.headers.get("Content-Type", "").lower():
        return response.text, response.url
    return None


def pdf_links(html: str, base_url: str) -> list[dict]:
    pattern = r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    found = {}
    for href, label in re.findall(pattern, html, flags=re.I | re.S):
        url = urljoin(base_url, href.strip())
        if urlparse(url).scheme in {"http", "https"} and ".pdf" in url.lower():
            found[url] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", label)).strip()
    return [{"url": url, "label": label} for url, label in sorted(found.items())]


def queue() -> list[dict]:
    with MASTER.open(encoding="utf-8") as handle:
        master_rows = list(csv.DictReader(handle))
    master_by_key = {ascii_key(row["comuna_nombre"]): row for row in master_rows}
    directory = load(DIRECTORY, {})
    municipalities = directory.get("municipalities", [])
    if directory.get("count") != 345 or len(municipalities) != 345:
        raise AssertionError("El directorio CPLT no acredita el universo oficial de 345 municipalidades")
    output = []
    unmatched = []
    for item in municipalities:
        canonical_name = CPLT_NAME_OVERRIDES.get(item["cplt_code"])
        key = ascii_key(canonical_name or item.get("municipality_key") or "")
        master = master_by_key.get(key)
        if not master:
            unmatched.append(item.get("cplt_code"))
            continue
        output.append({
            "cplt_code": item["cplt_code"], "comuna": master["comuna_nombre"],
            "region": master["region_nombre"], "region_id": master["region_id"],
            "seed_url": master.get("web_municipal", ""), "ta_url": item.get("ta_link"),
            "directory_url": item.get("directory_url"),
        })
    if unmatched or len(output) != 345:
        raise AssertionError(f"No se reconciliaron 345/345 municipalidades CPLT: {unmatched}")
    return output


def process(session: requests.Session, row: dict, args) -> tuple[str, dict]:
    try:
        root = fetch_html(session, row["seed_url"], args.http_timeout)
    except requests.RequestException:
        root = None
    discovered = {}
    source_attempts = []
    identity = {"verified": False, "reason": "seed_unreachable"}
    if root:
        root_html, resolved_seed = root
        identity = verify_municipal_identity(root_html, resolved_seed, row["comuna"])
    else:
        resolved_seed = row["seed_url"]

    municipal_urls = []
    if identity.get("verified"):
        municipal_urls = [urljoin(resolved_seed.rstrip("/") + "/", path.lstrip("/")) for path in PATHS]
    for url in municipal_urls:
        try:
            page = fetch_html(session, url, args.http_timeout)
        except requests.RequestException:
            page = None
        source_attempts.append({"url": url, "reachable": bool(page), "kind": "municipal"})
        if page:
            html, resolved = page
            for link in pdf_links(html, resolved):
                link["source_listing_url"] = resolved
                discovered[link["url"]] = link
        time.sleep(args.rate_limit)

    ta_url = row.get("ta_url")
    if ta_url:
        try:
            ta_page = fetch_html(session, ta_url, args.http_timeout)
        except requests.RequestException:
            ta_page = None
        source_attempts.append({"url": ta_url, "reachable": bool(ta_page), "kind": "cplt"})
        if ta_page:
            html, resolved = ta_page
            for link in pdf_links(html, resolved):
                link["source_listing_url"] = resolved
                discovered[link["url"]] = link
        time.sleep(args.rate_limit)
    if not discovered:
        reason = "no_pdf_candidates" if root or ta_url else "no_source_reachable"
        status = "review" if root or any(item["reachable"] for item in source_attempts) else "retry"
        return status, {"reason": reason, "identity": identity, "source_attempts": source_attempts}

    raw = ask_model(args.base_url, args.model, row["comuna"], list(discovered.values()), args.llm_timeout)
    candidates = []
    for item in raw:
        url = str(item.get("url") or "").strip() if isinstance(item, dict) else ""
        if url not in discovered:
            continue
        candidates.append({
            "url": url, "source_listing_url": discovered[url]["source_listing_url"],
            "titulo": str(item.get("titulo") or "").strip(), "numero": item.get("numero"),
            "fecha": item.get("fecha"), "materia_id": str(item.get("materia_id") or "otros"),
            "tipo_acto": str(item.get("tipo_acto") or "acto_relacionado"),
        })
    return "done", {
        "identity": identity, "source_attempts": source_attempts,
        "pdf_links_found": len(discovered), "candidates": candidates,
    }


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("P090_LMSTUDIO_URL", "http://127.0.0.1:1234/v1").rstrip("/"))
    parser.add_argument("--model", default=os.getenv("P090_LMSTUDIO_MODEL", "qwen/qwen3.5-9b"))
    parser.add_argument("--max", type=int, default=0)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--rate-limit", type=float, default=2.5)
    parser.add_argument("--http-timeout", type=float, default=20)
    parser.add_argument("--llm-timeout", type=float, default=300)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler()])
    try:
        models = available_models(args.base_url)
    except requests.RequestException as exc:
        logging.error("LM Studio no disponible en %s: %s", args.base_url, exc)
        return 2
    if args.model not in models:
        logging.error("Modelo '%s' no expuesto por LM Studio. Disponibles: %s", args.model, ", ".join(sorted(models)))
        return 2

    old = load(STATE, {})
    state = old if old.get("task_id") == TASK_ID else {"task_id": TASK_ID, "municipalities": {}}
    output = load(OUTPUT, {"task_id": TASK_ID, "policy": "QUARANTINE ONLY; coverage_complete=false", "records": []})
    all_rows = queue()
    fresh = []
    retries = []
    for row in all_rows:
        previous = state["municipalities"].get(row["comuna"], {})
        status = previous.get("status")
        if status in {"done", "review"}:
            continue
        if status == "retry":
            if args.retry_failed:
                retries.append(row)
        else:
            fresh.append(row)
    eligible = fresh + retries
    if args.max:
        eligible = eligible[:args.max]
    logging.info("%s | modelo=%s | cola=%d de %d municipalidades CPLT", TASK_ID, args.model, len(eligible), len(all_rows))
    if args.dry_run:
        return 0
    if not eligible:
        state["automatic_queue_complete"] = True
        state["completed_at"] = now()
        state["updated_at"] = now()
        save(STATE, state)
        logging.info("Cola recorrida: no quedan comunas automáticas pendientes.")
        return 3
    state["automatic_queue_complete"] = False

    session = requests.Session()
    session.headers["User-Agent"] = "P090CatastroBot/3.0 (investigacion academica; evegat@uchile.cl)"
    known = {(item.get("comuna"), item.get("url")) for item in output["records"]}
    for index, row in enumerate(eligible, 1):
        logging.info("[%d/%d] %s", index, len(eligible), row["comuna"])
        try:
            status, detail = process(session, row, args)
        except (requests.RequestException, json.JSONDecodeError, ValueError) as exc:
            status, detail = "retry", {"reason": type(exc).__name__, "message": str(exc)[:300]}
        except Exception as exc:
            logging.exception("Falla inesperada")
            status, detail = "retry", {"reason": type(exc).__name__, "message": str(exc)[:300]}
        prior_attempts = int(state["municipalities"].get(row["comuna"], {}).get("attempts", 0))
        attempts = prior_attempts + 1
        if status == "retry" and attempts >= 3:
            status = "review"
            detail["retry_limit_reached"] = True
        state["municipalities"][row["comuna"]] = {
            "status": status, "attempts": attempts, "updated_at": now(),
            "coverage_complete": False, "detail": detail,
        }
        for candidate in detail.get("candidates", []):
            key = (row["comuna"], candidate["url"])
            if key not in known:
                output["records"].append({**row, **candidate, "discovered_at": now(), "review_status": "pending"})
                known.add(key)
        state["updated_at"] = output["updated_at"] = now()
        output["count"] = len(output["records"])
        save(STATE, state)
        save(OUTPUT, output)
        time.sleep(args.rate_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
