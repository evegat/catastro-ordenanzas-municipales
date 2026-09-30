#!/usr/bin/env python3
"""
revisar_con_jev_linkedin.py
Auditoría y Juicio Semántico de TypeSafe Jev (System 1 RLCD) para el lanzamiento
y publicación en LinkedIn del Catastro Nacional de Ordenanzas Municipales (P090).
"""

import json
import time
from pathlib import Path

# Cargar API Key
key_path = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P129 - Typesafe ai Jev Acess First meeting\claves.txt")
api_key = key_path.read_text(encoding="utf-8").strip()

import typesafe_sdk
client = typesafe_sdk.TypeSafeClient(api_key=api_key)

# Contexto completo de la publicación y del producto
post_propuesto = """¿Sabías que en Chile no existe un solo repositorio oficial donde puedas consultar y comparar las ordenanzas de los 346 municipios?

En mis años en el sector público y haciendo clases en la U. de Chile siempre vi la misma fricción: la normativa local está completamente dispersa. Cada municipio publica donde puede, en formatos incompatibles, y cuando cambia una administración muchas veces los registros se pierden o desordenan.

Para enfrentar esa asimetría de información, crucé los registros de la Biblioteca del Congreso Nacional (BCN) y portales municipales para levantar un Catastro Nacional de Ordenanzas Municipales abierto y verificable:

📌 7.462 normas catalogadas (5.881 de BCN LeyChile + 1.581 de portales comunales verificadas documentalmente con hash SHA-256).  
📌 346 comunas cubiertas con trazabilidad de su brecha temporal.  
📌 Auditor de materias clave y de alta demanda vecinal (Derechos Municipales, Aseo, Tenencia de Mascotas, Participación Ciudadana y Convivencia).  
📌 Asistente normativo local que opera 100% en tu navegador (sin costo ni fuga de datos).  
📌 Datos abiertos en CSV y notebook didáctico en Python para docencia e investigación aplicada.  

Pongo esta herramienta al servicio de concejales, administradores públicos, académicos y tesistas:

🔗 https://ordenanzas.evegat.cl

El catastro es colaborativo: si en tu comuna falta alguna norma vigente, puedes sumarla directo al buzón para seguir cerrando la brecha.

#GestionPublica #Municipalidades #GovTech #DatosAbiertos #Transparencia #Chile #FAGOB"""

estado_evaluacion = {
    "autor": "Eduardo Vega Toledo (Docente FAGOB U. de Chile, ex-profesional SUBDERE)",
    "red_social": "LinkedIn (Audiencia: municipalistas, directores de control, alcaldes, concejales, colegas U. de Chile, tesistas)",
    "texto_post": post_propuesto,
    "longitud_caracteres": len(post_propuesto),
    "imagen_adjunta": "Captura de pantalla real de la plataforma funcionando (1200x675 px, UI oscura sobria, tarjetas temáticas, buscador, contador de 7.462 normas y badge Chile 2026). NO es ilustración sintética ni IA slop.",
    "datos_reales_verificados": {
        "total_normas": 7462,
        "normas_bcn": 5881,
        "normas_municipales_sha256": 1581,
        "total_comunas": 346,
        "comunas_vigentes_2021_2026": 217,
        "comunas_rezago_fuentes_abiertas": 129,
        "asistente_local_privado": "Corre en JS del navegador, cero cookies de rastreo personal, cero costo API",
        "descargas_abiertas": "CSV de 2.5 MB, CSV de 346 comunas, y Notebook Jupyter didáctico para estudiantes",
        "buzon_colaborativo": "Modal activo en la web para enviar ordenanzas faltantes a evegat@uchile.cl"
    },
    "antecedentes_corregidos": [
        "Se eliminó la afirmación de que el 37% de comunas no publica nada (era indemostrable).",
        "Se eliminó la etiqueta de '6 materias obligatorias' y 'Plan Regulador' para evitar disputas doctrinarias con abogados.",
        "Se precisó que el hash SHA-256 aplica a las 1.581 normas municipales y BCN proviene de API oficial."
    ]
}

print("Ejecutando evaluación semántica con TypeSafe Jev...")
start_t = time.time()

