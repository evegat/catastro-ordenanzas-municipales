"""Remediación H03: Homologación Taxonómica a los 9 Ejes Canónicos.
Mapea las 41 etiquetas históricas a los 9 ejes temáticos canónicos universales,
conservando la etiqueta original en el campo 'submateria'.
Task ID: P090-AUD-WEB-20261002
"""

import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
STATUS_DATA_PATH = REPO_ROOT / "dashboard" / "status_data.json"

CANONICAL_AXES = {
    "aseo_residuos": {
        "nombre": "Aseo, Ornato y Gestión de Residuos",
        "color": "emerald",
        "icono": "trash-2",
        "badge_bg": "bg-emerald-500/10",
        "badge_text": "text-emerald-400",
        "badge_border": "border-emerald-500/30"
    },
    "comercio_publicidad": {
        "nombre": "Comercio, Vía Pública y Publicidad",
        "color": "sky",
        "icono": "store",
        "badge_bg": "bg-sky-500/10",
        "badge_text": "text-sky-400",
        "badge_border": "border-sky-500/30"
    },
    "convivencia_ruidos": {
        "nombre": "Convivencia Vecinal y Ruidos Molestos",
        "color": "rose",
        "icono": "volume-2",
        "badge_bg": "bg-rose-500/10",
        "badge_text": "text-rose-400",
        "badge_border": "border-rose-500/30"
    },
    "derechos_tarifas": {
        "nombre": "Derechos, Tarifas y Concesiones Municipales",
        "color": "indigo",
        "icono": "badge-dollar-sign",
        "badge_bg": "bg-indigo-500/10",
        "badge_text": "text-indigo-400",
        "badge_border": "border-indigo-500/30"
    },
    "medio_ambiente": {
        "nombre": "Medio Ambiente, Humedales y Tenencia Responsable",
        "color": "teal",
        "icono": "leaf",
        "badge_bg": "bg-teal-500/10",
        "badge_text": "text-teal-400",
        "badge_border": "border-teal-500/30"
    },
    "obras_espacio_publico": {
        "nombre": "Obras, Urbanismo y Espacio Público",
        "color": "orange",
        "icono": "building",
        "badge_bg": "bg-orange-500/10",
        "badge_text": "text-orange-400",
        "badge_border": "border-orange-500/30"
    },
    "organizacion_participacion": {
        "nombre": "Organización Interna y Participación Ciudadana",
        "color": "zinc",
        "icono": "landmark",
        "badge_bg": "bg-zinc-800",
        "badge_text": "text-zinc-300",
        "badge_border": "border-zinc-700"
    },
    "transito_transporte": {
        "nombre": "Tránsito, Transporte y Estacionamientos",
        "color": "amber",
        "icono": "car",
        "badge_bg": "bg-amber-500/10",
        "badge_text": "text-amber-400",
        "badge_border": "border-amber-500/30"
    },
    "seguridad_prevencion": {
        "nombre": "Seguridad Ciudadana y Prevención",
        "color": "purple",
        "icono": "shield",
        "badge_bg": "bg-purple-500/10",
        "badge_text": "text-purple-400",
        "badge_border": "border-purple-500/30"
    }
}

# Tabla de mapeo de las 41 etiquetas históricas a (eje_id, nombre_canonico)
LABEL_MAPPING = {
    # Derechos y Tarifas
    "Derechos Municipales y Tarifas": "derechos_tarifas",
    "Derechos Municipales y cobro de tarifas": "derechos_tarifas",
    "Derechos, Tarifas y Concesiones Municipales": "derechos_tarifas",
    
    # Comercio y Vía Pública
    "Comercio, Alcoholes y Patentes": "comercio_publicidad",
    "Comercio, Vía Pública y Patentes": "comercio_publicidad",
    "Patentes, Comercio y Alcoholes": "comercio_publicidad",
    "Comercio, Rentas y Patentes": "comercio_publicidad",
    "Comercio, Alcoholes y Ferias": "comercio_publicidad",
    "Alcoholes y Seguridad Ciudadana": "comercio_publicidad",
    
    # Aseo y Residuos
    "Aseo, Ornato y Gestión de Residuos": "aseo_residuos",
    "Aseo, Ornato y Medio Ambiente": "aseo_residuos",
    "Medio Ambiente y Aseo": "aseo_residuos",
    
    # Medio Ambiente, Humedales y Mascotas
    "Medio Ambiente y Sustentabilidad": "medio_ambiente",
    "Medio ambiente, protección de humedales urbanos y biodiversidad": "medio_ambiente",
    "Tenencia Responsable de Mascotas": "medio_ambiente",
    "Tenencia Responsable y Mascotas": "medio_ambiente",
    "Tenencia responsable de mascotas y bienestar animal": "medio_ambiente",
    
    # Tránsito y Transporte
    "Tránsito y Transporte": "transito_transporte",
    "Tránsito, Transporte y Estacionamientos": "transito_transporte",
    "Tránsito, Transporte y Espacio Público": "transito_transporte",
    
    # Obras y Urbanismo
    "Urbanismo, Obras y Edificación": "obras_espacio_publico",
    "Urbanismo, Obras y Construcción": "obras_espacio_publico",
    "Obras, Urbanismo y Espacio Público": "obras_espacio_publico",
    "Plan Regulador y Obras": "obras_espacio_publico",
    "Urbanismo, Obras y Plan Regulador": "obras_espacio_publico",
    
    # Convivencia y Ruidos
    "Convivencia Vecinal y Ruidos Molestos": "convivencia_ruidos",
    "Convivencia Vecinal y Seguridad": "convivencia_ruidos",
    "Normas Sanitarias y Convivencia": "convivencia_ruidos",
    
    # Seguridad y Prevención
    "Seguridad y Convivencia": "seguridad_prevencion",
    "Seguridad Ciudadana y Convivencia": "seguridad_prevencion",
    "Seguridad Ciudadana y Prevención": "seguridad_prevencion",
    
    # Organización Interna, Participación y Social
    "Organización y Régimen Interno": "organizacion_participacion",
    "Organización Interna y Personal": "organizacion_participacion",
    "Subvenciones y Régimen Interno": "organizacion_participacion",
    "Subvenciones, aportes y fomento comunitario": "organizacion_participacion",
    "Participación Ciudadana": "organizacion_participacion",
    "Participación y Organizaciones Comunitarias": "organizacion_participacion",
    "Participación Ciudadana y Gobernanza Local": "organizacion_participacion",
    "Salud, Deporte y Desarrollo Social": "organizacion_participacion",
    "Salud, Higiene y Bienestar Social": "organizacion_participacion",
    "Educación, Becas y Desarrollo Social": "organizacion_participacion",
    "Desarrollo Social y Grupos Prioritarios": "organizacion_participacion",
    "Organización Interna y Participación Ciudadana": "organizacion_participacion",
}

