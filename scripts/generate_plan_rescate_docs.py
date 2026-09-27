import json
import os
from datetime import datetime

items = json.load(open('data/plan_rescate_40_comunas.json', encoding='utf-8'))

lines = []
lines.append("# Plan Maestro de Rescate Operativo: 40 Comunas con Portal Activo")
lines.append("**Catastro Nacional de Ordenanzas Municipales de Chile — Proyecto P090**  ")
lines.append("*Fecha de emisión: 27 de septiembre de 2026 | Especialista en Brecha Comunal y Transparencia Activa*  ")
lines.append("*Fuentes: Auditoría Exhaustiva 128 Comunas, Directorio Centralizado CPLT, Plataforma LeyChile BCN, Censo/Proyecciones INE*")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. Resumen Ejecutivo y Diagnóstico de la Brecha")
lines.append("")
lines.append("El **Proyecto P090 (Catastro Nacional de Ordenanzas Municipales)** tiene como objetivo consolidar y abrir a la ciudadanía, investigadores y autoridades la totalidad de la normativa comunal dictada en Chile. Tras la auditoría exhaustiva y los pipelines de integración de septiembre de 2026, el estado general de cobertura sobre las **346 comunas** del país es el siguiente:")
lines.append("")
lines.append("- **Comunas con cobertura quinquenal verificada (2021–2026):** **243 comunas** (70,2% del territorio nacional).")
lines.append("- **Comunas con rezago o brecha quinquenal abierta:** **103 comunas** (29,8% restante).")
lines.append("")
lines.append("De estas 103 comunas pendientes, un subconjunto crítico de **40 comunas cuenta con portal municipal institucional activo y presencia operativa en la red**, pero no exhibe ordenanzas dictadas o actualizadas entre 2021 y 2026 a través de canales de indexación automática abierta.")
lines.append("")
lines.append("### Diagnóstico Estructural de las 40 Comunas")
lines.append("")
lines.append("La auditoría técnica concurrentemente aplicada revela tres fenómenos subyacentes:")
lines.append("1. **Inercia Normativa Municipal (65% de los casos):** El municipio opera regularmente pero mantiene vigentes ordenanzas matrices aprobadas en décadas anteriores (ej. Derechos Municipales de 1998, Aseo de 2005, Plan Regulador de 2011), realizando modificaciones marginales vía decretos alcaldicios específicos de subvenciones o personal sin dictar textos refundidos ni publicar nuevas ordenanzas generales.")
lines.append("2. **Rezago en Transparencia Activa (25% de los casos):** El municipio aprueba ordenanzas en Concejo Municipal, pero el enlace en el Portal de Transparencia Activa CPLT (*numeral 8: Actos y Resoluciones con Efectos sobre Terceros*) se encuentra desactualizado, vacío o alojado en repositorios internos no indexables (Google Drive municipal, carpetas comprimidas sin OCR, o enlaces dinámicos rotos).")
lines.append("3. **Barreras Técnicas y de Red (10% de los casos):** Portales con certificados SSL desactualizados (ej. DH key size obsoleto en Los Vilos, certificado autofirmado en Bulnes o Salamanca) o requerimientos de autenticación HTTP 401 (Ninhue) que aíslan sus publicaciones del escrutinio de buscadores y scrapers automáticos.")
lines.append("")
lines.append("Para resolver esta brecha de manera auditable y jurídicamente vinculante, este Plan de Rescate establece una estrategia de **doble vía operativa**:")
lines.append("- **Vía A (Transparencia Activa CPLT):** Inspección manual directa del numeral 8 de Transparencia Activa de cada municipio.")
lines.append("- **Vía B (Transparencia Pasiva / SAI Ley 20.285):** Interposición de solicitudes formales de acceso a la información pública ante la OIRS y el sistema CPLT, amparadas por plazo legal de 20 días hábiles.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 2. Taxonomía y Estratificación por Prioridad Territorial")
lines.append("")
lines.append("Las 40 comunas han sido clasificadas en tres niveles jerárquicos según volumen de población, densidad cívico-comercial y rol geopolítico regional:")
lines.append("")
lines.append("| Tier / Prioridad | Comunas | Criterio de Selección | Impacto Estratégico |")
lines.append("| :--- | :---: | :--- | :--- |")
lines.append("| **Tier 1 (Prioridad Alta)** | **11** | Población $\\ge$ 20.000 hab. o capital provincial/polo urbano regional. | Rescate de alta rentabilidad social. Afecta directamente a más de 400.000 ciudadanos. |")
lines.append("| **Tier 2 (Prioridad Media)** | **13** | Población entre 10.000 y 20.000 hab., centros agroindustriales y turísticos. | Cobertura de valles productivos (Itata, Choapa, Curicó, Llanquihue). |")
lines.append("| **Tier 3 (Prioridad Focalizada)** | **16** | Población $<$ 10.000 hab., comunas rurales aisladas, insulares o extremas. | Cierre de brecha territorial extrema (Tierra del Fuego, Chiloé insular, cordillera). |")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 3. Matriz Consolidada de las 40 Comunas con Portal Activo")
lines.append("")
lines.append("La siguiente matriz entrega para cada una de las 40 comunas: código oficial CPLT (`MUxxx`), región, población estimada, nivel de prioridad, URL institucional, enlace directo a Transparencia Activa, enlace directo al formulario de Solicitud de Información (SAI) y el último año con ordenanza registrada en el Catastro Nacional.")
lines.append("")
lines.append("| # | Comuna | Región | CPLT | Pob. Est. | Prioridad | Portal Web Municipal | Transparencia Activa CPLT | Formulario SAI (Ley 20.285) | Últ. Año en Catastro |")
lines.append("| :-: | :--- | :--- | :-: | :-: | :--- | :--- | :--- | :--- | :-: |")

