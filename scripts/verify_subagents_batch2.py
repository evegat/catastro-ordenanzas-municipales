import os
import sys
import json
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

NEW_CANDIDATES = [
    {
        "comuna": "Ovalle",
        "region_id": "04",
        "cplt_code": "MU194",
        "tipo_norma": "Ordenanza",
        "numero": "Decreto Exento 4898",
        "fecha": "2021-06-30",
        "titulo": "Ordenanza sobre Uso de Espacios Públicos en la Comuna de Ovalle",
        "materia": "Seguridad y Convivencia",
        "materia_id": "seguridad_convivencia",
        "target_url": "https://muniovalle.gob.cl/documentos/07Terceros/Decretos/2021/junio/4898.pdf", # probaremos con https y http
        "target_url_fallback": "http://transparenciaovalle.cl/documentos/07Terceros/Decretos/2021/junio/4898.pdf",
        "source_listing_url": "https://muniovalle.gob.cl/documentos/"
    },
    {
        "comuna": "Vallenar",
        "region_id": "03",
        "cplt_code": "MU331",
        "tipo_norma": "Ordenanza",
        "numero": "Enmienda 002 PRCV",
        "fecha": "2026-09-25",
        "titulo": "Ordenanza Enmienda N° 002 Plan Regulador Comunal de Vallenar - Clasificación Vialidad Estructurante",
        "materia": "Urbanismo, Obras y Edificación",
        "materia_id": "urbanismo_obras",
        "target_url": "https://www.imvallenar.gob.cl/wp-content/uploads/2026/09/20260925-ORDENANZA-ENMIENDA-02-PRCV-VIALIDAD-ESTRUCTURANTE.pdf",
        "source_listing_url": "https://www.imvallenar.gob.cl/enmienda-02-al-prcv/"
    },
    {
        "comuna": "San Carlos",
        "region_id": "16",
        "cplt_code": "MU283",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2024-11-07",
        "titulo": "Ordenanza Local del Plan Regulador Comunal de San Carlos",
        "materia": "Urbanismo, Obras y Edificación",
        "materia_id": "urbanismo_obras",
        "target_url": "https://munisancarlos.cl/wp-content/uploads/2025/08/02-PRC-OrdenanzaDiarioOficial.pdf.pdf",
        "source_listing_url": "https://munisancarlos.cl/normativayplanes/"
    },
    {
        "comuna": "Lota",
        "region_id": "08",
        "cplt_code": "MU149",
        "tipo_norma": "Ordenanza",
        "numero": "3",
        "fecha": "2025-11-13",
        "titulo": "Ordenanza sobre Otorgamiento de Subvenciones, Recepción de Donaciones y su Registro de Lota",
        "materia": "Salud, Deporte y Desarrollo Social",
        "materia_id": "social_salud_deporte",
        "target_url": "https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=Ordenanza-3_13-NOV-2025&exportar_con_notas_bcn=False&exportar_con_notas_originales=False&exportar_con_notas_al_pie=False&hddResultadoExportar=1218454.2025-11-13.0.0%23",
        "source_listing_url": "https://www.bcn.cl/leychile/Navegar?idNorma=1218454"
    },
    {
        "comuna": "Ancud",
        "region_id": "10",
        "cplt_code": "MU006",
        "tipo_norma": "Ordenanza",
        "numero": "Decreto 242",
        "fecha": "2025-01-21",
        "titulo": "Texto Refundido y Sistematizado de la Ordenanza Municipal N° 14 sobre Tenencia Responsable de Mascotas y Animales de Compañía",
        "materia": "Tenencia Responsable y Mascotas",
        "materia_id": "tenencia_mascotas",
        "target_url": "https://muniancud.cl/transparencia/municipalidad/archivo/estandares/08%20Actos%20y%20Resoluciones/8.3%20Ordenanzas/ORDENANZAS/ORDENANZA%2014.pdf",
        "source_listing_url": "https://www.muniancud.cl/transparencia/municipalidad/inicio/index.php"
    },
    {
        "comuna": "La Unión",
        "region_id": "14",
        "cplt_code": "MU125",
        "tipo_norma": "Ordenanza",
        "numero": "5",
        "fecha": "2022-11-04",
        "titulo": "Ordenanza Nro. 05 Aprueba Ordenanza Local sobre Ferias Libres de la Comuna de La Unión",
        "materia": "Comercio, Alcoholes y Patentes",
        "materia_id": "comercio_alcoholes",
        "target_url": "https://transparencia.munilaunion.cl/Documentos/ActosResoluciones/928445Ordenanza%20Nro.%2005%20Aprueba%20Ordenanza%20Local%20sobre%20Ferias%20Libres.pdf",
        "source_listing_url": "https://transparencia.munilaunion.cl/"
    },
    {
        "comuna": "Vicuña",
        "region_id": "04",
        "cplt_code": "MU336",
        "tipo_norma": "Ordenanza",
        "numero": "S/N",
        "fecha": "2025-07-02",
        "titulo": "Ordenanza Municipal sobre Otorgamiento de Subvenciones de la Municipalidad de Vicuña",
        "materia": "Salud, Deporte y Desarrollo Social",
        "materia_id": "social_salud_deporte",
        "target_url": "https://munivicuna.cl/download/ordenanza-subvenciones-vigente-2025/?wpdmdl=910",
        "source_listing_url": "https://munivicuna.cl/download/ordenanza-subvenciones-vigente-2025/"
    },
    {
        "comuna": "Los Vilos",
        "region_id": "04",
        "cplt_code": "MU151",
        "tipo_norma": "Ordenanza",
        "numero": "Decreto 1164",
        "fecha": "2024-06-05",
        "titulo": "Ordenanza sobre Actividades Ruidosas y Fuentes Emisoras de Ruido de la Comuna de Los Vilos",
        "materia": "Aseo, Ornato y Medio Ambiente",
        "materia_id": "aseo_medioambiente",
        "target_url": "https://www.munilosvilos.cl/wp-content/uploads/2024/06/decretos1164.pdf",
        "source_listing_url": "https://www.munilosvilos.cl/"
    }
]

def verify(cand):
    urls_to_try = [cand["target_url"]]
    if "target_url_fallback" in cand:
        urls_to_try.append(cand["target_url_fallback"])
        
    for url in urls_to_try:
        # Enforce HTTPS si se puede o probar http si el servidor no tiene SSL
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                status = resp.status
                content = resp.read()
                size = len(content)
                sha256 = hashlib.sha256(content).hexdigest()
                print(f"[OK] {cand['comuna']}: HTTP {status}, {size:,} bytes, SHA256={sha256[:12]}...")
                # Note: build_public_snapshot exige target_url con https://
                # si url empieza con http:// intentemos normalizar a https:// si responde, o si no usar mirror
                final_target = url if url.startswith("https://") else f"https://{url[7:]}"
                return {
                    **cand,
                    "target_url": final_target if final_target.startswith("https://") else url,
                    "verified": True,
                    "http_status": status,
                    "sha256": sha256,
                    "size_bytes": size,
                    "verified_at": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"[RETRY/FAIL] {cand['comuna']} en {url[:45]}: {e}")
            
    return None

def main():
    verified_results = []
    for cand in NEW_CANDIDATES:
        res = verify(cand)
        if res:
            verified_results.append(res)
            
    print(f"\nTotal verificados exitosamente: {len(verified_results)} de {len(NEW_CANDIDATES)}")
    
    with open("data/subagent_verified_batch2.json", "w", encoding="utf-8") as f:
        json.dump(verified_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
