# -*- coding: utf-8 -*-
import hashlib, json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
VERIFIED_PATH = DATA_DIR / "municipal_verified_records.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

raw_records = [
  {
    "comuna": "Limache",
    "region_id": "05",
    "fuente": "Municipalidad",
    "numero": "5241/2023",
    "fecha": "2023-12-29",
    "titulo": "Ordenanza Municipal de Prevención y Gestión de Riesgo Comunal por Incendios Forestales",
    "materia": "Aseo, Ornato y Medio Ambiente",
    "materia_id": "aseo_medioambiente",
    "source_listing_url": "https://limache.cl/wp-content/uploads/2024/04/ordenanza_municipal_incendio_forestales.pdf",
    "target_url": "https://limache.cl/wp-content/uploads/2024/04/ordenanza_municipal_incendio_forestales.pdf"
  },
  {
    "comuna": "Limache",
    "region_id": "05",
    "fuente": "Municipalidad",
    "numero": "PRC-2025",
    "fecha": "2025-01-01",
    "titulo": "Ordenanza Local del Plan Regulador Comunal de Limache",
    "materia": "Urbanismo, Obras y Edificación",
    "materia_id": "urbanismo_obras",
    "source_listing_url": "https://limache.cl/wp-content/uploads/2025/05/ORDENANZA_PRC_LIMACHE_VC_CGR2-2.pdf",
    "target_url": "https://limache.cl/wp-content/uploads/2025/05/ORDENANZA_PRC_LIMACHE_VC_CGR2-2.pdf"
  },
  {
    "comuna": "Olmué",
    "region_id": "05",
    "fuente": "Municipalidad",
    "numero": "67",
    "fecha": "1983-05-24",
    "titulo": "Ordenanza Local del Plan Regulador Comunal de Olmué",
    "materia": "Urbanismo, Obras y Edificación",
    "materia_id": "urbanismo_obras",
    "source_listing_url": "https://www.muniolmue.cl/descargasMuni/doc/OrdenanzaPlanReguladoractual.pdf",
    "target_url": "https://www.muniolmue.cl/descargasMuni/doc/OrdenanzaPlanReguladoractual.pdf"
  },
  {
    "comuna": "Maule",
    "region_id": "07",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza sobre extracción de áridos en la comuna de Maule",
    "materia": "Urbanismo, Obras y Edificación",
    "materia_id": "urbanismo_obras",
    "source_listing_url": "https://www.comunademaule.cl/home/documentos/Ordenanza%20de%20aridos%20comuna%20de%20Maule.pdf",
    "target_url": "https://www.comunademaule.cl/home/documentos/Ordenanza%20de%20aridos%20comuna%20de%20Maule.pdf"
  },
  {
    "comuna": "Maule",
    "region_id": "07",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza sobre Diseño y Construcción del Espacio Público en la comuna de Maule",
    "materia": "Urbanismo, Obras y Edificación",
    "materia_id": "urbanismo_obras",
    "source_listing_url": "https://www.comunademaule.cl/home/documentos/Ordenanza%20Dise%C3%B1o%20y%20Construccion%20del%20Espacio%20Publico.pdf",
    "target_url": "https://www.comunademaule.cl/home/documentos/Ordenanza%20Dise%C3%B1o%20y%20Construccion%20del%20Espacio%20Publico.pdf"
  },
  {
    "comuna": "Pelluhue",
    "region_id": "07",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2016-01-01",
    "titulo": "Ordenanza sobre manejo de desechos en la comuna de Pelluhue",
    "materia": "Aseo, Ornato y Medio Ambiente",
    "materia_id": "aseo_medioambiente",
    "source_listing_url": "https://www.munipelluhue.cl/transparencia/2016/ordenanzas_desechos.pdf",
    "target_url": "https://www.munipelluhue.cl/transparencia/2016/ordenanzas_desechos.pdf"
  },
  {
    "comuna": "Pelluhue",
    "region_id": "07",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2014-01-01",
    "titulo": "Modificación de ordenanza que prohíbe conductas o actividades determinadas en Pelluhue",
    "materia": "Seguridad Ciudadana y Convivencia",
    "materia_id": "seguridad_convivencia",
    "source_listing_url": "https://munipelluhue.cl/transparencia/2014/mod.ord.prohibe.pdf",
    "target_url": "https://munipelluhue.cl/transparencia/2014/mod.ord.prohibe.pdf"
  },
  {
    "comuna": "Quirihue",
    "region_id": "16",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2023-01-01",
    "titulo": "Ordenanza Municipal de Prevención y Gestión de Riesgos Comunales Producto de Incendios Forestales",
    "materia": "Aseo, Ornato y Medio Ambiente",
    "materia_id": "aseo_medioambiente",
    "source_listing_url": "https://www.muniquirihue.cl/trans_activa/tranpa/docu2023/Ord_%20Prev_Inc_For.pdf",
    "target_url": "https://www.muniquirihue.cl/trans_activa/tranpa/docu2023/Ord_%20Prev_Inc_For.pdf"
  },
  {
    "comuna": "Quirihue",
    "region_id": "16",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza Municipal de Participación Ciudadana de la comuna de Quirihue",
    "materia": "Participación Ciudadana",
    "materia_id": "participacion_ciudadana",
    "source_listing_url": "https://www.muniquirihue.cl/trans_activa/tranpa/docu2024/saubsa/ORDENANZA%20PARTICIPACION%20CIUDADANA.pdf",
    "target_url": "https://www.muniquirihue.cl/trans_activa/tranpa/docu2024/saubsa/ORDENANZA%20PARTICIPACION%20CIUDADANA.pdf"
  },
  {
    "comuna": "Ñiquén",
    "region_id": "16",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza Local del Plan Regulador Comunal de Ñiquén",
    "materia": "Urbanismo, Obras y Edificación",
    "materia_id": "urbanismo_obras",
    "source_listing_url": "https://www.muniniquen.cl/images/zoom/transparente/anexos/secplan/ORDENANZA.pdf",
    "target_url": "https://www.muniniquen.cl/images/zoom/transparente/anexos/secplan/ORDENANZA.pdf"
  },
  {
    "comuna": "Ñiquén",
    "region_id": "16",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2025-03-01",
    "titulo": "Ordenanza Municipal de Prevención y Gestión de Riesgos por Incendios Forestales en Ñiquén",
    "materia": "Aseo, Ornato y Medio Ambiente",
    "materia_id": "aseo_medioambiente",
    "source_listing_url": "https://www.muniniquen.cl/images/descargas/Archivos_transparencia/Ordenanzas_Municipales_2025/Marzo/ORDENANZA%20MUNICIPAL%20DE%20PREVENCION%20Y%20GESTION%20DE%20RIESGOS%20POR%20ACCION%20DE%20INCENDIOS%20FORESTALES.pdf",
    "target_url": "https://www.muniniquen.cl/images/descargas/Archivos_transparencia/Ordenanzas_Municipales_2025/Marzo/ORDENANZA%20MUNICIPAL%20DE%20PREVENCION%20Y%20GESTION%20DE%20RIESGOS%20POR%20ACCION%20DE%20INCENDIOS%20FORESTALES.pdf"
  },
  {
    "comuna": "Ñiquén",
    "region_id": "16",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2021-01-01",
    "titulo": "Ordenanza de Cobros y Valores de la comuna de Ñiquén",
    "materia": "Derechos Municipales y Tarifas",
    "materia_id": "derechos_tarifas",
    "source_listing_url": "https://www.muniniquen.cl/images/descargas/Archivos_transparencia/Ordenanzas_Municipales_2019/2021/ORDENANZADECOBROSYVALORESDENIQUEN.pdf",
    "target_url": "https://www.muniniquen.cl/images/descargas/Archivos_transparencia/Ordenanzas_Municipales_2019/2021/ORDENANZADECOBROSYVALORESDENIQUEN.pdf"
  },
  {
    "comuna": "Mulchén",
    "region_id": "08",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza de Participación Ciudadana de la comuna de Mulchén",
    "materia": "Participación Ciudadana",
    "materia_id": "participacion_ciudadana",
    "source_listing_url": "https://www.munimulchen.cl/transparencia/1_7_actos_y_resoluciones/ordenanzas/ordenanza_participacion_ciudadana.pdf",
    "target_url": "https://www.munimulchen.cl/transparencia/1_7_actos_y_resoluciones/ordenanzas/ordenanza_participacion_ciudadana.pdf"
  },
  {
    "comuna": "Nacimiento",
    "region_id": "08",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza que crea beca para deportistas destacados de la comuna de Nacimiento",
    "materia": "Salud, Deporte y Desarrollo Social",
    "materia_id": "social_salud_deporte",
    "source_listing_url": "https://ligup-v2.s3.amazonaws.com/nacimiento/accountability/51219_ordenanza_beca_deportistas_destacados.pdf",
    "target_url": "https://ligup-v2.s3.amazonaws.com/nacimiento/accountability/51219_ordenanza_beca_deportistas_destacados.pdf"
  },
  {
    "comuna": "Cunco",
    "region_id": "09",
    "fuente": "Municipalidad",
    "numero": "03",
    "fecha": "2019-10-30",
    "titulo": "Ordenanza N° 03 que fija texto refundido de la Ordenanza Municipal de Desarrollo Turístico y Derechos Municipales",
    "materia": "Derechos Municipales y Tarifas",
    "materia_id": "derechos_tarifas",
    "source_listing_url": "https://www.municunco.cl/transparencia/2/ordenanza%203%202020.pdf",
    "target_url": "https://www.municunco.cl/transparencia/2/ordenanza%203%202020.pdf"
  },
  {
    "comuna": "Cunco",
    "region_id": "09",
    "fuente": "Municipalidad",
    "numero": "006",
    "fecha": "2016-12-28",
    "titulo": "Ordenanza N° 006 de Desarrollo Turístico Sustentable y Derechos Municipales",
    "materia": "Derechos Municipales y Tarifas",
    "materia_id": "derechos_tarifas",
    "source_listing_url": "https://www.municunco.cl/pdfs/ordenanza%20municipal%20cunco.pdf",
    "target_url": "https://www.municunco.cl/pdfs/ordenanza%20municipal%20cunco.pdf"
  },
  {
    "comuna": "Pitrufquén",
    "region_id": "09",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza Municipal sobre expendio y funcionamiento de establecimientos de bebidas alcohólicas en Pitrufquén",
    "materia": "Patentes, Comercio y Alcoholes",
    "materia_id": "alcoholes_comercio",
    "source_listing_url": "https://www.mpitrufquen.cl/Transparencia/Documentos/Reglamentos/Ordenanza%20de%20Alcoholes.pdf",
    "target_url": "https://www.mpitrufquen.cl/Transparencia/Documentos/Reglamentos/Ordenanza%20de%20Alcoholes.pdf"
  },
  {
    "comuna": "Pitrufquén",
    "region_id": "09",
    "fuente": "Municipalidad",
    "numero": "S/N",
    "fecha": "2024-01-01",
    "titulo": "Ordenanza sobre Tenencia Responsable de Mascotas y Animales de Compañía de la comuna de Pitrufquén",
    "materia": "Tenencia Responsable de Mascotas",
    "materia_id": "tenencia_mascotas",
    "source_listing_url": "https://www.mpitrufquen.cl/Transparencia/Documentos/Reglamentos/Ordenanza%20de%20Tenencia%20Responsable%20de%20Mascotas.pdf",
    "target_url": "https://www.mpitrufquen.cl/Transparencia/Documentos/Reglamentos/Ordenanza%20de%20Tenencia%20Responsable%20de%20Mascotas.pdf"
  }
]

