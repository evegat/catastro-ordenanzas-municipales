"""
Enriquecimiento semántico completo de las 1.632 ordenanzas (BCN y Transparencia Activa CPLT)
con categorización temática, preservación de fuentes y generación de datos para el dashboard.
"""

import json
import sqlite3
import requests
import unicodedata
from pathlib import Path
from datetime import datetime

DB_PATH = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/catastro_ordenanzas.db")
DASHBOARD_JSON = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.json")
DASHBOARD_JS = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.js")

CATEGORIAS = [
    {
        "id": "derechos_tarifas",
        "nombre": "Derechos Municipales y Tarifas",
        "color": "indigo",
        "badge_bg": "bg-indigo-500/10",
        "badge_text": "text-indigo-400",
        "badge_border": "border-indigo-500/30",
        "icono": "badge-dollar-sign",
        "keywords": ["derecho", "tarifa", "cobro", "exenc", "renta", "concesion", "arancel", "pago", "presupuesto", "tasa"]
    },
    {
        "id": "comercio_alcoholes",
        "nombre": "Comercio, Alcoholes y Patentes",
        "color": "sky",
        "badge_bg": "bg-sky-500/10",
        "badge_text": "text-sky-400",
        "badge_border": "border-sky-500/30",
        "icono": "store",
        "keywords": ["comercio", "comercial", "patente", "alcohol", "feria", "propaganda", "publicidad", "quiosco", "kiosco", "restauran", "ambulante", "espectaculo", "flipper", "billar", "juego", "fonda", "ramada", "botilleria", "microempresa", "mercado"]
    },
    {
        "id": "aseo_medioambiente",
        "nombre": "Aseo, Ornato y Medio Ambiente",
        "color": "emerald",
        "badge_bg": "bg-emerald-500/10",
        "badge_text": "text-emerald-400",
        "badge_border": "border-emerald-500/30",
        "icono": "trash-2",
        "keywords": ["aseo", "ornato", "basura", "residuo", "reciclaj", "escombro", "verde", "arbol", "medio ambiente", "contaminac", "ruido", "humedal", "plastico", "limpieza", "extraccion", "vertedero", "jardin", "rep"]
    },
    {
        "id": "transito_transporte",
        "nombre": "Tránsito y Transporte",
        "color": "amber",
        "badge_bg": "bg-amber-500/10",
        "badge_text": "text-amber-400",
        "badge_border": "border-amber-500/30",
        "icono": "car",
        "keywords": ["transito", "vehiculo", "estacionamiento", "parquimetro", "transporte", "ciclovia", "carga", "descarga", "vial", "conductor", "peaton", "velocidad", "paradero", "linea de distribucion", "energia"]
    },
    {
        "id": "urbanismo_obras",
        "nombre": "Urbanismo, Obras y Edificación",
        "color": "orange",
        "badge_bg": "bg-orange-500/10",
        "badge_text": "text-orange-400",
        "badge_border": "border-orange-500/30",
        "icono": "building",
        "keywords": ["obra", "construc", "edific", "urban", "regulador", "loteo", "acera", "cierro", "bien nacional", "suelo", "antena", "torre", "andamio", "ocupacion", "inmueble", "numeracion", "vivienda", "pavimento", "enmienda"]
    },
    {
        "id": "seguridad_convivencia",
        "nombre": "Seguridad y Convivencia",
        "color": "rose",
        "badge_bg": "bg-rose-500/10",
        "badge_text": "text-rose-400",
        "badge_border": "border-rose-500/30",
        "icono": "shield-alert",
        "keywords": ["seguridad", "convivencia", "pasaje", "alarma", "camara", "vigilancia", "alcohol en la via", "incivilidad", "droga", "orden publico", "cierre de calle", "acoso"]
    },
    {
        "id": "mascotas_animales",
        "nombre": "Tenencia Responsable y Mascotas",
        "color": "teal",
        "badge_bg": "bg-teal-500/10",
        "badge_text": "text-teal-400",
        "badge_border": "border-teal-500/30",
        "icono": "dog",
        "keywords": ["mascota", "animal", "perro", "canin", "gato", "tenencia responsable", "veterinari", "mordedura", "fauna", "zoonosis"]
    },
    {
        "id": "social_salud_deporte",
        "nombre": "Salud, Deporte y Desarrollo Social",
        "color": "purple",
        "badge_bg": "bg-purple-500/10",
        "badge_text": "text-purple-400",
        "badge_border": "border-purple-500/30",
        "icono": "heart-handshake",
        "keywords": ["salud", "deporte", "social", "cementerio", "crematorio", "junta de vecino", "subvencion", "cultura", "adulto mayor", "juventud", "infancia", "beca", "persona juridica", "organizacion comunitaria"]
    },
    {
        "id": "administracion_interna",
        "nombre": "Organización y Régimen Interno",
        "color": "zinc",
        "badge_bg": "bg-zinc-800",
        "badge_text": "text-zinc-300",
        "badge_border": "border-zinc-700",
        "icono": "landmark",
        "keywords": ["organiza", "reglamento", "concejo", "cosoc", "interno", "comision", "secretaria", "alcaldia", "delegac", "participacion", "transparencia", "consejo"]
    }
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    no_acc = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return no_acc.lower().strip()

def normalize_uri(u: str) -> str:
    if not u:
        return ""
    return u.replace("http://", "https://").rstrip("/")

def categorize_title(title: str) -> dict:
    cleaned = clean_text(title)
    for cat in CATEGORIAS:
        for kw in cat["keywords"]:
            if kw in cleaned:
                return cat
    return {
        "id": "general",
        "nombre": "Normativa General y Otras Materias",
        "color": "zinc",
        "badge_bg": "bg-zinc-800",
        "badge_text": "text-zinc-400",
        "badge_border": "border-zinc-700",
        "icono": "file-text"
    }

def fetch_all_sparql_data():
    print("Extrayendo metadatos completos de todas las ordenanzas vía SPARQL...")
    sparql_url = "https://datos.bcn.cl/sparql"
    query = """
    PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>

    SELECT DISTINCT ?norma ?title ?leychileCode WHERE {
      ?norma a bcnnorms:RootNorm .
      FILTER(CONTAINS(LCASE(STR(?norma)), "/orz/"))
      ?norma bcnnorms:hasVersion ?version .
      ?version dc:title ?title .
      OPTIONAL { ?norma bcnnorms:leychileCode ?leychileCode }
    }
    """
    try:
        r = requests.get(sparql_url, params={"query": query, "format": "json"}, timeout=60)
        if r.status_code == 200:
            bindings = r.json()["results"]["bindings"]
            print(f"SPARQL entregó {len(bindings)} títulos de versiones.")
            meta_map = {}
            for b in bindings:
                norma = normalize_uri(b.get("norma", {}).get("value", ""))
                t = b.get("title", {}).get("value", "").strip()
                lc = b.get("leychileCode", {}).get("value", "").strip()
                if norma and t:
                    meta_map[norma] = {"title": t, "leychileCode": lc}
            return meta_map
    except Exception as e:
        print(f"Error SPARQL: {e}")
    return {}

def run_enrichment():
    meta_map = fetch_all_sparql_data()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, fuente, norma_uri, municipalidad_slug, comuna_nombre, fecha_publicacion, numero, titulo, pdf_url FROM ordenanzas")
    rows = cursor.fetchall()

    print(f"Procesando {len(rows)} ordenanzas en base SQLite...")

    topic_counts = {}
    commune_ordinances_map = {}
    total_bcn = 0
    total_cplt = 0

    for row in rows:
        db_id, fuente, norma_uri, slug, comuna, fecha, num, current_titulo, current_pdf_url = row
        norm_key = normalize_uri(norma_uri)
        
        is_cplt = (fuente == "CPLT")

        if is_cplt:
            total_cplt += 1
            title_final = current_titulo or f"Ordenanza Municipal N° {num} ({fecha}) - Municipalidad de {comuna}"
            target_url = current_pdf_url or "https://www.portaltransparencia.cl/"
            fuente_label = "Transparencia Activa (2022-2026)"
            rdf_url = None
        else:
            total_bcn += 1
            sparql_meta = meta_map.get(norm_key, {})
            title_raw = sparql_meta.get("title", "").strip()
            leychile_code = sparql_meta.get("leychileCode", "").strip()

            if not title_raw:
                title_final = current_titulo or f"Ordenanza Municipal N° {num} ({fecha}) - Municipalidad de {comuna}"
            else:
                title_final = title_raw

            if leychile_code:
                target_url = f"https://www.bcn.cl/leychile/navegar?idNorma={leychile_code}"
            else:
                target_url = f"https://www.bcn.cl/leychile/consulta/busquedas_avanzadas"
            
            fuente_label = "BCN LeyChile"
            rdf_url = f"{norma_uri}/datos.json"

        cat = categorize_title(title_final)
        materia_nombre = cat["nombre"]
        materia_id = cat["id"]

        topic_counts[materia_nombre] = topic_counts.get(materia_nombre, 0) + 1

        cursor.execute("""
            UPDATE ordenanzas 
            SET titulo = ?, materia = ?, pdf_url = ?
            WHERE id = ?
        """, (title_final, materia_nombre, target_url, db_id))

        c_key = clean_text(comuna).replace("-", " ")
        if c_key not in commune_ordinances_map:
            commune_ordinances_map[c_key] = []

        commune_ordinances_map[c_key].append({
            "id": db_id,
            "fuente": fuente or "BCN",
            "fuente_label": fuente_label,
            "numero": num,
            "fecha": fecha,
            "titulo": title_final,
            "materia": materia_nombre,
            "materia_id": materia_id,
            "color": cat.get("color", "zinc"),
            "badge_bg": cat.get("badge_bg", "bg-zinc-800"),
            "badge_text": cat.get("badge_text", "text-zinc-300"),
            "badge_border": cat.get("badge_border", "border-zinc-700"),
            "target_url": target_url,
            "rdf_url": rdf_url
        })

    conn.commit()
    conn.close()

    # Update dashboard JSON
    with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    comunas_con_datos = 0
    for c in data.get("comunas", []):
        c_clean = clean_text(c["comuna"]).replace("-", " ")
        matched_ords = []
        for k, ords in commune_ordinances_map.items():
            if c_clean == k or c_clean in k or k in c_clean:
                matched_ords.extend(ords)
        
        # Deduplicate
        seen_ids = set()
        dedup_ords = []
        for o in matched_ords:
            if o["id"] not in seen_ids:
                seen_ids.add(o["id"])
                dedup_ords.append(o)
        
        # Sort by date descending
        dedup_ords.sort(key=lambda x: str(x.get("fecha", "")), reverse=True)

        bcn_cnt = sum(1 for o in dedup_ords if o.get("fuente") == "BCN")
        cplt_cnt = sum(1 for o in dedup_ords if o.get("fuente") == "CPLT")
        tot_cnt = len(dedup_ords)

        c["ordenanzas"] = dedup_ords
        c["bcn_count"] = bcn_cnt
        c["cplt_count"] = cplt_cnt
        c["total_count"] = tot_cnt

        if tot_cnt > 0:
            comunas_con_datos += 1
            if bcn_cnt > 0 and cplt_cnt > 0:
                c["status"] = "BCN + CPLT"
            elif cplt_cnt > 0:
                c["status"] = "Cargado CPLT"
            else:
                c["status"] = "Cargado BCN"
        else:
            c["status"] = "Pendiente CPLT"

    # Overall metrics
    data["metrics"]["ordenanzas_bcn"] = total_bcn
    data["metrics"]["ordenanzas_cplt"] = total_cplt
    data["metrics"]["total_ordenanzas"] = total_bcn + total_cplt
    data["metrics"]["comunas_con_datos"] = comunas_con_datos

    # Add topic distribution metrics
    data["topics"] = [
        {
            "id": cat["id"],
            "nombre": cat["nombre"],
            "color": cat["color"],
            "icono": cat["icono"],
            "badge_bg": cat["badge_bg"],
            "badge_text": cat["badge_text"],
            "badge_border": cat["badge_border"],
            "count": topic_counts.get(cat["nombre"], 0)
        }
        for cat in CATEGORIAS
    ]
    gen_cnt = topic_counts.get("Normativa General y Otras Materias", 0)
    if gen_cnt > 0:
        data["topics"].append({
            "id": "general",
            "nombre": "Normativa General y Otras Materias",
            "color": "zinc",
            "icono": "file-text",
            "badge_bg": "bg-zinc-800",
            "badge_text": "text-zinc-400",
            "badge_border": "border-zinc-700",
            "count": gen_cnt
        })

    data["updated_at"] = datetime.now().isoformat()

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(DASHBOARD_JS, "w", encoding="utf-8") as f:
        f.write("window.CATASTRO_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";")

    print(f"\nConsolidación final completada:")
    print(f"  • BCN: {total_bcn}")
    print(f"  • CPLT: {total_cplt}")
    print(f"  • Total: {total_bcn + total_cplt}")
    print(f"  • Comunas con datos: {comunas_con_datos} / 346")

if __name__ == "__main__":
    run_enrichment()
