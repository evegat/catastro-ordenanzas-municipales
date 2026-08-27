"""
Consolidación total de ordenanzas 2022-2026 (Zona Norte, Centro/RM y Sur/Austral) en SQLite y Dashboard.
"""

import json
import sqlite3
from pathlib import Path
from enrich_all_bcn import categorize_title, clean_text, CATEGORIAS

DB_PATH = Path("D:/Datasets/P090 - BCN Ordenanzas municipales/catastro_ordenanzas.db")
DASHBOARD_JSON = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.json")
DASHBOARD_JS = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN/dashboard/status_data.js")

ALL_CPLT_RECORDS = [
    # ZONA NORTE (Regiones XV a IV)
    {"comuna": "Arica", "region_id": "15", "numero": "Ord. 05/2024", "fecha": "2024-11-04", "titulo": "Texto Refundido y Sistematizado de la Ordenanza Local sobre Derechos Municipales por Permisos, Concesiones y Servicios", "url": "https://www.muniarica.cl/archivos/ordenanzas/ordenanza_5_2024.pdf"},
    {"comuna": "Arica", "region_id": "15", "numero": "Ord. 01/2023", "fecha": "2023-04-12", "titulo": "Ordenanza sobre Gestión Integral de Residuos Sólidos Domiciliarios, Limpieza y Aseo Comunal", "url": "https://www.muniarica.cl/archivos/ordenanzas/ordenanza_1_2023.pdf"},
    {"comuna": "Arica", "region_id": "15", "numero": "D.A. 3862/2026", "fecha": "2026-02-10", "titulo": "Modificación al Reglamento y Ordenanza de Uso de Bienes Nacionales de Uso Público para Ferias Libres e Itinerantes", "url": "https://www.muniarica.cl/archivos/decretos/DAL_3862_2026.pdf"},
    {"comuna": "Iquique", "region_id": "01", "numero": "Ord. 10/2024", "fecha": "2024-10-30", "titulo": "Fija Derechos Municipales por Concesiones, Permisos y Servicios para el Año 2025 en la Comuna de Iquique", "url": "https://transparencia.municipioiquique.cl/documentos/ordenanzas/ordenanza_10_2024.pdf"},
    {"comuna": "Iquique", "region_id": "01", "numero": "D.A. 184/2025", "fecha": "2025-01-30", "titulo": "Modificación de la Ordenanza sobre Expendio y Consumo de Bebidas Alcohólicas y Restricciones Horarias en el Borde Costero", "url": "https://transparencia.municipioiquique.cl/documentos/decretos/DA_184_2025.pdf"},
    {"comuna": "Iquique", "region_id": "01", "numero": "Ord. 03/2023", "fecha": "2023-08-18", "titulo": "Regula el Uso, Cuidado y Protección del Borde Costero, Playas y Balnearios de la Comuna de Iquique", "url": "https://transparencia.municipioiquique.cl/documentos/ordenanzas/ordenanza_3_2023.pdf"},
    {"comuna": "Alto Hospicio", "region_id": "01", "numero": "Ord. 04/2024", "fecha": "2024-10-25", "titulo": "Ordenanza Local sobre Derechos Municipales por Permisos, Concesiones y Servicios de la Municipalidad de Alto Hospicio", "url": "https://www.maho.cl/transparencia/normativa/ordenanza_derechos_2025.pdf"},
    {"comuna": "Antofagasta", "region_id": "02", "numero": "Ord. 01/2026", "fecha": "2026-08-19", "titulo": "Ordenanza Municipal sobre Funcionamiento y Servicios de Crematorio Municipal de Antofagasta", "url": "https://www.municipalidadantofagasta.cl/ordenanzas/ordenanza_crematorio_01_2026.pdf"},
    {"comuna": "Antofagasta", "region_id": "02", "numero": "Ord. 03/2026", "fecha": "2026-03-12", "titulo": "Ordenanza sobre Gestión de Residuos, Reciclaje y Responsabilidad Extendida del Productor (REP)", "url": "https://www.municipalidadantofagasta.cl/ordenanzas/ordenanza_rep_03_2026.pdf"},
    {"comuna": "Antofagasta", "region_id": "02", "numero": "Ord. 01/2025", "fecha": "2025-06-23", "titulo": "Ordenanza para la Protección, Conservación y Gestión de Humedales Urbanos de la Comuna de Antofagasta", "url": "https://www.municipalidadantofagasta.cl/ordenanzas/ordenanza_humedales_01_2025.pdf"},
    {"comuna": "Antofagasta", "region_id": "02", "numero": "D.A. 298/2023", "fecha": "2023-02-15", "titulo": "Reglamento y Ordenanza sobre Cierre de Calles, Pasajes o Conjuntos Habitacionales por Motivos de Seguridad (Ley 21.411)", "url": "https://www.municipalidadantofagasta.cl/ordenanzas/cierre_calles_2023.pdf"},
    {"comuna": "Calama", "region_id": "02", "numero": "Ord. 08/2024", "fecha": "2024-10-28", "titulo": "Ordenanza sobre Derechos Municipales por Permisos, Concesiones y Servicios para el Período 2025", "url": "https://www.municipalidadcalama.cl/transparencia/ordenanzas/ordenanza_08_2024.pdf"},
    {"comuna": "Calama", "region_id": "02", "numero": "D.A. 1102/2024", "fecha": "2024-05-14", "titulo": "Ordenanza de Protección del Humedal Urbano Ojos de Opache y Cuenca del Río Loa", "url": "https://www.municipalidadcalama.cl/transparencia/decretos/DA_1102_2024.pdf"},
    {"comuna": "Copiapó", "region_id": "03", "numero": "D.A. 3598/2024", "fecha": "2024-08-20", "titulo": "Promulgación de Enmienda al Plan Regulador Comunal de Copiapó en Sector Borde Río Copiapó", "url": "https://www.copiapo.cl/transparencia/decretos/DA_3598_2024.pdf"},
    {"comuna": "Copiapó", "region_id": "03", "numero": "Ord. 06/2024", "fecha": "2024-10-31", "titulo": "Fija Derechos Municipales por Concesiones, Permisos y Servicios para el Ejercicio 2025", "url": "https://www.copiapo.cl/transparencia/ordenanzas/ordenanza_derechos_2025.pdf"},
    {"comuna": "Vallenar", "region_id": "03", "numero": "Ord. 10/2024", "fecha": "2024-10-30", "titulo": "Regula los Derechos Municipales por Permisos, Concesiones y Servicios para el Año 2025", "url": "https://www.vallenar.cl/transparencia/ordenanzas/ordenanza_10_2024.pdf"},
    {"comuna": "La Serena", "region_id": "04", "numero": "Ord. 16/2025", "fecha": "2025-10-29", "titulo": "Ordenanza sobre Derechos Municipales por Permisos, Concesiones y Servicios Vigente para el Año 2026", "url": "https://transparencia.laserena.cl/ordenanzas/ordenanza_16_2025.pdf"},
    {"comuna": "La Serena", "region_id": "04", "numero": "Ord. 02/2024", "fecha": "2024-04-16", "titulo": "Ordenanza sobre Comercio Ambulante y Estacionado en Bienes Nacionales de Uso Público del Casco Histórico", "url": "https://transparencia.laserena.cl/ordenanzas/ordenanza_02_2024.pdf"},
    {"comuna": "Coquimbo", "region_id": "04", "numero": "Ord. 09/2024", "fecha": "2024-10-31", "titulo": "Ordenanza Local de Derechos Municipales por Permisos, Concesiones y Servicios de la Comuna de Coquimbo", "url": "https://transparencia.municoquimbo.cl/ordenanzas/ordenanza_09_2024.pdf"},
    {"comuna": "Coquimbo", "region_id": "04", "numero": "D.A. 842/2023", "fecha": "2023-07-11", "titulo": "Regulación de Horarios y Condiciones de Funcionamiento de Establecimientos con Patentes de Alcoholes", "url": "https://transparencia.municoquimbo.cl/decretos/DA_842_2023.pdf"},
    {"comuna": "Ovalle", "region_id": "04", "numero": "Ord. 07/2024", "fecha": "2024-10-30", "titulo": "Ordenanza sobre Derechos Municipales por Permisos, Concesiones y Servicios Correspondiente al Período 2025", "url": "https://transparencia.muniovalle.gob.cl/ordenanzas/ordenanza_derechos_2025.pdf"},

    # ZONA CENTRO Y RM (Regiones V, XIII, VI, VII)
    {"comuna": "Santiago", "region_id": "13", "numero": "D.A. 94", "fecha": "2024-11-15", "titulo": "Ordenanza Local sobre Derechos Municipales por Concesiones, Permisos y Servicios (Texto Refundido 2025)", "url": "https://www.munistgo.cl/transparencia/marco-normativo/"},
    {"comuna": "Santiago", "region_id": "13", "numero": "Reg. 971-2025", "fecha": "2025-01-15", "titulo": "Reglamento de Transparencia Activa y Acceso a la Información Pública Municipal", "url": "https://www.munistgo.cl/transparencia/"},
    {"comuna": "Providencia", "region_id": "13", "numero": "D.A. Ex. 1.570", "fecha": "2024-11-20", "titulo": "Fija Texto Refundido y Sistematizado de la Ordenanza Local sobre Derechos Municipales", "url": "https://www.providencia.cl/transparencia/"},
    {"comuna": "Las Condes", "region_id": "13", "numero": "D.A. 1.947", "fecha": "2025-06-09", "titulo": "Modificación a Ordenanza Municipal sobre Concesiones, Espacios Públicos y Gestión de Inmuebles", "url": "https://www.lascondes.cl/transparencia/"},
    {"comuna": "Las Condes", "region_id": "13", "numero": "D.A. 4.120", "fecha": "2024-10-18", "titulo": "Ordenanza sobre Convivencia Comunal, Prevención de Ruidos Molestos y Tenencia Responsable", "url": "https://www.lascondes.cl/ordenanzas/"},
    {"comuna": "Vitacura", "region_id": "13", "numero": "D.A. 824", "fecha": "2024-05-14", "titulo": "Ordenanza Local sobre Gestión Hídrica, Sustentabilidad y Riego Eficiente en Espacios Públicos", "url": "https://www.vitacura.cl/transparencia/"},
    {"comuna": "Maipú", "region_id": "13", "numero": "D.A. 2.385", "fecha": "2024-04-19", "titulo": "Aprueba Plan Comunal para la Reducción del Riesgo de Desastres 2023-2030 (Gestión de Emergencias)", "url": "https://www.municipalidadmaipu.cl/"},
    {"comuna": "Maipú", "region_id": "13", "numero": "D.A. 2.386", "fecha": "2024-04-19", "titulo": "Aprueba Plan Comunal de Emergencias y Protocolos de Respuesta Comunal", "url": "https://www.municipalidadmaipu.cl/"},
    {"comuna": "La Florida", "region_id": "13", "numero": "D.A. 510/2025", "fecha": "2025-03-12", "titulo": "Modificación a la Ordenanza de Derechos Municipales y Uso de Espacios Deportivos y Comunitarios", "url": "https://www.laflorida.cl/"},
    {"comuna": "Puente Alto", "region_id": "13", "numero": "D.A. 2.376", "fecha": "2024-08-01", "titulo": "Protocolo y Ordenanza Complementaria para la Prevención de Acoso y Seguridad en Espacios Públicos", "url": "https://www.puentealto.cl/"},
    {"comuna": "Valparaíso", "region_id": "05", "numero": "D.A. 3.110", "fecha": "2025-01-20", "titulo": "Ordenanza de Comercio en el Bien Nacional de Uso Público y Bienes Municipales (Regulación Ambulante)", "url": "https://www.munivalpo.cl/transparencia/"},
    {"comuna": "Valparaíso", "region_id": "05", "numero": "D.A. 1.845", "fecha": "2025-02-14", "titulo": "Ordenanza Municipal que Regula el Tránsito, Estacionamiento y Carga/Descarga en Polígono Mercado El Cardonal", "url": "https://www.munivalpo.cl/transparencia/"},
    {"comuna": "Valparaíso", "region_id": "05", "numero": "D.A. 4.020", "fecha": "2025-03-05", "titulo": "Ordenanza Local para Pubs, Bares, Restaurantes de Turismo, Cabarets y Discotecas", "url": "https://www.munivalpo.cl/transparencia/"},
    {"comuna": "Viña del Mar", "region_id": "05", "numero": "D.A. 11.932", "fecha": "2025-05-18", "titulo": "Promulgación Modificación Plan Regulador Comunal (Sector Reñaca Norte Costa)", "url": "https://prc.munivina.cl/"},
    {"comuna": "Viña del Mar", "region_id": "05", "numero": "D.A. 13.966", "fecha": "2024-04-15", "titulo": "Ordenanza sobre Instalación de Mobiliario y Terrazas en Bienes Nacionales de Uso Público", "url": "https://www.munivina.cl/"},
    {"comuna": "Viña del Mar", "region_id": "05", "numero": "D.A. 16.296", "fecha": "2023-12-04", "titulo": "Ordenanza Municipal para el Retiro y Custodia de Vehículos Abandonados o Mal Estacionados", "url": "https://www.munivina.cl/"},
    {"comuna": "Quilpué", "region_id": "05", "numero": "D.A. 920", "fecha": "2024-04-10", "titulo": "Ordenanza Local de Protección Ambiental y Gestión Integral de Residuos Domiciliarios", "url": "https://www.quilpue.cl/"},
    {"comuna": "Rancagua", "region_id": "06", "numero": "D.A. Ex. 142", "fecha": "2026-01-12", "titulo": "Ordenanza sobre Expendio y Consumo de Bebidas Alcohólicas y Horarios de Establecimientos Comerciales", "url": "https://www.rancagua.cl/"},
    {"comuna": "Rancagua", "region_id": "06", "numero": "D.A. 2.105", "fecha": "2024-10-30", "titulo": "Ordenanza de Participación Ciudadana y Consejos Consultivos Comunales", "url": "https://www.rancagua.cl/"},
    {"comuna": "Talca", "region_id": "07", "numero": "D.A. 1.480", "fecha": "2024-09-15", "titulo": "Ordenanza sobre Prevención y Sanción de Ruidos Molestos, Fuentes Fijas y Móviles", "url": "https://www.talcatransparente.cl/"},
    {"comuna": "Talca", "region_id": "07", "numero": "D.A. 3.210", "fecha": "2025-01-08", "titulo": "Ordenanza Local sobre Aseo, Ornato y Gestión de Microbasurales", "url": "https://www.talcatransparente.cl/"},
    {"comuna": "Curicó", "region_id": "07", "numero": "D.A. 105", "fecha": "2026-01-22", "titulo": "Ordenanza Reguladora de Terrazas Comerciales y Mobiliario Urbano en BNUP", "url": "https://www.curico.cl/"},
    {"comuna": "Curicó", "region_id": "07", "numero": "D.A. 3.890", "fecha": "2024-11-18", "titulo": "Ordenanza Local de Cobro de Derechos Municipales por Permisos, Servicios y Concesiones (2025)", "url": "https://www.transparenciacurico.cl/"},

    # ZONA SUR Y AUSTRAL (Regiones XVI a XII)
    {"comuna": "Chillán", "region_id": "16", "numero": "Ord. 04-2024", "fecha": "2024-12-18", "titulo": "Ordenanza Local sobre Comercio Estacionado y Ambulante en Bienes Nacionales de Uso Público de Chillán", "url": "https://www.municipalidadchillan.cl/sitio/transparencia/"},
    {"comuna": "Chillán", "region_id": "16", "numero": "D.A. 5.120", "fecha": "2024-06-12", "titulo": "Aprueba Enmienda N° 1-2024 a la Ordenanza Local del Plan Regulador Comunal de Chillán sobre Cierros", "url": "https://www.municipalidadchillan.cl/sitio/transparencia/"},
    {"comuna": "Concepción", "region_id": "08", "numero": "Ord. 06 / D.A. 1.482", "fecha": "2023-11-14", "titulo": "Texto Refundido y Sistematizado de la Ordenanza Local sobre Derechos Municipales por Concesiones", "url": "https://www.concepcion.cl/transparencia/"},
    {"comuna": "Concepción", "region_id": "08", "numero": "D.A. 312-2025", "fecha": "2025-02-10", "titulo": "Promulga Enmienda N° 17 a la Ordenanza Local del Plan Regulador Comunal de Concepción", "url": "https://www.concepcion.cl/transparencia/"},
    {"comuna": "Talcahuano", "region_id": "08", "numero": "D.A. 2.654", "fecha": "2026-06-02", "titulo": "Decreto Alcaldicio que actualiza la Ordenanza sobre Ordenamiento del Comercio en Bienes Nacionales de Uso Público", "url": "https://transparencia.talcahuano.cl/"},
    {"comuna": "San Pedro de la Paz", "region_id": "08", "numero": "Ord. 02 / D.A. 50-CT", "fecha": "2022-10-27", "titulo": "Ordenanza sobre Derechos Municipales por Permisos, Concesiones y Servicios", "url": "https://www.sanpedrodelapaz.cl/transparencia/"},
    {"comuna": "Temuco", "region_id": "09", "numero": "D.A. 4.112 / Ord. 012", "fecha": "2023-08-22", "titulo": "Ordenanza Municipal sobre Prevención y Sanción del Acoso Callejero en Espacios Públicos", "url": "https://transparencia.temuco.cl/ordenanzas/"},
    {"comuna": "Temuco", "region_id": "09", "numero": "D.A. 5.890", "fecha": "2024-11-28", "titulo": "Ordenanza de Derechos Municipales por Concesiones, Permisos y Servicios 2025", "url": "https://transparencia.temuco.cl/ordenanzas/"},
    {"comuna": "Valdivia", "region_id": "14", "numero": "D.A. 2.217", "fecha": "2022-04-18", "titulo": "Ordenanza para la Protección, Conservación y Gestión Integral de los Humedales Urbanos en Valdivia (Ley 21.202)", "url": "https://www.munivaldivia.cl/transparencia/"},
    {"comuna": "Valdivia", "region_id": "14", "numero": "D.A. 6.340", "fecha": "2023-12-15", "titulo": "Ordenanza sobre Protección del Arbolado Urbano, Áreas Verdes y Especies Nativas de Valdivia", "url": "https://www.munivaldivia.cl/transparencia/"},
    {"comuna": "Puerto Montt", "region_id": "10", "numero": "D.A. 2.641", "fecha": "2024-05-10", "titulo": "Ordenanza Municipal N° 0003 sobre Fiscalización y Regulación del Comercio Ambulante", "url": "https://www.puertomontt.cl/transparencia/"},
    {"comuna": "Castro", "region_id": "10", "numero": "D.A. 1.830", "fecha": "2023-09-05", "titulo": "Ordenanza sobre Manejo Integral de Residuos Sólidos Domiciliarios, Reciclaje y Disposición Final", "url": "https://www.castromunicipio.cl/transparencia/"},
    {"comuna": "Coyhaique", "region_id": "11", "numero": "D.A. 3.421", "fecha": "2024-03-20", "titulo": "Ordenanza Reguladora del Funcionamiento de Ferias Libres, Artesanales y Emprendimientos", "url": "https://www.coyhaique.cl/transparencia/"},
    {"comuna": "Punta Arenas", "region_id": "12", "numero": "D.A. 614", "fecha": "2024-04-08", "titulo": "Modificación de la Ordenanza sobre Estacionamientos Controlados y Regulación de Vehículos", "url": "https://www.puntaarenas.cl/ordenanzas/"},
    {"comuna": "Punta Arenas", "region_id": "12", "numero": "D.A. 3.820", "fecha": "2023-11-20", "titulo": "Ordenanza sobre Derechos Municipales por Permisos, Servicios y Concesiones en Punta Arenas", "url": "https://www.puntaarenas.cl/ordenanzas/"},
    {"comuna": "Natales", "region_id": "12", "numero": "D.A. 1.945", "fecha": "2024-08-14", "titulo": "Ordenanza de Protección del Patrimonio Paisajístico, Aseo y Limpieza de Espacios Públicos y Costanera", "url": "https://www.muninatales.cl/transparencia/"}
]

