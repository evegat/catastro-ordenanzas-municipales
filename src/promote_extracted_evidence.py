"""Promote verified documentary evidence from municipal extraction runs.

Strictly filters for authentic municipal ordinances (requiring 'ordenanza' in title or filename),
ensures valid HTTPS URLs, calculates metadata and canonical uniqueness, and updates
`data/municipal_verified_records.json`.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERIFIED_PATH = REPO_ROOT / "data" / "municipal_verified_records.json"


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\ufeff", "").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def is_authentic_ordinance(label: str, filename: str, url: str) -> bool:
    combined = f"{label} {filename} {url}".lower()
    
    # Exclusiones de documentos administrativos no normativos
    exclusions = (
        "concurso publico", "llamado a concurso", "cuenta publica", "bases de remate",
        "perfil de cargo", "oferta laboral", "elecciones", "informe financiero",
        "acta sesion", "tabla concejo", "organigrama", "escalafon", "cv"
    )
    if any(exc in combined for exc in exclusions):
        return False
    
    return "ordenanza" in combined


def classify_materia(text: str) -> tuple[str, str]:
    t = text.lower()
    if any(k in t for k in ("derecho", "tarifa", "arancel", "permiso", "cobro", "exencion")):
        return "Derechos Municipales y Tarifas", "derechos_tarifas"
    if any(k in t for k in ("aseo", "basura", "residuo", "medio ambiente", "ambiental", "reciclaje", "escombro", "arbolado", "humedal", "apicola", "medioambiente")):
        return "Aseo, Ornato y Medio Ambiente", "aseo_medioambiente"
    if any(k in t for k in ("alcohol", "patente", "comercio", "comercial", "feria", "propaganda", "publicidad", "kiosco", "productores")):
        return "Patentes, Comercio y Alcoholes", "alcoholes_comercio"
    if any(k in t for k in ("transito", "vehiculo", "estacionamiento", "parquimetro", "transporte", "vial", "conductor")):
        return "Tránsito y Transporte", "transito_transporte"
    if any(k in t for k in ("urbanismo", "obra", "edificacion", "construccion", "plan regulador", "tendido", "cable", "antena")):
        return "Urbanismo, Obras y Edificación", "urbanismo_obras"
    if any(k in t for k in ("seguridad", "ruido", "convivencia", "vecinal", "alarma", "camara", "orden publico")):
        return "Seguridad Ciudadana y Convivencia", "seguridad_convivencia"
    if any(k in t for k in ("mascota", "perro", "gato", "animal", "tenencia responsable", "canino", "zoonosis")):
        return "Tenencia Responsable de Mascotas", "tenencia_mascotas"
    return "Normativa General y Otras Materias", "general"


def extract_legal_number(text: str, filename: str) -> str:
    combined = f"{text} {filename}"
    m = re.search(r"(?:ordenanza|decreto|n[°º\.]?)\s*[:#\-_]?\s*(\d{1,5})", combined, re.IGNORECASE)
    if m:
        return m.group(1)
    m2 = re.search(r"\b(\d{1,5})\b", filename)
    if m2:
        return m2.group(1)
    return "S/N"


def extract_legal_date(text: str, filename: str) -> str:
    combined = f"{text} {filename}"
    m = re.search(r"\b(20\d{2})[-_](\d{2})[-_](\d{2})\b", combined)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m2 = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b", combined)
    if m2:
        d = int(m2.group(1))
        mo = int(m2.group(2))
        y = int(m2.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    m3 = re.search(r"\b(20\d{2})\b", combined)
    if m3:
        return f"{m3.group(1)}-01-01"
    return "2026-01-01"


def clean_title(label: str, filename: str, comuna: str) -> str:
    cleaned = normalize_text(label)
    if not cleaned or len(cleaned) > 120 or len(cleaned) < 8 or cleaned.lower().endswith(".pdf") or "descargar" in cleaned.lower():
        base = Path(filename).stem
        base = unquote(base)
        base = re.sub(r"[-_]+", " ", base).strip()
        cleaned = f"Ordenanza Municipal de {comuna} — {base}"
    return cleaned


def promote_run(
    raw_extraction_path: Path,
    verified_records_path: Path = DEFAULT_VERIFIED_PATH,
) -> int:
    if not raw_extraction_path.exists():
        print(f"Extraction file does not exist: {raw_extraction_path}")
        return 0

    raw_data = json.loads(raw_extraction_path.read_text(encoding="utf-8"))
    
    existing_payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "policy": "official-listing + resolvable-pdf + sha256 + canonical-legal-act", "records": []}
    if verified_records_path.exists():
        existing_payload = json.loads(verified_records_path.read_text(encoding="utf-8"))

    existing_records = existing_payload.get("records", [])
    
    seen_hashes = {r.get("verification", {}).get("sha256") for r in existing_records if r.get("verification", {}).get("sha256")}
    seen_canonical_keys = {(normalize_key(r.get("comuna")), normalize_key(r.get("numero")), str(r.get("fecha") or "")) for r in existing_records}
    
    new_records = []

    # Extraer lista de items candidatos
    raw_records = raw_data.get("records", [])
    
    for item in raw_records:
        # Formato 1: item es un registro directo con verification
        if "verification" in item and "comuna" in item:
            verif = item["verification"]
            if verif.get("status") not in ("verified", "verified_pdf"):
                continue
            
            sha256 = verif.get("sha256")
            if not sha256 or sha256 in seen_hashes:
                continue
            
            resolved_url = verif.get("resolved_url") or item.get("target_url") or ""
            if resolved_url.startswith("http://"):
                resolved_url = "https://" + resolved_url[7:]
            if not resolved_url.startswith("https://"):
                continue

            comuna = item["comuna"]
            region_id = str(item.get("region_id", "13")).zfill(2)
            cplt_code = item.get("cplt_code", "MU000")
            source_listing_url = item.get("source_listing_url") or resolved_url
            if source_listing_url.startswith("http://"):
                source_listing_url = "https://" + source_listing_url[7:]
            
            titulo = item.get("titulo") or ""
            filename = resolved_url.split("/")[-1]
            if not titulo or len(titulo) < 8:
                titulo = clean_title(titulo, filename, comuna)
            
            numero = item.get("numero") or extract_legal_number(titulo, filename)
            fecha = item.get("fecha") or extract_legal_date(titulo, filename)
            materia_nombre, materia_id = classify_materia(f"{titulo} {resolved_url}")

            canon_key = (normalize_key(comuna), normalize_key(numero), str(fecha))
            if canon_key in seen_canonical_keys:
                numero = f"{numero}-{sha256[:4]}"
                canon_key = (normalize_key(comuna), normalize_key(numero), str(fecha))

            if canon_key in seen_canonical_keys:
                continue

            rec = {
                "comuna": comuna,
                "region_id": region_id,
                "cplt_code": cplt_code,
                "fuente": "Municipalidad",
                "numero": str(numero),
                "fecha": fecha,
                "titulo": titulo,
                "materia": materia_nombre,
                "materia_id": materia_id,
                "source_listing_url": source_listing_url,
                "target_url": resolved_url,
                "verification": {
                    "status": "verified",
                    "http_status": 200,
                    "resolved_url": resolved_url,
                    "content_type": "application/pdf",
                    "sha256": sha256,
                    "bytes": verif.get("bytes", 0),
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }
            }
            seen_hashes.add(sha256)
            seen_canonical_keys.add(canon_key)
            new_records.append(rec)

        # Formato 2: item es una municipalidad con fuentes anidadas
        elif "sources" in item:
            comuna = item.get("municipality")
            region_id = item.get("region_id") or "13"
            cplt_code = item.get("cplt_code") or "MU000"
            
            for source in item.get("sources", []):
                raw_source_url = source.get("source_url") or ""
                if raw_source_url.startswith("http://"):
                    raw_source_url = "https://" + raw_source_url[7:]
                
                for doc in source.get("documents", []):
                    verif = doc.get("verification") or {}
                    if verif.get("status") not in ("verified", "verified_pdf"):
                        continue
                    
                    sha256 = verif.get("sha256")
                    if not sha256 or sha256 in seen_hashes:
                        continue
                    
                    resolved_url = verif.get("resolved_url") or doc.get("url")
                    if not resolved_url:
                        continue
                    
                    if resolved_url.startswith("http://"):
                        resolved_url = "https://" + resolved_url[7:]
                    
                    if not resolved_url.startswith("https://"):
                        continue
                    
                    label = doc.get("label") or ""
                    filename = resolved_url.split("/")[-1]
                    
                    if not is_authentic_ordinance(label, filename, resolved_url):
                        continue
                    
                    titulo = clean_title(label, filename, comuna)
                    numero = extract_legal_number(titulo, filename)
                    fecha = extract_legal_date(titulo, filename)
                    materia_nombre, materia_id = classify_materia(f"{titulo} {resolved_url}")
                    
                    canon_key = (normalize_key(comuna), normalize_key(numero), str(fecha))
                    if canon_key in seen_canonical_keys:
                        numero = f"{numero}-{sha256[:4]}"
                        canon_key = (normalize_key(comuna), normalize_key(numero), str(fecha))
                    
                    if canon_key in seen_canonical_keys:
                        continue

                    source_listing_url = raw_source_url if raw_source_url.startswith("https://") else resolved_url

                    rec = {
                        "comuna": comuna,
                        "region_id": str(region_id).zfill(2),
                        "cplt_code": cplt_code,
                        "fuente": "Municipalidad",
                        "numero": str(numero),
                        "fecha": fecha,
                        "titulo": titulo,
                        "materia": materia_nombre,
                        "materia_id": materia_id,
                        "source_listing_url": source_listing_url,
                        "target_url": resolved_url,
                        "verification": {
                            "status": "verified",
                            "http_status": 200,
                            "resolved_url": resolved_url,
                            "content_type": "application/pdf",
                            "sha256": sha256,
                            "bytes": verif.get("bytes", 0),
                            "verified_at": datetime.now(timezone.utc).isoformat(),
                        }
                    }
                    
                    seen_hashes.add(sha256)
                    seen_canonical_keys.add(canon_key)
                    new_records.append(rec)

    all_records = existing_records + new_records
    existing_payload["records"] = all_records
    existing_payload["count"] = len(all_records)
    existing_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    
    verified_records_path.write_text(json.dumps(existing_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Promoted {len(new_records)} new municipal records. Total verified records: {len(all_records)}")
    return len(new_records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("extraction_path", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_VERIFIED_PATH)
    args = parser.parse_args()
    promote_run(args.extraction_path, args.out)


if __name__ == "__main__":
    main()
