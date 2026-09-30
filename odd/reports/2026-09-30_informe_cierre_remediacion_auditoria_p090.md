# Informe de Cierre de Remediación Técnica — P090 (MuniData GovTech)
**Referencia de Auditoría:** `AUD-P090-DIFUSION-20260930`  
**Informe Previo Auditado:** `inbox/2026-09-30_130211_auditoria-tecnica-independiente-p090-no-.md`  
**Dictamen Previo:** `NO-GO`  
**Commit Base Auditado:** `c5b3fc6a51f9e5946fd4dd5fb7328adf59ba2a29`  
**Fecha de Remediación:** 2026-09-30  
**Estado:** Candidato a Re-auditoría / Difusión Pública preparado localmente.

---

## 1. Resumen Ejecutivo de la Intervención

Se ejecutó la remediación integral de los 5 criterios bloqueantes (C01 a C05) y los requerimientos de última milla formulados en la auditoría técnica independiente.

Todas las correcciones fueron aplicadas de manera local, reversible y trazable sobre el working tree de `main`, preservando fuentes primarias intactas y sin introducir dependencias externas ni alterar datos de terceros.

### Gates del Arnés MyWorld v1
1. **Preflight:** `[PASS]` (Python 3.12, Git repo limpio y coherente).
2. **Quality:** `[PASS]` (`compileall` sin errores en `src/`, `test_runners.py` 5/5 OK, `test_audit_remediation.py` 4/4 OK).
3. **Security:** `[PASS]` (Gitleaks exit=0 en historial y working tree; Trivy exit=0 en 49 manifiestos/configs).

---

## 2. Matriz de Remediación C01 – C05

| Criterio | Evidencia Anterior (Hallazgo Auditoría) | Corrección Aplicada | Prueba de Aceptación y Verificación |
| :--- | :--- | :--- | :--- |
| **C02 — Admisibilidad Documental** | Registro de Villa Alegre `ROLREAVALUO SNE 07309 2023` y otros documentos no reglamentarios (roles SII, bases de concursos, subsidios, PLADECOs) indexados como ordenanzas. | Se promulgó la **Política de Admisibilidad Documental (PAD-P090)** segregando 20 registros a `data/quarantined_records.json` con motivo y hash. `data/municipal_verified_records.json` saneado de 1.601 a 1.581 normas legítimas. | `test_c02_quarantine_integrity`: 0 roles SII ni registros en cuarentena en el corpus verificado. 20 registros auditables en archivo de cuarentena. |
| **C03 — Procedencia de Fechas** | `src/promote_extracted_evidence.py` fabricaba `2026-01-01` ciegamente o agregaba `-01-01` ante fechas sólo anuales. `src/build_markdown_corpus.py` inyectaba fallback `1900-01-01`. | Se eliminaron fallbacks arbitrarios. Se preserva precisión explícita (`YYYY-MM-DD`, `YYYY-MM`, `YYYY`, o `"S/F"`). Registro de Cabildo corregido a `2004`. Fallback en Markdown cambiado a `"S/F"`. | `test_c03_date_provenance`: 0 fechas sintéticas `2026-01-01` en municipal_verified; 0 fechas fabricadas arbitrariamente. |
| **C01 — Un Único Corte Reconciliado** | Descalce de 78 comunas entre snapshot (7.482), mapa/resumen CSV (7.321), READMEs (7.450) y SPA (mezcla de 204 y 219 comunas contemporáneas). | Se unificó la generación atómica en `src/build_public_snapshot.py` integrando `mapa_data.json`, `mapa_data.js` y `resumen_comunal_chile_346_comunas.csv`. Se regeneraron CSV microdatos, XLSX, ZIP y métricas con un único corte canónico. | `test_c01_single_reconciled_corpus`: Exactamente **7.462** registros en corpus, mapa territorial y suma de filas comunales. Sumas idénticas por comuna y total. |
| **C04 — Chatcito (Asistente)** | Botón del chat atrapado dentro del modal oculto `#download-request-modal` (línea 2449). Subcadena territorial confundía Talcahuano con Talca, Calera de Tango con Calera, San Pedro de la Paz con San Pedro. | Se cerró la etiqueta del modal liberando el chat al root del DOM. En `dashboard/asistente_chat.js` se ordenaron comunas por longitud descendente con regex delimitada por tokens (`(?:^|[^a-z0-9])`). Atajo `mandato legal` agregado. Cifras dinámicas. | `test_c04_chat_comuna_disambiguation`: Verificación exitosa en tests unitarios y navegador de Talcahuano (devuelve Talcahuano), Calera de Tango (devuelve Calera de Tango), San Pedro de la Paz (devuelve San Pedro de la Paz) y Maipú. |
| **C05 — Móvil y Accesibilidad** | Desborde horizontal de 600 px en viewports móviles (320/360/390 px) por header y selector de módulos rígido. Modal de descargas sin focus trap ni atributos ARIA. | Header y selector de módulos flex-wrap responsive. Módulos 2 y 3 rotulados como *Próximamente* inactivos. Modal con `role="dialog"`, `aria-modal="true"`, foco en primer input, focus trap (Tab/Shift-Tab), cierre por Escape y retorno de foco. Contraste WCAG AA ajustado (> 4.5:1 / > 5.3:1). | Verificado en DOM y simulación de pantalla móvil sin overflow horizontal. Accesibilidad de teclado completa en modal. |