eval_res = client.system_one(
    state=estado_evaluacion,
    questions={
        # 1. Rigor y Blindaje Fáctico
        "rigor_factico": typesafe_sdk.Choice(
            instructions="Evalúa el grado de precisión y veracidad de las afirmaciones frente a posibles críticas de municipalistas y académicos chilenos:",
            criteria={
                "vulnerable_a_desmentidos": "Contiene datos fáciles de refutar que dañan la credibilidad del autor",
                "parcialmente_respaldado": "Tiene asertos atendibles pero deja dudas metodológicas",
                "solido_y_verificable": "Afirmaciones sobrias, verificables en fuentes oficiales y sin sobrepromesas",
                "blindado_100_por_ciento": "Cada dato y afirmación tiene respaldo documental y técnico incontestable"
            }
        ),
        # 2. Percepción de Reputación y Tono
        "tono_y_humildad": typesafe_sdk.Choice(
            instructions="¿Cómo se percibe el tono de Eduardo en este post?",
            criteria={
                "soberbio_o_vende_humo": "Suena a startup que promete resolver todo o a crítica destructiva a municipios",
                "aburrido_o_academico_denso": "Muy técnico, poco atractivo para leer en el feed",
                "autoridad_tecnica_humilde": "Docente riguroso, comparte trabajo real, invita a colaborar sin ponerse en pedestal",
                "inseguro_o_defensivo": "Pide disculpas antes de mostrar el valor"
            }
        ),
        # 3. Riesgo de Percepción de 'IA Slop'
        "riesgo_ia_slop": typesafe_sdk.Choice(
            instructions="Teniendo en cuenta el post y la imagen (screenshot real de software funcionando, sin arte generativo):",
            criteria={
                "huele_a_ia_slop": "Parece contenido automatizado de relleno de IA que genera desconfianza",
                "hibrido_dudoso": "Tiene algunos destellos de marketing genérico",
                "producto_real_creible": "Evidencia contundente de software programado y funcionando (Proof of Work)"
            }
        ),
        # 4. Probabilidad de Rechazo o Crítica Maliciosa
        "probabilidad_ataque_malicioso": typesafe_sdk.Noul(
            instructions="Probabilidad (0.0 a 1.0) de que un funcionario municipal o colega acuse falsedad o mala fe en el post:"
        ),
        # 5. Reacción Esperada de la Comunidad de Gestión Pública
        "reaccion_comunidad": typesafe_sdk.Choice(
            instructions="¿Cuál será la reacción predominante de la comunidad pública y académica chilena?",
            criteria={
                "ataque_defensivo": "Sentimiento de fiscalización punitiva injusta",
                "curiosidad_y_consulta": "Van directo a revisar su comuna y ver qué ordenanzas aparecen",
                "adopcion_y_colaboracion": "Reconocimiento del valor público, aportes de decretos y uso en cátedras"
            }
        ),
        # 6. Veredicto Final de Publicación
        "veredicto_final": typesafe_sdk.Choice(
            instructions="Veredicto final para publicar este post en LinkedIn hoy mismo:",
            criteria={
                "detener_no_publicar": "Hay riesgos críticos no resueltos",
                "ajustar_redaccion": "Requiere cambios menores en frases específicas",
                "publicar_inmediato_recomendado": "Texto calibrado, blindado, auténtico y con alto potencial de impacto cívico"
            }
        )
    }
)

duracion = round(time.time() - start_t, 2)
print(f"Evaluación completada en {duracion}s.")

# Extraer resultados estructurados
rigor = eval_res.choices.get("rigor_factico")
tono = eval_res.choices.get("tono_y_humildad")
slop = eval_res.choices.get("riesgo_ia_slop")
ataque = eval_res.nouls.get("probabilidad_ataque_malicioso")
reaccion = eval_res.choices.get("reaccion_comunidad")
veredicto = eval_res.choices.get("veredicto_final")

res_dict = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "duracion_segundos": duracion,
    "veredicto_final": {
        "resultado": veredicto.choice if veredicto else "desconocido",
        "confianza": round(veredicto.confidence, 3) if veredicto else 0.0
    },
    "rigor_factico": {
        "resultado": rigor.choice if rigor else "desconocido",
        "confianza": round(rigor.confidence, 3) if rigor else 0.0
    },
    "tono_y_humildad": {
        "resultado": tono.choice if tono else "desconocido",
        "confianza": round(tono.confidence, 3) if tono else 0.0
    },
    "riesgo_ia_slop": {
        "resultado": slop.choice if slop else "desconocido",
        "confianza": round(slop.confidence, 3) if slop else 0.0
    },
    "probabilidad_ataque_malicioso_noul": round(ataque.noul, 3) if ataque else 0.0,
    "reaccion_comunidad": {
        "resultado": reaccion.choice if reaccion else "desconocido",
        "confianza": round(reaccion.confidence, 3) if reaccion else 0.0
    }
}

output_path = Path("reports/evaluacion_jev_linkedin.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(res_dict, indent=2, ensure_ascii=False), encoding="utf-8")

print("\n=================================================================")
print("DICTAMEN SEMÁNTICO TYPESAFE JEV (SYSTEM 1 RLCD) — LINKEDIN P090")
print("=================================================================")
print(f"• VEREDICTO FINAL:          {res_dict['veredicto_final']['resultado'].upper()} (confianza: {res_dict['veredicto_final']['confianza']})")
print(f"• RIGOR FÁCTICO:            {res_dict['rigor_factico']['resultado']} (confianza: {res_dict['rigor_factico']['confianza']})")
print(f"• TONO Y REPUTACIÓN:        {res_dict['tono_y_humildad']['resultado']} (confianza: {res_dict['tono_y_humildad']['confianza']})")
print(f"• RIESGO IA SLOP:           {res_dict['riesgo_ia_slop']['resultado']} (confianza: {res_dict['riesgo_ia_slop']['confianza']})")
print(f"• REACCIÓN COMUNIDAD:       {res_dict['reaccion_comunidad']['resultado']} (confianza: {res_dict['reaccion_comunidad']['confianza']})")
print(f"• PROBABILIDAD ATAQUE:      {res_dict['probabilidad_ataque_malicioso_noul']} ({res_dict['probabilidad_ataque_malicioso_noul']*100:.1f}%)")
print(f"\nArchivo guardado en: {output_path}")
