"""Audit Canasta Basica de 5 Ordenanzas Obligatorias por Ley.

Audita determinísticamente las 7.450 ordenanzas en dashboard/status_data.json
evaluando el cumplimiento de las 5 ordenanzas obligatorias por ley en las 346 comunas
de Chile (con desglose específico para el universo nacional y la cohorte activa de 243 comunas).

Materias auditadas:
1. Derechos Municipales y Tarifas (DL 3.063 / Rentas Municipales).
2. Aseo, Gestión de Residuos y Protección Ambiental (Ley 18.695 / Ley 20.920 REP).
3. Seguridad, Convivencia y Ruidos Molestos (DS 38 MMA / Ley 18.695).
4. Tenencia Responsable de Mascotas y Animales de Compañía (Ley 21.020 / 'Ley Cholito').
5. Participación Ciudadana (Ley 20.500 / Ley 18.695 art. 93).
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
STATUS_DATA_PATH = REPO_ROOT / "dashboard" / "status_data.json"
AUDIT_128_PATH = REPO_ROOT / "data" / "auditoria_128_comunas.json"
OUTPUT_METRICS_PATH = REPO_ROOT / "dashboard" / "canasta_basica_metrics.json"

MACROZONAS = {
    "Norte Grande": [15, 1, 2],
    "Norte Chico": [3, 4],
    "Centro": [5, 13, 6, 7],
    "Sur": [16, 8, 9, 14, 10],
    "Austral": [11, 12]
}

def get_macrozona(region_id: int | str) -> str:
    try:
        rid = int(region_id)
    except (ValueError, TypeError):
        return "Desconocida"
    for mz, rids in MACROZONAS.items():
        if rid in rids:
            return mz
    return "Desconocida"

def norm(text: str | None) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8")
    return t.lower().strip()

PATTERNS = {
    "1_derechos": {
        "id": "derechos_tarifas",
        "name": "Derechos Municipales y Tarifas",
        "legal_base": "DL 3.063 de Rentas Municipales (arts. 41 y 42)",
        "law_name": "DL 3.063",
        "regex": re.compile(
            r"\b(derecho|derechos|tarifa|tarifas|arancel|aranceles|rentas?\s*municipales|"
            r"concesiones,?\s*permisos\s*y\s*servicios|cobro\s*de\s*derechos|derechos\s*municipales|"
            r"derecho\s*de\s*aseo|exencion\s*de\s*derechos|pagos?\s*de\s*derechos)\b"
        ),
        "mats": {"derechos_tarifas", "derechos_municipales"}
    },
    "2_aseo_ambiente": {
        "id": "aseo_residuos_ambiente",
        "name": "Aseo, Gestión de Residuos y Protección Ambiental",
        "legal_base": "Ley 18.695 (art. 3f) / Ley 20.920 REP",
        "law_name": "Ley 18.695 / Ley REP",
        "regex": re.compile(
            r"\b(aseo|ornato|residuos?|basuras?|medio\s*ambiente|ambiental|vertederos?|escombros?|"
            r"reciclaje|recoleccion|desechos?|limpieza|microbasurales?|areas?\s*verdes?|arbolado|"
            r"humedales?|bolsas?\s*plasticas?|sustentabilidad|sustentable|cambio\s*climatico|biodiversidad)\b"
        ),
        "mats": {"aseo_medioambiente", "aseo_residuos", "medio_ambiente"}
    },
    "3_seguridad_ruidos": {
        "id": "seguridad_convivencia_ruidos",
        "name": "Seguridad, Convivencia y Ruidos Molestos",
        "legal_base": "DS 38 MMA / Ley 18.695 (arts. 4h y 4j)",
        "law_name": "DS 38 MMA / Ley 18.695",
        "regex": re.compile(
            r"\b(ruidos?|sonidos?\s*molestos?|contaminacion\s*acustica|acustica|fuentes\s*sonoras|"
            r"seguridad|convivencia|tranquilidad|orden\s*publico|incivilidades?|acoso\s*callejero|"
            r"cierre\s*de\s*calles?|cierre\s*de\s*pasajes?|camaras|televigilancia|rayados?|graffitis?|"
            r"vigilancia|guardias|seguridad\s*ciudadana|seguridad\s*publica|alcohol\s*en\s*la\s*via\s*publica)\b"
        ),
        "mats": {"seguridad_convivencia", "convivencia_seguridad", "convivencia_ruidos"}
    },
    "4_mascotas": {
        "id": "mascotas_tenencia_responsable",
        "name": "Tenencia Responsable de Mascotas y Animales de Compañía",
        "legal_base": "Ley 21.020 (Ley Cholito, art. 7)",
        "law_name": "Ley 21.020",
        "regex": re.compile(
            r"\b(mascotas?|animales?\s*de\s*compania|tenencia\s*responsable|canino|canina|perros?|"
            r"felinos?|gatos?|zoosanitari[ao]|bienestar\s*animal|proteccion\s*animal|veterinari[ao]|"
            r"ley\s*cholito|control\s*canino|mordeduras?|fauna\s*urbana|palomas|plagas)\b"
        ),
        "mats": {"mascotas_animales", "tenencia_mascotas", "mascotas", "tenencia_responsable_mascotas"}
    },
    "5_participacion": {
        "id": "participacion_ciudadana",
        "name": "Participación Ciudadana",
        "legal_base": "Ley 20.500 / Ley 18.695 (art. 93)",
        "law_name": "Ley 20.500",
        "regex": re.compile(
            r"\b(participacion\s*ciudadana|participacion\s*(?:de\s*la\s*)?comunidad|participacion\s*vecinal|"
            r"cosoc\b|consejo\s*comunal\s*de\s*la\s*sociedad\s*civil|consejo\s*economico\s*y\s*social|"
            r"cesco\b|plebiscitos?|consultas?\s*ciudadanas?|audiencias?\s*publicas?|"
            r"cabildos?\s*(?:comunales?|ciudadanos?)|presupuestos?\s*participativos?|organizaciones\s*comunitarias)\b"
        ),
        "mats": {"participacion_ciudadana"}
    }
}

def classify_ord(ord_item: dict) -> set[str]:
    t = norm(ord_item.get("titulo", ""))
    m = norm(ord_item.get("materia", ""))
    mid = ord_item.get("materia_id", "")
    
    matches = set()
    for cat_key, cat_data in PATTERNS.items():
        if cat_data["regex"].search(t):
            matches.add(cat_key)
        elif mid in cat_data["mats"]:
            # Filtro defensivo contra falsos positivos en materia_id
            if cat_key == "3_seguridad_ruidos" and ("denominacion de poblaciones" in t or "cambio de nombre" in t):
                pass
            else:
                matches.add(cat_key)
        elif cat_data["regex"].search(m):
            matches.add(cat_key)
    return matches

def run_audit():
    print(f"[*] Leyendo base consolidada: {STATUS_DATA_PATH}")
    with open(STATUS_DATA_PATH, "r", encoding="utf-8") as f:
        master_data = json.load(f)
        
    comunas_data = master_data.get("comunas", [])
    print(f"[OK] Cargadas {len(comunas_data)} comunas con {sum(len(c.get('ordenanzas', [])) for c in comunas_data)} ordenanzas.")

    # Cargar auditoria 128 comunas para desglosar la cohorte activa (243 comunas)
    rescued_set = set()
    missing_unrescued_set = set()
    if AUDIT_128_PATH.exists():
        with open(AUDIT_128_PATH, "r", encoding="utf-8") as f:
            audit_128 = json.load(f)
        for item in audit_128:
            com = item.get("comuna")
            st = item.get("estado")
            if st == "RESCATADA":
                rescued_set.add(com)
            else:
                missing_unrescued_set.add(com)
    print(f"[OK] Cohorte de 128 faltantes: {len(rescued_set)} rescatadas, {len(missing_unrescued_set)} no rescatadas.")

    # Analizar cada comuna
    communes_audit = {}
    materia_stats = {k: {"total_ords": 0, "comunas_historico": set(), "comunas_reciente": set(), "recent_ords": 0} for k in PATTERNS}

    for c in comunas_data:
        c_name = c.get("comuna")
        rid = c.get("region_id")
        r_name = c.get("region_nombre") or c.get("region")
        macrozona = get_macrozona(rid)
        ords = c.get("ordenanzas", [])
        
        # Histórico vs Reciente (2021-2026)
        cats_historico = set()
        cats_reciente = set()
        ord_by_cat = defaultdict(list)
        recent_ords_by_cat = defaultdict(list)
        all_recent_ords = []
        
        for o in ords:
            f = str(o.get("fecha") or "")
            is_recent = False
            if len(f) >= 4 and f[:4].isdigit() and 2021 <= int(f[:4]) <= 2026:
                is_recent = True
                all_recent_ords.append(o)
                
            matched = classify_ord(o)
            for m in matched:
                cats_historico.add(m)
                ord_by_cat[m].append({
                    "titulo": o.get("titulo"),
                    "fecha": o.get("fecha"),
                    "numero": o.get("numero"),
                    "materia": o.get("materia"),
                    "url": o.get("target_url") or o.get("source_listing_url")
                })
                materia_stats[m]["total_ords"] += 1
                materia_stats[m]["comunas_historico"].add(c_name)
                
                if is_recent:
                    cats_reciente.add(m)
                    recent_ords_by_cat[m].append(o)
                    materia_stats[m]["recent_ords"] += 1
                    materia_stats[m]["comunas_reciente"].add(c_name)

        # Flag cohorte activa 243
        # Cohorte 243 = Las comunas que NO estan en missing_unrescued_set
        is_in_active_cohort = (c_name not in missing_unrescued_set)
        has_recent_strict = len(all_recent_ords) > 0

        communes_audit[c_name] = {
            "comuna": c_name,
            "region_id": rid,
            "region_nombre": r_name,
            "macrozona": macrozona,
            "is_in_active_cohort": is_in_active_cohort,
            "has_recent_strict": has_recent_strict,
            "total_ordenanzas": len(ords),
            "total_ordenanzas_recientes": len(all_recent_ords),
            "score_historico": len(cats_historico),
            "score_reciente": len(cats_reciente),
            "categorias_historico": sorted(list(cats_historico)),
            "categorias_reciente": sorted(list(cats_reciente)),
            "detalle_por_materia": {
                k: {
                    "cumple_historico": k in cats_historico,
                    "cumple_reciente": k in cats_reciente,
                    "total_normas": len(ord_by_cat[k]),
                    "norma_reciente_ejemplo": ord_by_cat[k][0] if ord_by_cat[k] else None
                }
                for k in PATTERNS
            }
        }

    # Distribuciones
    dist_all_hist = Counter(c["score_historico"] for c in communes_audit.values())
    dist_all_rec = Counter(c["score_reciente"] for c in communes_audit.values())

    active_cohort = [c for c in communes_audit.values() if c["is_in_active_cohort"]]
    dist_active_hist = Counter(c["score_historico"] for c in active_cohort)
    dist_active_rec = Counter(c["score_reciente"] for c in active_cohort)

    strict_cohort = [c for c in communes_audit.values() if c["has_recent_strict"]]
    dist_strict_hist = Counter(c["score_historico"] for c in strict_cohort)
    dist_strict_rec = Counter(c["score_reciente"] for c in strict_cohort)

    # Macrozonal aggregation
    macro_stats = defaultdict(lambda: {
        "comunas": 0,
        "active_comunas": 0,
        "score_hist_sum": 0,
        "score_rec_sum": 0,
        "score_dist_hist": Counter(),
        "score_dist_rec": Counter(),
        "materias_hist": Counter(),
        "materias_rec": Counter()
    })

    for c in communes_audit.values():
        mz = c["macrozona"]
        macro_stats[mz]["comunas"] += 1
        if c["is_in_active_cohort"]:
            macro_stats[mz]["active_comunas"] += 1
        macro_stats[mz]["score_hist_sum"] += c["score_historico"]
        macro_stats[mz]["score_rec_sum"] += c["score_reciente"]
        macro_stats[mz]["score_dist_hist"][c["score_historico"]] += 1
        macro_stats[mz]["score_dist_rec"][c["score_reciente"]] += 1
        for cat in c["categorias_historico"]:
            macro_stats[mz]["materias_hist"][cat] += 1
        for cat in c["categorias_reciente"]:
            macro_stats[mz]["materias_rec"][cat] += 1

    # Regional aggregation
    region_stats = defaultdict(lambda: {
        "region_id": None,
        "region_nombre": "",
        "macrozona": "",
        "comunas": 0,
        "active_comunas": 0,
        "score_hist_avg": 0.0,
        "score_dist_hist": Counter(),
        "materias_hist": Counter()
    })

    for c in communes_audit.values():
        rid = c["region_id"]
        rname = c["region_nombre"]
        region_stats[rid]["region_id"] = rid
        region_stats[rid]["region_nombre"] = rname
        region_stats[rid]["macrozona"] = c["macrozona"]
        region_stats[rid]["comunas"] += 1
        if c["is_in_active_cohort"]:
            region_stats[rid]["active_comunas"] += 1
        region_stats[rid]["score_dist_hist"][c["score_historico"]] += 1
        for cat in c["categorias_historico"]:
            region_stats[rid]["materias_hist"][cat] += 1

    for rid, st in region_stats.items():
        total_pts = sum(s * cnt for s, cnt in st["score_dist_hist"].items())
        st["score_hist_avg"] = round(total_pts / st["comunas"], 2) if st["comunas"] else 0.0

    # Comunas destacadas (5/5)
    destacadas_5_5 = [c for c in communes_audit.values() if c["score_historico"] == 5]
    destacadas_5_5.sort(key=lambda x: (x["score_reciente"], x["total_ordenanzas_recientes"], x["total_ordenanzas"]), reverse=True)

    # Comunas críticas (0/5 y 1/5)
    criticas_0_5 = [c for c in communes_audit.values() if c["score_historico"] == 0]
    criticas_1_5 = [c for c in communes_audit.values() if c["score_historico"] == 1]

    # Preparamos JSON para el Dashboard
    metrics_export = {
        "metadata": {
            "generado_el": datetime.now().isoformat(),
            "universo_total_comunas": 346,
            "cohorte_activa_comunas": len(active_cohort),
            "cohorte_estricta_quinquenio": len(strict_cohort),
            "total_ordenanzas_auditadas": sum(c["total_ordenanzas"] for c in communes_audit.values())
        },
        "distribucion_nacional_346": {
            f"score_{s}": {
                "comunas": dist_all_hist[s],
                "porcentaje": round(dist_all_hist[s] / 346 * 100, 2)
            }
            for s in range(5, -1, -1)
        },
        "distribucion_cohorte_activa_243": {
            f"score_{s}": {
                "comunas": dist_active_hist[s],
                "porcentaje": round(dist_active_hist[s] / len(active_cohort) * 100, 2)
            }
            for s in range(5, -1, -1)
        },
        "distribucion_vigencia_reciente_2021_2026": {
            f"score_{s}": {
                "comunas": dist_all_rec[s],
                "porcentaje": round(dist_all_rec[s] / 346 * 100, 2)
            }
            for s in range(5, -1, -1)
        },
        "ranking_materias": [
            {
                "codigo": k,
                "nombre": PATTERNS[k]["name"],
                "base_legal": PATTERNS[k]["legal_base"],
                "ley": PATTERNS[k]["law_name"],
                "total_ordenanzas": materia_stats[k]["total_ords"],
                "comunas_historico": len(materia_stats[k]["comunas_historico"]),
                "cobertura_nacional_pct": round(len(materia_stats[k]["comunas_historico"]) / 346 * 100, 2),
                "comunas_reciente": len(materia_stats[k]["comunas_reciente"]),
                "cobertura_reciente_pct": round(len(materia_stats[k]["comunas_reciente"]) / 346 * 100, 2)
            }
            for k in sorted(PATTERNS.keys(), key=lambda x: len(materia_stats[x]["comunas_historico"]), reverse=True)
        ],
        "macrozonas": {
            mz: {
                "total_comunas": data["comunas"],
                "comunas_activas": data["active_comunas"],
                "promedio_score_historico": round(data["score_hist_sum"] / data["comunas"], 2) if data["comunas"] else 0,
                "distribucion_scores": {f"score_{s}": data["score_dist_hist"][s] for s in range(5, -1, -1)},
                "cobertura_materias": {PATTERNS[k]["name"]: data["materias_hist"][k] for k in PATTERNS}
            }
            for mz, data in macro_stats.items()
        },
        "regiones": [
            {
                "region_id": st["region_id"],
                "region_nombre": st["region_nombre"],
                "macrozona": st["macrozona"],
                "total_comunas": st["comunas"],
                "promedio_score": st["score_hist_avg"],
                "comunas_5_de_5": st["score_dist_hist"][5],
                "comunas_0_o_1_de_5": st["score_dist_hist"][0] + st["score_dist_hist"][1],
                "cobertura_materias": {PATTERNS[k]["name"]: st["materias_hist"][k] for k in PATTERNS}
            }
            for rid, st in sorted(region_stats.items(), key=lambda x: x[1]["score_hist_avg"], reverse=True)
        ],
        "comunas_destacadas_5_de_5": [
            {
                "comuna": c["comuna"],
                "region": c["region_nombre"],
                "macrozona": c["macrozona"],
                "score_historico": c["score_historico"],
                "score_reciente": c["score_reciente"],
                "total_ordenanzas": c["total_ordenanzas"],
                "total_ordenanzas_recientes": c["total_ordenanzas_recientes"]
            }
            for c in destacadas_5_5
        ],
        "comunas_alertas_rezago": {
            "cero_de_cinco": [c["comuna"] for c in criticas_0_5],
            "uno_de_cinco_total": len(criticas_1_5),
            "muestra_uno_de_cinco": [c["comuna"] for c in criticas_1_5[:15]]
        },
        "comunas_detalle": {
            c["comuna"]: {
                "region": c["region_nombre"],
                "macrozona": c["macrozona"],
                "score_historico": c["score_historico"],
                "score_reciente": c["score_reciente"],
                "is_in_active_cohort": c["is_in_active_cohort"],
                "categorias_historico": c["categorias_historico"],
                "categorias_reciente": c["categorias_reciente"]
            }
            for c in communes_audit.values()
        }
    }

    OUTPUT_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_export, f, indent=2, ensure_ascii=False)
    print(f"[OK] Metricas exportadas exitosamente a {OUTPUT_METRICS_PATH}")

    # Imprimir resumen de consola
    print("\n=======================================================")
    print("      RESUMEN EJECUTIVO DE AUDITORIA DE CANASTA BASICA")
    print("=======================================================")
    print(f"Total Comunas Nacionales: 346 | Cohorte Activa: {len(active_cohort)}")
    print("\n--- DISTRIBUCION CUMPLIMIENTO HISTORICO (346 Comunas) ---")
    for s in range(5, -1, -1):
        cnt = dist_all_hist[s]
        pct = cnt / 346 * 100
        bar = "#" * int(pct / 2)
        print(f"  {s}/5: {cnt:3d} comunas ({pct:5.1f}%) | {bar}")

    print(f"\n--- DISTRIBUCION COHORTE ACTIVA ({len(active_cohort)} Comunas) ---")
    for s in range(5, -1, -1):
        cnt = dist_active_hist[s]
        pct = cnt / len(active_cohort) * 100
        bar = "#" * int(pct / 2)
        print(f"  {s}/5: {cnt:3d} comunas ({pct:5.1f}%) | {bar}")

    print("\n--- RANKING DE LAS 5 MATERIAS OBLIGATORIAS ---")
    for item in metrics_export["ranking_materias"]:
        print(f"  {item['nombre']:<55} | {item['comunas_historico']:3d} comunas ({item['cobertura_nacional_pct']:5.1f}%) | Recientes: {item['comunas_reciente']:3d} ({item['cobertura_reciente_pct']:5.1f}%)")

    print("\n--- PROMEDIO HISTORICO POR MACROZONA ---")
    for mz, data in macro_stats.items():
        avg = data["score_hist_sum"] / data["comunas"] if data["comunas"] else 0
        print(f"  {mz:<15}: Promedio {avg:.2f}/5.00 | {data['comunas']} comunas (5/5: {data['score_dist_hist'][5]})")

    print(f"\nComunas con cumplimiento perfecto (5/5): {len(destacadas_5_5)}")
    print(f"Comunas con 0/5 ordenanzas: {[c['comuna'] for c in criticas_0_5]}")
    print("=======================================================\n")

if __name__ == "__main__":
    run_audit()