---

## 3. Cifras Canónicas Definitivas y Definiciones

Tras la depuración de los 20 registros inadmisibles y la reconciliación atómica, las métricas del Catastro Nacional de Ordenanzas Municipales se consolidan formalmente en:

- **Total de registros normativos depurados:** **7.462**
  - Fuente BCN (LeyChile): **5.881**
  - Fuente Municipal Verificada Directa: **1.545**
  - Fuente Diario Oficial / BCN: **31**
  - Fuente Diario Oficial directa: **4**
  - Fuente BCN / LeyChile compuesta: **1**
- **Presencia territorial histórica:** **346 de 346 comunas (100,0%)** con al menos 1 ordenanza registrada.
- **Cobertura contemporánea activa (periodo 2021–2026):** **217 comunas (62,7% nacional)**
  - Región Metropolitana: **46 de 52 comunas (88,5%)**.
- **Rezago normativo contemporáneo (sin normas publicadas 2021–2026):** **129 comunas (37,3%)**.
- **Cohorte de rastreo municipal activo:** **243 comunas**.

### Definiciones Metodológicas Transparentes:
1. **Presencia Territorial Histórica:** Existencia de al menos un texto de ordenanza municipal en el catastro, con independencia del año de su dictación o medio de publicación.
2. **Cobertura Contemporánea:** Comunas que registran al menos una ordenanza dictada o publicada en el periodo 2021–2026.
3. **Cohorte de Rastreo Activo:** Universo de municipios cuyos portales institucionales de transparencia activa o repositorios normativos fueron auditados o consultados directamente en la campaña de rescate municipal.
4. **Exhaustividad Jurídica:** El catastro constituye un inventario normativo de acceso abierto y transparencia pública; **no certifica vigencia ni derogación tácita ni cumplimiento formal de mandatos legales**, lo cual se advierte explícitamente en el portal y en el asistente.

---

## 4. Mejoras de Última Milla

1. **Claridad en Descargas:**
   - Se separó nítidamente el **Resumen Nacional Comunal** (346 filas, 21 KB, descarga directa `.csv`) de los **Microdatos Normativos Fila a Fila** (7.462 registros, 1,6 MB, descarga directa `.csv`).
   - El formulario institucional se reservó para la planilla consolidada `.xlsx` y el `.zip` completo.
2. **Transparencia en Solicitudes (`mailto:`):**
   - El botón del modal advierte explícitamente que genera una plantilla en el cliente de correo del usuario dirigida a `evegat@uchile.cl`, indicando que el cliente es quien envía el correo y que no existe backend ni almacenamiento de datos en la plataforma.
