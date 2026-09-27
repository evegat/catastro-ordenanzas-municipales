import os
import sys
import json
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

# UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

CANDIDATES = [
    # Pedro Aguirre Cerda (RM)
    {
        "comuna": "Pedro Aguirre Cerda",
        "region_id": "13",
        "cplt_code": "MU197",
        "tipo_norma": "Ordenanza",
        "numero": "4751",
        "fecha": "2025-08-22",
        "fecha_diario_oficial": "2025-08-29",
        "titulo": "Aprueba Ordenanza Local sobre Derechos Municipales por Concesiones, Permisos y Servicios de Pedro Aguirre Cerda",
        "materia": "Derechos Municipales, permisos y tarifas comunales",
        "materia_id": "derechos_municipales",
        "target_url": "https://www.diariooficial.interior.gob.cl/publicaciones/2025/08/29/43936/01/2692113.pdf",
        "source_listing_url": "https://www.diariooficial.interior.gob.cl/edicionelectronica/empresas_cve.php?date=29-08-2025&edition=43936"
    },
    # El Bosque (RM)
    {
        "comuna": "El Bosque",
        "region_id": "13",
        "cplt_code": "MU080",
        "tipo_norma": "Ordenanza",
        "numero": "126",
        "fecha": "2026-01-09",
        "fecha_diario_oficial": "2026-01-27",
        "titulo": "Modifica Ordenanza de Derechos Municipales por Concesiones, Permisos y Servicios para la Comuna de El Bosque",
        "materia": "Derechos Municipales y permisos comunales",
        "materia_id": "derechos_municipales",
        "target_url": "https://www.diariooficial.interior.gob.cl/publicaciones/2026/01/27/44061/01/2755442.pdf",
        "source_listing_url": "https://www.diariooficial.interior.gob.cl/edicionelectronica/empresas_cve.php?date=27-01-2026&edition=44061"
    },
    # Quinta Normal (RM)
    {
        "comuna": "Quinta Normal",
        "region_id": "13",
        "cplt_code": "MU246",
        "tipo_norma": "Ordenanza",
        "numero": "1708",
        "fecha": "2026-09-03",
        "fecha_diario_oficial": "2026-09-14",
        "titulo": "Aprueba Ordenanza sobre Cierre de Calles y Pasajes por Motivos de Seguridad en la Comuna de Quinta Normal",
        "materia": "Seguridad ciudadana y cierre de calles y pasajes",
        "materia_id": "seguridad_ciudadana",
        "target_url": "https://nuevo.leychile.cl/servicios/Consulta/Exportar?opt=1&idNorma=1228087",
        "source_listing_url": "https://nuevo.leychile.cl/navegar?idNorma=1228087"
    },
    # Ancud (Los Lagos)
    {
        "comuna": "Ancud",
        "region_id": "10",
        "cplt_code": "MU006",
        "tipo_norma": "Ordenanza",
        "numero": "1298",
        "fecha": "2025-05-06",
        "titulo": "Ordenanza Municipal de Derechos y Concesiones de la Comuna de Ancud",
        "materia": "Derechos Municipales y concesiones comunales",
        "materia_id": "derechos_municipales",
        "target_url": "https://www.muniancud.cl/transparencia/archivos/ordenanza1298_2025.pdf",
        "source_listing_url": "https://www.muniancud.cl/transparencia/ordenanzas.php"
    },
    # Puerto Varas (Los Lagos)
    {
        "comuna": "Puerto Varas",
        "region_id": "10",
        "cplt_code": "MU237",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2023-08-15",
        "titulo": "Ordenanza Municipal de Protección de Humedales Urbanos de Puerto Varas",
        "materia": "Medio ambiente, protección de humedales urbanos y biodiversidad",
        "materia_id": "medio_ambiente",
        "target_url": "https://ptovaras.cl/ordenanzas-municipales/ORDENANZA%20DE%20PROTECCI%C3%93N%20DE%20HUMEDALES%20URBANOS%20-%20PUERTO%20VARAS%20%281%29.pdf",
        "source_listing_url": "https://ptovaras.cl/ordenanzas-municipales/"
    },
    # Lebu (Biobío)
    {
        "comuna": "Lebu",
        "region_id": "08",
        "cplt_code": "MU128",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2026-01-15",
        "titulo": "Ordenanza Local de Derechos Municipales por Permisos, Concesiones y Servicios de Lebu",
        "materia": "Derechos Municipales y cobro de tarifas",
        "materia_id": "derechos_municipales",
        "target_url": "https://lebu.cl/wp-content/uploads/2026/01/ORDENANZA-DERECHOS-MUNIC.pdf",
        "source_listing_url": "https://lebu.cl/ordenanzas/"
    },
    # Vallenar (Atacama)
    {
        "comuna": "Vallenar",
        "region_id": "03",
        "cplt_code": "MU331",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2026-03-10",
        "titulo": "Ordenanza Municipal sobre Funcionamiento y Administración de Cementerios Municipales de Vallenar",
        "materia": "Salud pública, higiene y cementerios",
        "materia_id": "salud_e_higiene",
        "target_url": "https://www.imvallenar.gob.cl/wp-content/uploads/2026/03/Ordenanza-Cementerio-Vallenar.pdf",
        "source_listing_url": "https://www.imvallenar.gob.cl/ordenanzas/"
    },
    # Molina (Maule)
    {
        "comuna": "Molina",
        "region_id": "07",
        "cplt_code": "MU176",
        "tipo_norma": "Ordenanza",
        "numero": "11",
        "fecha": "2025-06-18",
        "titulo": "Ordenanza Municipal N° 11 sobre Otorgamiento de Subvenciones Municipales de Molina",
        "materia": "Subvenciones, aportes y fomento comunitario",
        "materia_id": "desarrollo_social",
        "target_url": "https://web.molina.cl/wp-content/uploads/2025/06/ORDENANZA-N11-SUBVENCIONES-2-7-1.pdf",
        "source_listing_url": "https://web.molina.cl/subvenciones/"
    },
    # Cañete (Biobío)
    {
        "comuna": "Cañete",
        "region_id": "08",
        "cplt_code": "MU034",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2022-08-10",
        "titulo": "Ordenanza Municipal sobre Tenencia Responsable de Mascotas y Animales de Compañía de Cañete",
        "materia": "Tenencia responsable de mascotas y bienestar animal",
        "materia_id": "tenencia_responsable_mascotas",
        "target_url": "https://www.municanete.cl/TRANSPARENCIA2022/Agosto2022/terceros/ordenanzas/Ordenanza_Mascotas_y_Animales_de_Compa%C3%B1ia.pdf",
        "source_listing_url": "https://www.municanete.cl/transparencia/"
    }
]

def verify_and_download(cand):
    url = cand["target_url"]
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            content = resp.read()
            size = len(content)
            sha256 = hashlib.sha256(content).hexdigest()
            print(f"[OK] {cand['comuna']}: HTTP {status}, {size:,} bytes, SHA256={sha256[:12]}...")
            return {
                **cand,
                "verified": True,
                "http_status": status,
                "sha256": sha256,
                "size_bytes": size,
                "verified_at": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"[FAIL] {cand['comuna']}: {e}")
        return None

def main():
    verified_results = []
    for cand in CANDIDATES:
        res = verify_and_download(cand)
        if res:
            verified_results.append(res)
    
    print(f"\nTotal verificados exitosamente: {len(verified_results)} de {len(CANDIDATES)}")
    
    with open("data/subagent_verified_batch.json", "w", encoding="utf-8") as f:
        json.dump(verified_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