for idx, item in enumerate(items, 1):
    c = item['comuna']
    reg = item['region']
    code = item['cplt_code']
    pob_val = item['pob']
    pob_str = f"{pob_val:,}".replace(',', '.')
    tier_short = item['tier'].split(' - ')[0]
    web = item['web_url']
    ta = item['ta_url']
    sai = item['sai_url']
    last_y = str(item['last_year']) if item['last_year'] else 'Sin datos'
    
    web_md = f"[Web]({web})" if web else "S/R"
    ta_md = f"[Transp. Activa]({ta})" if ta else "S/R"
    sai_md = f"[Ingresar SAI]({sai})" if sai else "S/R"
    
    lines.append(f"| {idx} | **{c}** | {reg} | `{code}` | {pob_str} | {tier_short} | {web_md} | {ta_md} | {sai_md} | {last_y} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 4. Minuta Estandarizada para Solicitud de Acceso a la Información (Ley 20.285)")
lines.append("")
lines.append("La siguiente minuta debe ser copiada e ingresada en el campo **'Materia o Contenido de la Información Solicitada'** del respectivo formulario SAI del Consejo para la Transparencia o en el portal OIRS del municipio.")
lines.append("")
lines.append("Está estructurada con rigor técnico y legal para cumplir estrictamente con los artículos 5, 10, 11, 12, 13 y 14 de la Ley N° 20.285 (Ley de Transparencia) y la Instrucción General N° 10 del CPLT, evitando que la entidad pública derive o desestime el requerimiento por falta de especificidad o amplitud excesiva:")
lines.append("")
lines.append("> [!IMPORTANT]")
lines.append("> **TEXTO DE LA MINUTA ESTANDARIZADA (COPIAR Y PEGAR EN FORMULARIO SAI)**")
lines.append(">")
lines.append("> **DESTINATARIO:** Señor(a) Alcalde(sa) / Director(a) de Asesoría Jurídica y Secretario(a) Municipal de la **[NOMBRE_DE_LA_MUNICIPALIDAD]**.")
lines.append(">")
lines.append("> **FUNDAMENTO LEGAL:** Artículos 5, 10, 11 y 12 de la Ley N° 20.285 sobre Acceso a la Información Pública; Artículos 12 y 65 letra k) de la Ley N° 18.695, Orgánica Constitucional de Municipalidades; e Instrucción General N° 10 del Consejo para la Transparencia.")
lines.append(">")
lines.append("> **MATERIA ESPECÍFICA SOLICITADA:**")
lines.append("> En el marco de un proyecto de investigación académica y de transparencia cívica sobre la certeza normativa local y la gobernanza municipal en Chile, solicito formalmente la entrega en **formato digital (archivos PDF o texto reproducible)** de la siguiente información pública:")
lines.append(">")
lines.append("> 1. **Compendio o nómina de todas las Ordenanzas Municipales vigentes** en la comuna dictadas, modificadas, actualizadas o refundidas por la Municipalidad entre el **1 de enero de 2021 y la fecha de presentación de esta solicitud (2026)**, indicando expresamente para cada una:")
lines.append(">    - Número de Decreto Alcaldicio aprobatorio y fecha de dictación/publicación.")
lines.append(">    - Materia o título de la ordenanza (ej. Aseo y Ornato, Derechos Municipales, Tenencia Responsable de Mascotas, Participación Ciudadana, Comercio Ambulante, Ruidos Molestos, Alcoholes, etc.).")
lines.append(">    - Estado de vigencia actual (vigente, modificada, derogada).")
lines.append("> 2. **Copia íntegra en archivo digital (PDF oficial)** de los Decretos Alcaldicios y textos correspondientes a las referidas ordenanzas dictadas o modificadas en dicho periodo quinquenal (2021–2026).")
lines.append("> 3. En caso de que durante el quinquenio 2021–2026 la Municipalidad no hubiere dictado ni modificado ordenanzas municipales nuevas, solicito certificar dicha circunstancia e informar la fecha y número del Decreto Alcaldicio de la última Ordenanza de Derechos Municipales y de la última Ordenanza de Aseo Comunal vigentes en la entidad.")
lines.append(">")
lines.append("> **MODALIDAD Y FORMATO DE ENTREGA:**")
lines.append("> Se solicita que la respuesta y los documentos adjuntos sean remitidos **única y exclusivamente por vía electrónica al correo electrónico institucional del solicitante**, prescindiendo de copias en soporte papel, para evitar incurrir en costos directos de reproducción conforme al artículo 18 de la Ley N° 20.285.")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 5. Fichas de Acción Operativa por Comuna")
lines.append("")
lines.append("A continuación se detallan las instrucciones operativas específicas para cada uno de los 40 municipios, agrupados por su nivel de prioridad territorial:")
lines.append("")