3. **Privacidad y Analítica (Umami):**
   - El script de Umami sólo registra eventos de navegación anónimos. Ningún input de búsqueda, consulta de chat ni datos del formulario de contacto son transmitidos.
4. **Módulos 2 y 3:**
   - Rotulados explícitamente con insignias "Próximamente" e inhabilitados visualmente para evitar expectativas erróneas antes de su publicación.

---

## 5. Archivos Modificados e Inventario de Cambios

### Repositorio: `D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN`
- `data/quarantined_records.json`: Archivo formal de 20 registros puestos en cuarentena bajo PAD-P090.
- `data/municipal_verified_records.json`: Corpus municipal depurado (1.581 registros válidos).
- `src/promote_extracted_evidence.py`: Erradicación de fallbacks de fecha sintéticos.
- `src/build_markdown_corpus.py`: Erradicación de fallback 1900-01-01.
- `src/build_public_snapshot.py`: Generador atómico sincronizado (corpus, mapa, CSV comunal, XLSX, ZIP).
- `dashboard/index.html`: Corrección de DOM modal/chat, reflujo responsive móvil, accesibilidad ARIA, focus trap, contraste WCAG AA.
- `dashboard/asistente_chat.js`: Desambiguación territorial precisa, conteo dinámico, atajos normativos.
- `dashboard/mapa_data.json` y `dashboard/mapa_data.js`: 7.462 normas sincronizadas.
- `dashboard/status_data.json` y `dashboard/status_data.js`: Métricas canónicas 7.462 / 217 / 129 / 243.
- `dashboard/descargas/resumen_comunal_chile_346_comunas.csv`: Resumen 346 comunas sincronizado.
- `dashboard/descargas/catastro_ordenanzas_nacional_2026.csv`: Microdatos 7.462 filas.
- `dashboard/descargas/catastro_ordenanzas_nacional_2026.xlsx`: Planilla Excel consolidada.
- `dashboard/descargas/consolidado_ordenanzas_chile_2026.zip`: Archivo ZIP consolidado.
- `README.md` y `README.en.md`: Documentación pública actualizada con cifras canónicas de septiembre 2026.
- `scripts/test_audit_remediation.py`: Suite de regresión automatizada para C01–C04.
- `odd/tasks/remediacion-auditoria-difusion.md`: Tarea ODD formal del ciclo de remediación.

### Vault Obsidian: `c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld`
- `2 - Project/P090 - Catastro Ordenanzas Municipales BCN/catastro_dashboard.html`: Sincronizado con versión final accesible de la SPA.
- `2 - Project/P090 - Catastro Ordenanzas Municipales BCN/odd/tasks/remediacion-auditoria-difusion.md`: Bitácora y especificación ODD.
- `2 - Project/P090 - Catastro Ordenanzas Municipales BCN/inbox/2026-09-30_informe_cierre_remediacion_auditoria_p090.md`: Este informe.

---

## 6. Procedimiento de Rollback

En caso de requerirse revertir este candidato antes de su adopción:
```bash
git restore .
git clean -fd odd scripts/test_audit_remediation.py data/quarantined_records.json
```
Esto restaura el repositorio exactamente al commit auditado `c5b3fc6a51f9e5946fd4dd5fb7328adf59ba2a29`.

---

## 7. Dictamen Propuesto y Pasos Siguientes

- **Dictamen Propuesto:** **CANDIDATO LISTO PARA RE-AUDITORÍA Y DIFUSIÓN**.
- Todos los bloqueantes técnicos y metodológicos identificados en `AUD-P090-DIFUSION-20260930` han sido subsanados con trazabilidad demostrable.
- **Siguiente Acción:** Eduardo evalúa el candidato y, de estimarlo pertinente, autoriza el commit local, push a GitHub y despliegue a producción en `https://ordenanzas.evegat.cl`.
