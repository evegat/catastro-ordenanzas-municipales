"""Classify extracted municipal PDF evidence with local LM Studio, checkpointed."""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "MW-P090-0014-LM-CLASSIFICATION"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(path: Path, payload: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def ask(base_url: str, model: str, municipality: str, documents: list[dict], timeout: float) -> list[dict]:
    compact = [{"url": d["url"], "label": d.get("label"), "source_page": d.get("source_page")} for d in documents]
    prompt = (
        f"Clasifica documentos oficiales de la Municipalidad de {municipality}. "
        "Decide por el documento específico, no por texto genérico del menú. Es ordenanza sólo si constituye una ordenanza municipal, "
        "su modificación, texto refundido o decreto que la aprueba/modifica. Rechaza concursos, bases, cuentas públicas, estrategias, "
        "actas, contratos, reglamentos internos y documentos que sólo mencionan ordenanzas. No inventes URLs. Devuelve sólo JSON "
        "{\"decisiones\":[{\"url\":...,\"es_ordenanza\":true,\"tipo_acto\":\"ordenanza|modificacion|texto_refundido|acto_relacionado|no_ordenanza\","
        "\"titulo\":...,\"materia_id\":\"otros\",\"confianza\":0.0,\"razon\":...}]}. Entradas:\n" +
        json.dumps(compact, ensure_ascii=False)
    )
    last_error: Exception | None = None
    for _attempt in range(3):
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                json={"model": model, "temperature": 0, "max_tokens": 5000, "messages": [{"role": "user", "content": prompt}]},
                timeout=timeout,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"].get("content", "")
            match = re.search(r"\{.*\}", content, flags=re.S)
            if not match:
                raise ValueError("LM Studio no devolvió JSON")
            parsed = json.loads(match.group())
            return parsed.get("decisiones", [])
        except (requests.RequestException, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(f"LM Studio falló tres veces para {municipality}") from last_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/sinim_validated_extraction.json")
    parser.add_argument("--out", type=Path, default=ROOT / "data/sinim_llm_classification.json")
    parser.add_argument("--base-url", default=os.getenv("P090_LMSTUDIO_URL", "http://127.0.0.1:1234/v1").rstrip("/"))
    parser.add_argument("--model", default=os.getenv("P090_LMSTUDIO_MODEL", "qwen/qwen3.5-9b"))
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    output = {"task_id": TASK_ID, "model": args.model, "policy": "LOCAL LM TRIAGE; human-reviewable; no publication", "municipalities": {}}
    if args.out.exists():
        prior = json.loads(args.out.read_text(encoding="utf-8"))
        if prior.get("task_id") == TASK_ID and prior.get("model") == args.model:
            output = prior
    models = requests.get(f"{args.base_url}/models", timeout=8)
    models.raise_for_status()
    if args.model not in {row.get("id") for row in models.json().get("data", [])}:
        raise AssertionError(f"Modelo no disponible: {args.model}")

    for municipality in source.get("records", []):
        code = municipality["cplt_code"]
        if output["municipalities"].get(code, {}).get("status") == "done":
            continue
        unique = {}
        for source_row in municipality.get("sources", []):
            for document in source_row.get("documents", []):
                verification = document.get("verification") or {}
                if verification.get("status") == "verified_pdf":
                    unique[document["url"]] = document
        decisions = []
        items = list(unique.values())
        prior_row = output["municipalities"].get(code, {})
        if prior_row.get("status") == "in_progress":
            decisions = list(prior_row.get("decisions", []))
        completed_urls = {row.get("url") for row in decisions}
        for offset in range(0, len(items), args.batch_size):
            batch = [item for item in items[offset:offset + args.batch_size] if item["url"] not in completed_urls]
            if not batch:
                continue
            raw = ask(args.base_url, args.model, municipality.get("municipality", code), batch, args.timeout)
            allowed = {item["url"] for item in batch}
            by_url = {str(item.get("url")): item for item in raw if isinstance(item, dict) and str(item.get("url")) in allowed}
            for document in batch:
                decision = by_url.get(document["url"])
                if not decision:
                    decisions.append({"url": document["url"], "status": "pending", "reason": "modelo_no_devolvio_decision"})
                    continue
                confidence = max(0.0, min(1.0, float(decision.get("confianza", 0))))
                decisions.append({
                    "url": document["url"], "sha256": (document.get("verification") or {}).get("sha256"),
                    "is_ordinance": bool(decision.get("es_ordenanza")) and confidence >= 0.8,
                    "model_decision": bool(decision.get("es_ordenanza")), "confidence": confidence,
                    "act_type": decision.get("tipo_acto"), "title": decision.get("titulo"),
                    "matter_id": decision.get("materia_id", "otros"), "reason": decision.get("razon"), "status": "classified",
                })
            output["municipalities"][code] = {
                "municipality": municipality.get("municipality"), "status": "in_progress", "updated_at": now(),
                "documents_seen": len(items), "decisions": decisions,
            }
            output["updated_at"] = now()
            save(args.out, output)
        output["municipalities"][code] = {
            "municipality": municipality.get("municipality"), "status": "done", "updated_at": now(),
            "documents_seen": len(items), "decisions": decisions,
        }
        output["updated_at"] = now()
        save(args.out, output)
        print(f"{code} documents={len(items)} ordinances={sum(bool(d.get('is_ordinance')) for d in decisions)}", flush=True)
    all_decisions = [d for m in output["municipalities"].values() for d in m.get("decisions", [])]
    output["summary"] = {
        "municipalities": len(output["municipalities"]), "documents": len(all_decisions),
        "ordinances": sum(bool(row.get("is_ordinance")) for row in all_decisions),
        "rejected": sum(row.get("status") == "classified" and not row.get("is_ordinance") for row in all_decisions),
        "pending": sum(row.get("status") != "classified" for row in all_decisions),
    }
    save(args.out, output)
    return 0 if output["summary"]["pending"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