def normalize_text(v: str) -> str:
    v = unicodedata.normalize("NFKC", str(v or ""))
    v = re.sub(r'\[page:\d+\]', '', v)
    return re.sub(r"\s+", " ", v).strip()

def ascii_key(v: str) -> str:
    v = unicodedata.normalize("NFKD", normalize_text(v))
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", v.lower()).strip()

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

verified_data = json.loads(VERIFIED_PATH.read_text(encoding="utf-8"))
records = verified_data.get("records", [])
seen_hashes = {r.get("verification", {}).get("sha256") for r in records if r.get("verification", {}).get("sha256")}

added = 0
for r in raw_records:
    comuna = r.get("comuna")
    target_url = (r.get("target_url") or "").replace("http://", "https://")
    src_url = (r.get("source_listing_url") or "").replace("http://", "https://")
    
    try:
        resp = session.get(target_url, timeout=12, stream=True, verify=False)
        if resp.status_code == 200:
            hasher = hashlib.sha256()
            total_b = 0
            header_checked = False
            for chunk in resp.iter_content(chunk_size=65536):
                if not header_checked:
                    if not chunk.startswith(b"%PDF-"):
                        break
                    header_checked = True
                hasher.update(chunk)
                total_b += len(chunk)
                if total_b > 40 * 1024 * 1024:
                    break
            if header_checked and total_b > 500:
                sha = hasher.hexdigest()
                if sha not in seen_hashes:
                    doc = {
                        "comuna": comuna,
                        "region_id": str(r.get("region_id", "13")).zfill(2),
                        "cplt_code": f"MU_{ascii_key(comuna)}",
                        "fuente": r.get("fuente", "Municipalidad"),
                        "numero": str(r.get("numero") or "S/N"),
                        "fecha": str(r.get("fecha") or "2024-01-01"),
                        "titulo": normalize_text(r.get("titulo", f"Ordenanza Municipal {comuna}")),
                        "materia": r.get("materia", "Normativa General"),
                        "materia_id": r.get("materia_id", "general"),
                        "source_listing_url": src_url or target_url,
                        "target_url": target_url,
                        "verification": {
                            "status": "verified",
                            "http_status": 200,
                            "resolved_url": target_url,
                            "content_type": "application/pdf",
                            "sha256": sha,
                            "bytes": total_b,
                            "verified_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                    records.append(doc)
                    seen_hashes.add(sha)
                    added += 1
                    print(f"[{comuna}] +1 ordenanza verificada con SHA-256: {doc['titulo'][:45]}")
    except Exception as e:
        print(f"Error descargando {target_url}: {e}")

print(f"Total nuevas ordenanzas agregadas con SHA-256: {added}")
verified_data["records"] = records
verified_data["count"] = len(records)
verified_data["generated_at"] = datetime.now(timezone.utc).isoformat()
VERIFIED_PATH.write_text(json.dumps(verified_data, ensure_ascii=False, indent=2), encoding="utf-8")