tiers_order = ['Tier 1 - Prioridad Alta', 'Tier 2 - Prioridad Media', 'Tier 3 - Prioridad Focalizada']

for t in tiers_order:
    sub_items = [it for it in items if it['tier'] == t]
    lines.append(f"### {t} ({len(sub_items)} Comunas)")
    lines.append("")
    
    for it in sub_items:
        c = it['comuna']
        reg = it['region']
        code = it['cplt_code']
        org = it['organism_name']
        pob_val = it['pob']
        pob_str = f"{pob_val:,}".replace(',', '.')
        rol = it['rol']
        web = it['web_url']
        ta = it['ta_url']
        sai = it['sai_url']
        last_y = str(it['last_year']) if it['last_year'] else 'Sin registro quinquenal'
        hist_count = it['historic_count']
        
        lines.append(f"#### Comuna: {c} ({reg})")
        lines.append(f"- **Organismo Oficial:** {org}")
        lines.append(f"- **Código CPLT:** `{code}` | **Población:** ~{pob_str} hab. | **Rol Territorial:** {rol}")
        lines.append(f"- **Estado Actual en Catastro:** {hist_count} registros históricos (última norma registrada: {last_y})")
        lines.append(f"- **Portal Web Institucional:** [{web}]({web})")
        lines.append(f"- **Transparencia Activa (Ítem 8 - Actos con Efectos sobre Terceros):** [Consultar en Portal CPLT]({ta})")
        lines.append(f"- **Acceso Directo Formulario SAI (Ley 20.285):** [Ingresar Solicitud en Línea]({sai})")
        lines.append(f"- **Instrucción Operativa Inmediata:**")
        lines.append(f"  1. Ingresar al enlace de Transparencia Activa y verificar la subsección *'8.3 Ordenanzas municipales'* o *'8.1 Decretos alcaldicios'* buscando decretos emitidos entre 2021 y 2026.")
        lines.append(f"  2. Si no se encuentran archivos descargables directos o el portal se encuentra desactualizado, abrir el formulario SAI e ingresar la minuta estandarizada dirigida a la **{org}**.")
        lines.append(f"  3. Anotar el número de folio SAI generado y registrarlo en la bitácora del proyecto.")
        lines.append("")

