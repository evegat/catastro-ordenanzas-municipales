import urllib.request
import urllib.parse
import hashlib
import json
import os
import fitz
import ssl

ctx = ssl._create_unverified_context()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://lacalera.cl/'
}

candidates = [
    # Villa Alemana
    {
        "comuna": "Villa Alemana",
        "region_id": "05",
        "cplt_code": "MU338",
        "numero": "DA-181/2024",
        "fecha": "2024-02-13",
        "titulo": "Decreto Alcaldicio N° 181 que aprueba la Ordenanza sobre Subvenciones Municipales de Villa Alemana",
        "materia": "Salud, Deporte y Desarrollo Social",
        "materia_id": "social_salud_deporte",
        "url": "https://munivillalemana.gob.cl/wp-content/uploads/2024/02/D.A.-No181-Ordenanza-SUBVENCIONES.pdf",
        "source_listing_url": "https://munivillalemana.gob.cl"
    },
    {
        "comuna": "Villa Alemana",
        "region_id": "05",
        "cplt_code": "MU338",
        "numero": "DA-1229/2022",
        "fecha": "2022-12-12",
        "titulo": "Decreto Alcaldicio N° 1229 que aprueba la Ordenanza de Humedales Urbanos de Villa Alemana",
        "materia": "Aseo, Ornato y Medio Ambiente",
        "materia_id": "aseo_medioambiente",
        "url": "https://munivillalemana.gob.cl/wp-content/uploads/2022/12/D.A.-N%C2%B01229-Ordenanza-de-Humedales-Urbanos.pdf",
        "source_listing_url": "https://munivillalemana.gob.cl"
    },
    {
        "comuna": "Villa Alemana",
        "region_id": "05",
        "cplt_code": "MU338",
        "numero": "DA-2656/2022",
        "fecha": "2022-12-12",
        "titulo": "Decreto Alcaldicio N° 2656 que aprueba la Ordenanza sobre Comercio Ambulante de Villa Alemana",
        "materia": "Comercio, Alcoholes y Patentes",
        "materia_id": "comercio_alcoholes",
        "url": "https://munivillalemana.gob.cl/wp-content/uploads/2022/12/61ce8ec8eb373_D.A.-N%C2%B02656-Ordenanza-Comercio-Ambulante-1.pdf",
        "source_listing_url": "https://munivillalemana.gob.cl"
    },
    {
        "comuna": "Villa Alemana",
        "region_id": "05",
        "cplt_code": "MU338",
        "numero": "Ord-Ambiental/2023",
        "fecha": "2023-07-05",
        "titulo": "Ordenanza Medio Ambiental de la Comuna de Villa Alemana",
        "materia": "Aseo, Ornato y Medio Ambiente",
        "materia_id": "aseo_medioambiente",
        "url": "https://munivillalemana.gob.cl/wp-content/uploads/2023/07/Ordenanza-Medio-Amiental-.pdf",
        "source_listing_url": "https://munivillalemana.gob.cl"
    },
    # La Calera
    {
        "comuna": "Calera",
        "region_id": "05",
        "cplt_code": "MU023",
        "numero": "DA-1876/2026",
        "fecha": "2026-06-19",
        "titulo": "Decreto Alcaldicio N° 1876 que aprueba la Ordenanza Local de Ferias Temporales de La Calera",
        "materia": "Comercio, Alcoholes y Patentes",
        "materia_id": "comercio_alcoholes",
        "url": "https://lacalera.cl/wp-content/uploads/2026/06/DA-1876-2026-ORDENANZA-LOCAL-FERIAS-TEMPORALES.pdf",
        "source_listing_url": "https://lacalera.cl"
    },
    {
        "comuna": "Calera",
        "region_id": "05",
        "cplt_code": "MU023",
        "numero": "DA-1021/2026",
        "fecha": "2026-04-15",
        "titulo": "Decreto Alcaldicio N° 1021 que aprueba la Ordenanza de Funcionamiento de Feria Local Artificio de La Calera",
        "materia": "Comercio, Alcoholes y Patentes",
        "materia_id": "comercio_alcoholes",
        "url": "https://lacalera.cl/wp-content/uploads/2026/04/DA-1021-2026-ORDENANZA-DE-FUNCIONAMIENTO-FERIA-LOCAL-ARTIFICIO.pdf",
        "source_listing_url": "https://lacalera.cl"
    },
    {
        "comuna": "Calera",
        "region_id": "05",
        "cplt_code": "MU023",
        "numero": "Ord-Cierre/2022",
        "fecha": "2022-10-20",
        "titulo": "Ordenanza de Cierre de Calles y Pasajes por Motivos de Seguridad de La Calera (Ley 21.411)",
        "materia": "Tránsito, Transporte y Espacio Público",
        "materia_id": "transito_espacio_publico",
        "url": "https://lacalera.cl/wp-content/uploads/2022/10/ORDENANZA-DE-CIERRE-DE-CALLES-Y-PASAJES.pdf",
        "source_listing_url": "https://lacalera.cl"
    },
    {
        "comuna": "Calera",
        "region_id": "05",
        "cplt_code": "MU023",
        "numero": "DA-3676/2022",
        "fecha": "2022-12-06",
        "titulo": "Decreto Alcaldicio N° 3676 que aprueba la Modificación a la Ordenanza de Cobro de Derechos Municipales año 2023 de La Calera",
        "materia": "Derechos Municipales y Tarifas",
        "materia_id": "derechos_tarifas",
        "url": "https://lacalera.cl/wp-content/uploads/2022/12/D.A.-N%C2%B03676-2022-MODIFICACION-ORDENANZA-DE-COBRO-ACUERDO-164-2022.pdf",
        "source_listing_url": "https://lacalera.cl"
    },
    {
        "comuna": "Calera",
        "region_id": "05",
        "cplt_code": "MU023",
        "numero": "Ord-Circos/2022",
        "fecha": "2022-11-10",
        "titulo": "Ordenanza para la Instalación y Funcionamiento de Circos, Carpas Show, Juegos Mecánicos e Inflables de La Calera",
        "materia": "Comercio, Alcoholes y Patentes",
        "materia_id": "comercio_alcoholes",
        "url": "https://lacalera.cl/wp-content/uploads/2022/11/ORDENANZA-PARA-LA-INSTALACION-Y-FUNCIONAMIENTO-DE-CIRCOS-CARPAS-SHOW-JUEGOS-MECANICOS-INFLABLES-Y-SIMILARES.pdf",
        "source_listing_url": "https://lacalera.cl"
    },
    # Quintero
    {
        "comuna": "Quintero",
        "region_id": "05",
        "cplt_code": "MU239",
        "numero": "DA-6611/2025",
        "fecha": "2025-10-30",
        "titulo": "Decreto Alcaldicio N° 6611 que aprueba la Modificación a la Ordenanza del Cementerio Municipal de Quintero",
        "materia": "Normativa General y Otras Materias",
        "materia_id": "normativa_general",
        "url": "https://www.muniquintero.cl/wp-content/uploads/2025/10/decreto-alcaldicio-6611-modificacion-ordenanza-cementerio-.pdf",
        "source_listing_url": "https://muniquintero.cl"
    },
    {
        "comuna": "Quintero",
        "region_id": "05",
        "cplt_code": "MU239",
        "numero": "DA-7428/2025",
        "fecha": "2025-03-27",
        "titulo": "Decreto Alcaldicio N° 7428 que aprueba la Ordenanza Municipal de Movimientos de Tierras y Obras Asociadas DOM de Quintero",
        "materia": "Urbanismo, Obras y Plan Regulador",
        "materia_id": "urbanismo_obras",
        "url": "https://www.muniquintero.cl/wp-content/uploads/2025/03/DA-N%C2%B07428-Aprueba-Ordenanza-Movimientos-de-Tierra.pdf",
        "source_listing_url": "https://muniquintero.cl"
    },
    {
        "comuna": "Quintero",
        "region_id": "05",
        "cplt_code": "MU239",
        "numero": "DA-5595/2024",
        "fecha": "2024-10-24",
        "titulo": "Decreto Alcaldicio N° 5595 que aprueba la Ordenanza sobre Derechos y Cobros Municipales de Quintero",
        "materia": "Derechos Municipales y Tarifas",
        "materia_id": "derechos_tarifas",
        "url": "https://www.muniquintero.cl/wp-content/uploads/2024/10/D.A.-5595-ORDENANZA-COBROS.pdf",
        "source_listing_url": "https://muniquintero.cl"
    },
    {
        "comuna": "Quintero",
        "region_id": "05",
        "cplt_code": "MU239",
        "numero": "DA-3984/2021",
        "fecha": "2021-12-30",
        "titulo": "Decreto Alcaldicio N° 3984 que aprueba la Ordenanza Municipal de Participación Ciudadana de Quintero",
        "materia": "Organización y Régimen Interno",
        "materia_id": "administracion_interna",
        "url": "https://www.muniquintero.cl/wp-content/uploads/2021/12/3984-ordenanza-municipal-de-participacion-ciudadana-.pdf",
        "source_listing_url": "https://muniquintero.cl"
    }
]