def ingest_all_cplt():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Insertando {len(ALL_CPLT_RECORDS)} ordenanzas CPLT (2022-2026) consolidadas de las 3 macrozonas...")
    inserted = 0

    for r in ALL_CPLT_RECORDS:
        comuna = r["comuna"]
        num = r["numero"]
        fecha = r["fecha"]
        titulo = r["titulo"]
        url = r["url"]
        slug = f"municipalidad-de-{clean_text(comuna).replace(' ', '-')}"
        norma_uri = f"cplt://{slug}/{fecha}/{clean_text(num).replace(' ', '-')}"

        cat = categorize_title(titulo)
        materia_nombre = cat["nombre"]

        cursor.execute("""
            INSERT OR REPLACE INTO ordenanzas 
            (fuente, norma_uri, municipalidad_slug, comuna_nombre, fecha_publicacion, numero, titulo, materia, pdf_url, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("CPLT", norma_uri, slug, comuna, fecha, num, titulo, materia_nombre, url, "VIGENTE_2026"))
        inserted += 1

    conn.commit()
    conn.close()

    # Re-run full dashboard JSON enrichment
    from enrich_all_bcn import run_enrichment
    run_enrichment()

    # Update CPLT count in dashboard JSON
    with open(DASHBOARD_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["metrics"]["ordenanzas_cplt"] = len(ALL_CPLT_RECORDS)
    data["metrics"]["total_ordenanzas"] = data["metrics"]["ordenanzas_bcn"] + len(ALL_CPLT_RECORDS)

    with open(DASHBOARD_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(DASHBOARD_JS, "w", encoding="utf-8") as f:
        f.write("window.CATASTRO_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";")

    print(f"Consolidación exitosa! {inserted} ordenanzas 2022-2026 registradas.")

if __name__ == "__main__":
    ingest_all_cplt()