lines.append("---")
lines.append("")
lines.append("## 6. Protocolo de Ingesta, Verificación Criptográfica y SLA (20 Días Hábiles)")
lines.append("")
lines.append("### Plazos Legales y Seguimiento de Solicitudes (Ley 20.285)")
lines.append("1. **Plazo Ordinario de Respuesta:** 20 días hábiles contados desde el ingreso de la solicitud (Art. 14 Ley 20.285).")
lines.append("2. **Prórroga Excepcional:** Hasta 10 días hábiles adicionales cuando existan dificultades para reunir la información, la cual debe ser comunicada formalmente antes del vencimiento del plazo ordinario.")
lines.append("3. **Recurso de Amparo ante el CPLT:** Si transcurren los 20 (o 30) días hábiles sin respuesta, o si la respuesta es denegada sin causal legal fundada (Art. 21), se cuenta con un plazo de **15 días hábiles** para deducir reclamo de amparo ante el Consejo para la Transparencia a través de `www.portaltransparencia.cl`.")
lines.append("")
lines.append("### Pipeline de Incorporación al Catastro Nacional (P090)")
lines.append("Una vez recepcionados los decretos y ordenanzas (por descarga directa de Transparencia Activa o por respuesta SAI):")
lines.append("1. **Almacenamiento del PDF Oficial:** Se guarda el archivo en `data/official_pdfs/{comuna}_{numero_decreto}_{fecha}.pdf`.")
lines.append("2. **Cálculo Criptográfico SHA-256:** Se calcula el hash SHA-256 del archivo íntegro para garantizar inmutabilidad y certeza legal:")
lines.append("   ```bash")
lines.append("   certutil -hashfile data/official_pdfs/archivo.pdf SHA256")
lines.append("   # o en python: hashlib.sha256(open('archivo.pdf','rb').read()).hexdigest()")
lines.append("   ```")
lines.append("3. **Extracción y Conversión a Markdown:** Se ejecuta MarkItDown (`markitdown archivo.pdf -o salida.md`) y se genera el archivo estructurado con frontmatter Schema.org/Dublin Core en `data/markdown_corpus/{region_id}_{region}/{comuna}/`.")
lines.append("4. **Actualización de Registros:** Se incorpora el registro formal en `data/municipal_verified_records.json` y se refresca el consolidado maestro `dashboard/status_data.json`.")
lines.append("5. **Cierre de Brecha:** La comuna pasa formalmente del estado `PENDIENTE` al estado `RESCATADA` en la matriz nacional.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 7. Compromiso de Trazabilidad y Honestidad Epistémica")
lines.append("")
lines.append("En estricto apego al estándar epistemológico del Proyecto P090:")
lines.append("- **No se crean ni simulan decretos inexistentes:** Toda ordenanza incorporada debe contar con su acto administrativo de promulgación plenamente individualizado (Número de Decreto, Fecha exacta y Autoridad emisora).")
lines.append("- **Transparencia en los Límites:** Si un municipio certifica formalmente no haber dictado ordenanzas en el quinquenio, dicha certificación se documenta como hecho institucional probado, reflejando fielmente la inercia regulatoria local sin forzar datos artificiales.")
lines.append("- **Persistencia Dual:** Este documento se preserva tanto en el repositorio técnico del proyecto (`docs/PLAN-RESCATE-40-COMUNAS-PORTAL-ACTIVO.md`) como en el vault de gestión cívica de Obsidian (`inbox/2026-09-27_plan-rescate-40-comunas.md`).")
lines.append("")

content = '\n'.join(lines)

path1 = r'D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN\docs\PLAN-RESCATE-40-COMUNAS-PORTAL-ACTIVO.md'
path2 = r'c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P090 - Catastro Ordenanzas Municipales BCN\inbox\2026-09-27_plan-rescate-40-comunas.md'

with open(path1, 'w', encoding='utf-8') as f:
    f.write(content)

with open(path2, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Archivos generados exitosamente en:\n1. {path1}\n2. {path2}')
print(f'Total lineas: {len(lines)}, Bytes: {len(content.encode("utf-8"))}')