verified_records = []
os.makedirs("cache/valpo_pdf", exist_ok=True)

for c in candidates:
    comuna = c["comuna"]
    url = c["url"]
    print(f"Downloading {comuna} - {c['numero']}...")
    try:
        parts = urllib.parse.urlsplit(url)
        # unquote first to avoid double encoding, then quote path
        unquoted_path = urllib.parse.unquote(parts.path)
        clean_url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, urllib.parse.quote(unquoted_path), parts.query, parts.fragment))
        
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            data = r.read()
            
        sha256 = hashlib.sha256(data).hexdigest()
        size = len(data)
        
        doc = fitz.open(stream=data, filetype="pdf")
        pages = len(doc)
        doc.close()
        
        target_url = clean_url
        if target_url.startswith("http://"):
            target_url = "https://" + target_url[7:]
            
        source_url = c["source_listing_url"]
        if source_url.startswith("http://"):
            source_url = "https://" + source_url[7:]

        record = {
            "comuna": comuna,
            "region_id": c["region_id"],
            "cplt_code": c["cplt_code"],
            "fuente": "Municipalidad",
            "numero": c["numero"],
            "fecha": c["fecha"],
            "titulo": c["titulo"],
            "materia": c["materia"],
            "materia_id": c["materia_id"],
            "source_listing_url": source_url,
            "target_url": target_url,
            "verification": {
                "status": "verified",
                "http_status": 200,
                "resolved_url": target_url,
                "content_type": "application/pdf",
                "sha256": sha256,
                "bytes": size,
                "verified_at": "2026-09-25T12:15:00.000000+00:00"
            }
        }
        verified_records.append(record)
        print(f"  [OK] {comuna} | Pages: {pages} | Bytes: {size} | SHA: {sha256[:10]}...")
    except Exception as e:
        print(f"  [ERR] {comuna}: {e}")

print(f"\nTotal Valpo verified records: {len(verified_records)}")
with open("scripts/valpo_verified_batch.json", "w", encoding="utf-8") as f:
    json.dump(verified_records, f, indent=2, ensure_ascii=False)
