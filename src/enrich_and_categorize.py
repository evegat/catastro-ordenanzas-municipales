"""
Extractor de títulos, enlaces a LeyChile y categorizador semántico de ordenanzas municipales.
"""

import re
import csv
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
        "id": "aseo_medioambiente",
        "nombre": "Aseo, Ornato y Medio Ambiente",
        "color": "emerald",
        "icono": "trash-2",
        "keywords": ["aseo", "ornato", "basura", "residuo", "reciclaj", "escombro", "verde", "arbol", "medio ambiente", "contaminac", "ruido", "humedal", "plastico", "limpieza"]
    },
    {
        "id": "transito_transporte",
        "nombre": "Tránsito y Transporte",
        "color": "amber",
        "icono": "car",
        "keywords": ["transito", "vehiculo", "estacionamiento", "parquimetro", "transporte", "ciclovia", "carga", "descarga", "vial", "conductor", "peaton", "velocidad"]
    },
    {
        "id": "comercio_alcoholes",
        "nombre": "Comercio, Alcoholes y Patentes",
        "color": "sky",
        "icono": "store",
        "keywords": ["comercio", "comercial", "patente", "alcohol", "feria", "propaganda", "publicidad", "quiosco", "kiosco", "restauran", "ambulante", "espectaculo", "flipper", "billar", "juego", "fondas", "ramada"]
    },
    {
        "id": "derechos_tarifas",
        "nombre": "Derechos Municipales y Tarifas",
        "color": "indigo",
        "icono": "badge-dollar-sign",
        "keywords": ["derecho", "tarifa", "cobro", "exenc", "renta", "concesion", "arancel", "pago", "presupuesto"]
    },
    {
        "id": "urbanismo_obras",
        "nombre": "Urbanismo, Obras y Edificación",
        "color": "orange",
        "icono": "building",
        "keywords": ["obra", "construc", "edific", "urban", "regulador", "loteo", "acera", "cierro", "bien nacional", "suelo", "antena", "torre", "andamio", "ocupacion"]
    },
    {
        "id": "seguridad_convivencia",
        "nombre": "Seguridad y Convivencia",
        "color": "rose",
        "icono": "shield-alert",
        "keywords": ["seguridad", "convivencia", "pasaje", "alarma", "camara", "vigilancia", "alcohol en la via", "incivilidad", "droga", "orden publico"]
    },
    {
        "id": "mascotas_animales",
        "nombre": "Tenencia Responsable y Animales",
        "color": "teal",
        "icono": "dog",
        "keywords": ["mascota", "animal", "perro", "canin", "gato", "tenencia responsable", "veterinari", "mordedura", "fauna"]
    },
    {
        "id": "social_salud_deporte",
        "nombre": "Salud, Deporte y Comunidad",
        "color": "purple",
        "icono": "heart-handshake",
        "keywords": ["salud", "deporte", "social", "cementerio", "junta de vecino", "subvencion", "cultura", "adulto mayor", "juventud", "infancia", "beca"]
    },
    {
        "id": "administracion_interna",
        "nombre": "Organización y Régimen Interno",
        "color": "zinc",
        "icono": "landmark",
        "keywords": ["organiza", "reglamento", "concejo", "cosoc", "interno", "comision", "secretaria", "alcaldia", "delegac", "participacion"]
    }
]