def classify_title(title: str) -> str:
    t = title.lower()
    if re.search(r"ruido|ac[uú]stic|sonor", t):
        return "convivencia_ruidos"
    if re.search(r"derecho|tarifa|arancel|concesi[oó]n|cobro|rentas", t):
        return "derechos_tarifas"
    if re.search(r"comercio|patente|alcohol|feria|propaganda|publicidad|kiosco|ambulante|mercado", t):
        return "comercio_publicidad"
    if re.search(r"aseo|basura|residuo|limpieza|escombro|recolecci[oó]n", t):
        return "aseo_residuos"
    if re.search(r"humedal|biodiversidad|medio\s+ambiente|mascota|animal|canin|perro|arbolado", t):
        return "medio_ambiente"
    if re.search(r"tr[aá]nsito|transporte|veh[ií]cul|estacionamiento|paradero|circulaci[oó]n", t):
        return "transito_transporte"
    if re.search(r"obra|urbanis|edific|construc|plan\s+regulador|cierro|antena|fachada|paviment", t):
        return "obras_espacio_publico"
    if re.search(r"seguridad|alarma|vigilancia|prevenci[oó]n|delito", t):
        return "seguridad_prevencion"
    if re.search(r"participaci[oó]n|plebiscito|cosoc|comunitari|subvenci[oó]n|junta|concejo|personal|estatuto", t):
        return "organizacion_participacion"
    return "organizacion_participacion"

def run_remediation():
    with open(STATUS_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    stats = {axis_id: 0 for axis_id in CANONICAL_AXES}
    migrated_from_general = 0

    for c in data.get("comunas", []):
        for ord_ in c.get("ordenanzas", []):
            orig_mat = ord_.get("materia", "")
            ord_["submateria"] = orig_mat  # Conservar siempre etiqueta histórica

            axis_id = None
            if orig_mat in LABEL_MAPPING:
                axis_id = LABEL_MAPPING[orig_mat]
            elif orig_mat == "Normativa General y Otras Materias" or not orig_mat:
                axis_id = classify_title(ord_.get("titulo", ""))
                migrated_from_general += 1
            else:
                axis_id = classify_title(ord_.get("titulo", ""))

            axis_meta = CANONICAL_AXES[axis_id]
            ord_["materia_id"] = axis_id
            ord_["materia"] = axis_meta["nombre"]
            stats[axis_id] += 1

    # Actualizar la lista canónica de topics en status_data
    topics = []
    for axis_id, meta in CANONICAL_AXES.items():
        topics.append({
            "id": axis_id,
            "nombre": meta["nombre"],
            "color": meta["color"],
            "icono": meta["icono"],
            "badge_bg": meta["badge_bg"],
            "badge_text": meta["badge_text"],
            "badge_border": meta["badge_border"],
            "count": stats[axis_id]
        })

    data["topics"] = topics

    with open(STATUS_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("H03 Remediación completada:")
    print(f"  - Normas migradas desde 'Normativa General': {migrated_from_general}")
    print("  - Distribución en los 9 ejes canónicos:")
    for t in topics:
        print(f"    * {t['nombre']}: {t['count']} normas")

if __name__ == "__main__":
    run_remediation()
