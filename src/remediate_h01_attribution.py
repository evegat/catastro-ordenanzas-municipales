"""Remediación H01: Atribución comunal de ordenanzas BCN/LeyChile.
Corrige falsos positivos causados por matching histórico de subcadena.
Task ID: P090-AUD-WEB-20261002
"""

import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
STATUS_DATA_PATH = REPO_ROOT / "dashboard" / "status_data.json"

def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def run_remediation():
    with open(STATUS_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    comunas = data.get("comunas", [])
    comunas_map = {c["comuna"]: c for c in comunas}
    norm_map = {normalize_key(c["comuna"]): c for c in comunas}

    # Definir los pares de subcadena y sus patrones de organismo en rdf_url
    # (comuna_afectada_por_falso_positivo, comuna_real_duena_de_la_norma, patron_slug_real)
    corrections = [
        # (afectada, real, slug_organismo_real)
        ("Talca", "Talcahuano", "municipalidad-de-talcahuano"),
        ("Quillota", "Lota", "municipalidad-de-lota"),
        ("Rauco", "Arauco", "municipalidad-de-arauco"),
        ("Pica", "Chépica", "municipalidad-de-chepica"),
        ("Florida", "La Florida", "municipalidad-de-la-florida"),
        ("Paine", "Torres del Paine", "municipalidad-de-torres-del-paine"),
        ("Calera", "Calera de Tango", "municipalidad-de-calera-de-tango"),
        ("Pinto", "María Pinto", "municipalidad-de-maria-pinto"),
        ("El Carmen", "Alto del Carmen", "municipalidad-de-alto-del-carmen"),
        ("Chillán", "Chillán Viejo", "municipalidad-de-chillan-viejo"),
        ("San Pedro", "San Pedro de Atacama", "municipalidad-de-san-pedro-de-atacama"),
        ("San Pedro", "San Pedro de la Paz", "municipalidad-de-san-pedro-de-la-paz"),
        # Casos inversos (la norma de la comuna corta fue metida en la larga)
        ("Torres del Paine", "Paine", "municipalidad-de-paine"),
        ("La Florida", "Florida", "municipalidad-de-florida"),
        ("Alto del Carmen", "El Carmen", "municipalidad-de-el-carmen"),
        ("Chépica", "Pica", "municipalidad-de-pica"),
        ("Chillán Viejo", "Chillán", "municipalidad-de-chillan"),
    ]

    total_removed = 0
    total_reassigned = 0
    details = []

    for afectada_name, real_name, slug_real in corrections:
        c_afectada = norm_map.get(normalize_key(afectada_name))
        c_real = norm_map.get(normalize_key(real_name))
        
        if not c_afectada or not c_real:
            print(f"Advertencia: no se encontró {afectada_name} o {real_name}")
            continue

        kept_afectada = []
        moved_to_real = []

        real_existing_rdfs = {o.get("rdf_url") for o in c_real.get("ordenanzas", []) if o.get("rdf_url")}
        real_existing_targets = {o.get("target_url") for o in c_real.get("ordenanzas", []) if o.get("target_url")}

        for ord_ in c_afectada.get("ordenanzas", []):
            rdf = (ord_.get("rdf_url") or "").lower()
            tit = (ord_.get("titulo") or "").lower()

            # Si la norma pertenece claramente al slug del organismo real
            if slug_real in rdf or (slug_real.replace("-", " ") in tit and "municipalidad" in tit):
                moved_to_real.append(ord_)
                total_removed += 1
                
                # Verificar si ya existe en la comuna real
                rdf_url = ord_.get("rdf_url")
                target_url = ord_.get("target_url")
                already_in_real = (rdf_url and rdf_url in real_existing_rdfs) or (target_url and target_url in real_existing_targets)
                
                if not already_in_real:
                    c_real.setdefault("ordenanzas", []).append(ord_)
                    total_reassigned += 1
            else:
                kept_afectada.append(ord_)

        c_afectada["ordenanzas"] = kept_afectada
        if moved_to_real:
            details.append({
                "afectada": c_afectada["comuna"],
                "real": c_real["comuna"],
                "removidas_de_afectada": len(moved_to_real),
                "agregadas_a_real": total_reassigned
            })

    # Etiquetar casos legítimos compartidos
    # 1. Pirque y Puente Alto (Río Maipo)
    pirque = norm_map.get("pirque")
    puente_alto = norm_map.get("puente alto")
    if pirque and puente_alto:
        for ord_ in pirque.get("ordenanzas", []):
            if "maipo" in (ord_.get("titulo") or "").lower():
                ord_["co_emision"] = True
                ord_["nota_jurisdiccional"] = "Ordenanza conjunta Cuenca Río Maipo (Pirque - Puente Alto)"
        for ord_ in puente_alto.get("ordenanzas", []):
            if "maipo" in (ord_.get("titulo") or "").lower():
                ord_["co_emision"] = True
                ord_["nota_jurisdiccional"] = "Ordenanza conjunta Cuenca Río Maipo (Pirque - Puente Alto)"

    # 2. Cabo de Hornos y Antártica
    antartica = norm_map.get("antartica")
    cabo_hornos = norm_map.get("cabo de hornos")
    if antartica and cabo_hornos:
        for ord_ in antartica.get("ordenanzas", []):
            ord_["administracion_agrupada"] = True
            ord_["nota_jurisdiccional"] = "I. Municipalidad de Cabo de Hornos (Administración agrupada Cabo de Hornos y Antártica)"
        for ord_ in cabo_hornos.get("ordenanzas", []):
            ord_["administracion_agrupada"] = True
            ord_["nota_jurisdiccional"] = "I. Municipalidad de Cabo de Hornos (Administración agrupada Cabo de Hornos y Antártica)"

    # Guardar status_data.json actualizado
    with open(STATUS_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"H01 Remediación completada:")
    print(f"  - Total normas removidas de comunas erróneas: {total_removed}")
    print(f"  - Total normas transferidas/aseguradas en comuna correcta: {total_reassigned}")
    for d in details:
        print(f"    * {d['afectada']} -> {d['real']}: {d['removidas_de_afectada']} removidas")

if __name__ == "__main__":
    run_remediation()