def clean_text(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    no_acc = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return no_acc.lower()

def categorize_title(title: str) -> dict:
    cleaned = clean_text(title)
    for cat in CATEGORIAS:
        for kw in cat["keywords"]:
            if kw in cleaned:
                return cat
    # Default fallback
    return {
        "id": "general",
        "nombre": "Normativa General y Otras Materias",
        "color": "zinc",
        "icono": "file-text"
    }

def fetch_bcn_sparql_metadata():
    print("Consultando endpoint SPARQL de la BCN para extraer títulos y enlaces LeyChile...")
    sparql_url = "https://datos.bcn.cl/sparql"
    query = """
    PREFIX bcnnorms: <http://datos.bcn.cl/ontologies/bcn-norms#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?norma ?title ?leychileCode ?publishDate ?number WHERE {
      ?norma a bcnnorms:RootNorm .
      FILTER(CONTAINS(LCASE(STR(?norma)), "/orz/"))
      OPTIONAL { ?norma dc:title ?title }
      OPTIONAL { ?norma bcnnorms:leychileCode ?leychileCode }
      OPTIONAL { ?norma bcnnorms:publishDate ?publishDate }
      OPTIONAL { ?norma bcnnorms:hasNumber ?number }
    }
    """
    try:
        r = requests.get(sparql_url, params={"query": query, "format": "json"}, timeout=60)
        if r.status_code == 200:
            bindings = r.json()["results"]["bindings"]
            print(f"SPARQL devolvió {len(bindings)} registros enriquecidos.")
            meta_map = {}
            for b in bindings:
                norma = b.get("norma", {}).get("value", "")
                if norma:
                    meta_map[norma] = {
                        "title": b.get("title", {}).get("value", ""),
                        "leychileCode": b.get("leychileCode", {}).get("value", ""),
                        "publishDate": b.get("publishDate", {}).get("value", ""),
                        "number": b.get("number", {}).get("value", "")
                    }
            return meta_map
    except Exception as e:
        print(f"Error consultando SPARQL: {e}")
    return {}

def run_enrichment():
    meta_map = fetch_bcn_sparql_metadata()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, norma_uri, municipalidad_slug, comuna_nombre, fecha_publicacion, numero, titulo FROM ordenanzas")
    rows = cursor.fetchall()

    print(f"Enriqueciendo y categorizando semánticamente {len(rows)} ordenanzas...")

    topic_counts = {}
    commune_ordinances_map = {}

    for row in rows:
        db_id, norma_uri, slug, comuna, fecha, num, current_titulo = row
        
        # Check if we got SPARQL metadata
        sparql_meta = meta_map.get(norma_uri, {})
        titulo_final = sparql_meta.get("title") or current_titulo
        leychile_code = sparql_meta.get("leychileCode") or ""

        # Construct LeyChile URL
        if leychile_code:
            leychile_url = f"https://www.bcn.cl/leychile/navegar?idNorma={leychile_code}"
        else:
            leychile_url = f"https://www.bcn.cl/leychile/consulta/busquedas_avanzadas"

        # Categorize semantically
        cat = categorize_title(titulo_final)
        materia_nombre = cat["nombre"]
        materia_id = cat["id"]

        topic_counts[materia_nombre] = topic_counts.get(materia_nombre, 0) + 1

        # Update in SQLite
        cursor.execute("""
            UPDATE ordenanzas 
            SET titulo = ?, materia = ?, pdf_url = ?
            WHERE id = ?
        """, (titulo_final, materia_nombre, leychile_url, db_id))

        # Store for dashboard commune details
        c_key = clean_text(comuna)
        if c_key not in commune_ordinances_map:
            commune_ordinances_map[c_key] = []

        commune_ordinances_map[c_key].append({
            "id": db_id,
            "numero": num,
            "fecha": fecha,
            "titulo": titulo_final,
            "materia": materia_nombre,
            "materia_id": materia_id,
            "leychile_url": leychile_url,
            "rdf_url": f"{norma_uri}/datos.json"
        })

    conn.commit()
    conn.close()

    # Update dashboard JSON
    with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Attach ordinances details to each commune
    for c in data.get("comunas", []):
        c_key = clean_text(c["comuna"])
        ords = commune_ordinances_map.get(c_key, [])
        c["ordenanzas"] = ords
        if ords and c["bcn_count"] == 0:
            c["bcn_count"] = len(ords)
            c["total_count"] = len(ords)
            c["status"] = "Cargado BCN"

    # Add topic distribution metrics
    data["topics"] = [
        {"id": cat["id"], "nombre": cat["nombre"], "color": cat["color"], "icono": cat["icono"], "count": topic_counts.get(cat["nombre"], 0)}
        for cat in CATEGORIAS
    ]
    data["updated_at"] = datetime.now().isoformat()

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(DASHBOARD_JS, "w", encoding="utf-8") as f:
        f.write("window.CATASTRO_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";")

    print("\nCategorización temática completada exitosamente:")
    for t in data["topics"]:
        print(f"  • {t['nombre']}: {t['count']} ordenanzas")

if __name__ == "__main__":
    run_enrichment()
