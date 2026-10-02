"""Remediación H02: Admisibilidad Documental (PAD-P090) y Cuarentena.
Segrega planes estratégicos, manuales internos, formularios y contrataciones
a quarantined_records.json con trazabilidad completa.
Task ID: P090-AUD-WEB-20261002
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
MUNICIPAL_FILE = REPO_ROOT / "data" / "municipal_verified_records.json"
QUARANTINE_FILE = REPO_ROOT / "data" / "quarantined_records.json"

INADMISSIBLE_RULES = [
    (r"plan\s+comunal\s+de\s+seguridad", "PAD-P090: Plan Comunal de Seguridad Pública (instrumento de gestión estratégica, no ordenanza)"),
    (r"plan\s+comunal\s+para\s+la\s+rrd", "PAD-P090: Plan Comunal de Gestión del Riesgo de Desastres (instrumento de gestión, no ordenanza)"),
    (r"plan\s+de\s+acci[oó]n\s+comunal\s+de\s+cambio\s+clim[aá]tico", "PAD-P090: Plan de Acción Comunal de Cambio Climático (PACCC - instrumento de política ambiental, no ordenanza)"),
    (r"paccc", "PAD-P090: Plan de Acción Comunal de Cambio Climático (PACCC)"),
    (r"manual\s+de\s+procedimiento", "PAD-P090: Manual de procedimientos administrativos internos"),
    (r"c[aá]maras\s+de\s+seguridad", "PAD-P090: Guía de procedimientos para acceso a grabaciones de cámaras (gestión interna)"),
    (r"trato\s+directo", "PAD-P090: Decreto de contratación pública / trato directo (acto administrativo particular, no ordenanza)"),
    (r"formulario\s+renovacion\s+patentes", "PAD-P090: Formulario de trámite municipal"),
    (r"resumen\s+reporte.*ley\s+de\s+inclusi[oó]n", "PAD-P090: Reporte informativo institucional"),
]

def run_quarantine():
    with open(MUNICIPAL_FILE, "r", encoding="utf-8") as f:
        muni_payload = json.load(f)

    if QUARANTINE_FILE.exists():
        with open(QUARANTINE_FILE, "r", encoding="utf-8") as f:
            quarantine_payload = json.load(f)
    else:
        quarantine_payload = {
            "policy": "PAD-P090: Política de Admisibilidad Documental.",
            "count": 0,
            "records": []
        }

    records = muni_payload.get("records", [])
    kept_records = []
    quarantined_new = []

    now_iso = datetime.now(timezone.utc).isoformat()

    existing_quarantined_targets = {
        q.get("target_url") for q in quarantine_payload.get("records", []) if q.get("target_url")
    }

    for rec in records:
        title = rec.get("titulo", "")
        reason = None
        for pattern, r_desc in INADMISSIBLE_RULES:
            if re.search(pattern, title, re.IGNORECASE):
                reason = r_desc
                break

        if reason:
            rec_q = dict(rec)
            rec_q["motivo_cuarentena"] = reason
            rec_q["quarantine_reason"] = reason
            rec_q["fecha_cuarentena"] = now_iso
            quarantined_new.append(rec_q)
            if rec.get("target_url") not in existing_quarantined_targets:
                quarantine_payload.setdefault("records", []).append(rec_q)
        else:
            kept_records.append(rec)

    # Actualizar payloads
    muni_payload["records"] = kept_records
    muni_payload["count"] = len(kept_records)
    quarantine_payload["count"] = len(quarantine_payload.get("records", []))
    quarantine_payload["last_updated"] = now_iso

    with open(MUNICIPAL_FILE, "w", encoding="utf-8") as f:
        json.dump(muni_payload, f, ensure_ascii=False, indent=2)

    with open(QUARANTINE_FILE, "w", encoding="utf-8") as f:
        json.dump(quarantine_payload, f, ensure_ascii=False, indent=2)

    print(f"H02 Remediación completada:")
    print(f"  - Registros segregados a cuarentena: {len(quarantined_new)}")
    print(f"  - Registros municipales activos restantes: {len(kept_records)}")
    print(f"  - Total registros en cuarentena acumulados: {quarantine_payload['count']}")
    for q in quarantined_new:
        print(f"    * [{q.get('comuna')}] {q.get('titulo')} -> {q.get('motivo_cuarentena')}")

if __name__ == "__main__":
    run_quarantine()
