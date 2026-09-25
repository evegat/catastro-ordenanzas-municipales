# P090 — Estado y reentrada

## Revisión de cierre — 2026-09-21 UTC

Task ID: `P090-20260920-cierre`. Responsable: Codex. Integration owner: Eduardo Vega.
Base: `91e93bf17ff8b8cea61c772c47763b162cdc065b`, rama `main`, con cambios previos preservados.

**Estado: no listo para cierre; sitio público no disponible (HTTP 503).** Esta sección prevalece sobre los recuentos y estados históricos inferiores.

### Trabajo verificado

- Snapshot: 7.321 registros, 5.881 BCN y 1.440 en el conjunto municipal verificado del pipeline; 346 comunas representadas. No acredita exhaustividad ni vigencia.
- Inventario regenerado sin cifras manuales: 1.299 PDF con cabecera PDF válida bajo `data/official_pdfs`, 7.269 archivos Markdown bajo `data/markdown_corpus` y 19 textos externos. Estos recuentos no prueban integridad completa ni calidad de extracción.
- Generador del inventario portable respecto del repositorio, directorio externo configurable y SQLite abierto solo en lectura. No vuelve a escribirse a sí mismo. Devuelve error si detecta diferencias de conteo.
- Dos pruebas de regresión aprobadas: conteos variables/categorías de fuente/discrepancias y exclusión de archivos ajenos o falsas descargas PDF.
- Reconstrucción del snapshot en copia temporal: 7.321 filas CSV y XLSX; ZIP coincide con CSV/JSON; JS coincide con JSON; validador HTML aprobado; segunda generación produce JSON idéntico.
- Artefactos del checkout: contenido completo del CSV coincide con las filas del snapshot; JS y JSON del ZIP coinciden con el JSON canónico; métricas HTML pasan el validador existente. XLSX comprobado fila por fila; mapa con 346 comunas únicas y 7.321 registros, recuentos por comuna coincidentes y JS/JSON iguales. Pendiente interacción visual.
- `git diff --check` aprobado para los archivos de este bloque. La comprobación global falla por espacios en el corpus Markdown preexistente; se conserva sin modificación.
- Compilación de `src` y `scripts` aprobada. No prueba ejecución de todos los recolectores.

### Validación del visualizador local — 21 de septiembre

- Reproducido y corregido: mapa sin marcadores por `ReferenceError: TOPIC_ALIASES is not defined`. Los alias ahora se derivan de los grupos temáticos existentes.
- Navegador local: 346 marcadores renderizados; filtro de mascotas con 93 comunas en verde, igual al recuento independiente del JSON. Prueba de regresión `node scripts/test_map.cjs`: PASS.
- Reemplazado el mapa base Carto que mostraba avisos de clave requerida por mosaicos HTTPS de OpenStreetMap. Carga visible comprobada, atribución conservada, sin precarga masiva ni cambios de caché/Referer. Política: https://operations.osmfoundation.org/policies/tiles/ (servicio sin garantía de disponibilidad; evaluar proveedor dedicado si aumenta el tráfico).
- Búsqueda «Arica»: 55 resultados en 4 comunas de la región; ficha de Arica: 39 registros; filtro «contaminacion»: 1 resultado. Son casos de prueba, no evaluación exhaustiva de relevancia.
- Descarga abierta del resumen CSV: evento de descarga confirmado en navegador; 346 filas y 7.321 registros agregados, conteos por comuna coincidentes con el snapshot. Excel y ZIP mantienen el flujo existente de solicitud institucional; no se enviaron formularios.
- Corregidos textos que confundían presencia territorial con exhaustividad o registros con vigencia, y enlaces que prometían PDF sin garantizarlo. Ahora indican «Consultar fuente oficial».
- Versionados los dos scripts modificados por hash en el HTML para evitar servir la versión anterior desde caché.
- Pendiente: revisión completa de accesibilidad, interacción de todos los filtros, asistente y formularios; no se declara completado el visualizador por estos casos acotados.

### Lanzadores y asistente — revisión adicional

- `run_local_crawler.ps1`: comprueba módulo e intérprete antes de comenzar; `-ValidateOnly` no ejecuta trabajo; un lote por defecto mediante `-MaxBatches`; máximo dos fallos consecutivos; distingue límite de lotes de cola completa.
- `run_sinim_discovery.ps1`: comprueba los siete módulos del flujo antes del mutex, logs, red o inferencia; `-ValidateOnly` solo verifica dependencias locales.
- `python scripts/test_runners.py`: cinco pruebas aprobadas en repositorios temporales con un crawler ficticio (dependencias ausentes, validación sin ejecución, límite de lotes, fallos repetidos y cola completa). No se ejecutó un crawler real ni LM Studio.
- Los dos lanzadores reales devuelven 1 con `-ValidateOnly` por dependencias ausentes. Los cuatro módulos faltantes fueron eliminados por el commit `25fa8b5f` de saneamiento para open-source: `continuous_commune_crawler.py`, `classify_sinim_evidence_lmstudio.py`, `merge_sinim_discovery_shards.py`, `merge_sinim_extraction_shards.py`. No se restauran sin revisar el motivo y el contenido de esa eliminación. El watchdog histórico sigue pendiente de revisión y no debe reactivarse.
- Asistente: consultas y campos interpolados se escapan como texto HTML; enlaces Markdown aceptan solo HTTP/HTTPS; botón comunal admite apóstrofos; analítica conserva el evento sin transmitir texto de consultas.
- `node scripts/test_chat.cjs`: prueba aprobada con consulta HTML, URL ejecutable, metadatos y comuna O'Higgins. Comprueba el módulo real con adaptador DOM mínimo; no equivale a prueba completa en navegador.
- El asistente actual es un conjunto de respuestas predefinidas y búsquedas del catálogo, no un sistema RAG sobre texto documental. Sus explicaciones jurídicas predefinidas y la sección de materias obligatorias requieren revisión de fuentes y vigencia antes de considerarlas validadas. No se certifican en este bloque.

### Disponibilidad pública: evidencia y límites

- `https://ordenanzas.evegat.cl/`: HTTP 503; también fallan JSON y manifiesto de descargas. Verificador E2E devuelve 1 correctamente.
- GitHub Pages redirige su URL de proyecto a `http://ordenanzas.evegat.cl/`.
- La consulta a `https://evegat.github.io` con cabecera Host del dominio entrega HTTP 200 y 102.001 bytes. Solo prueba respuesta del servidor; no prueba TLS del dominio ni igualdad con el candidato local.
- Consulta DNS pública: A/AAAA de Cloudflare y servidores autoritativos de Cloudflare; sin CNAME público expuesto. Esto no permite conocer el origen configurado detrás del proxy.
- Consulta directa a GitHub Pages usando SNI `ordenanzas.evegat.cl`: falla la validación de nombre del certificado. No desactivar el proxy como solución automática: HTTPS directo aún no está acreditado.
- GitHub API para Pages responde 404 en esta sesión; no se puede concluir si falta acceso o configuración.

### Pendientes estructurados

| ID | Estado | Siguiente acción / criterio |
| --- | --- | --- |
| CIERRE-01 | pendiente de acceso/configuración | Inspeccionar registro y origen reales en Cloudflare y configuración Pages; preparar cambio exacto, respaldo y reversión. Modificar DNS/producción requiere autorización específica de Eduardo. Cerrar solo con TLS válido y E2E público aprobado. |
| CIERRE-02 | parcial | Datos de XLSX/mapa comprobados. Casos de búsqueda, filtro comunal, mapa y descarga CSV aprobados; ampliar prueba de los demás flujos sin enviar formularios. |
| CIERRE-03 | abierto | Revisar corpus Markdown/PDF, ledger y lote documental antes de afirmar disponibilidad de RAG o exhaustividad. |
| CIERRE-04 | abierto | Diagnóstico temprano y límites añadidos. Revisar eliminación deliberada de módulos en 25fa8b5f y definir flujo soportado; watchdog sin reactivar. |

Superficie de este bloque: generador, verificador E2E, pruebas de regresión, manifiesto/inventario, README en ambos idiomas, esta guía y correcciones de dashboard/index.html, mapa_chile.js, asistente_chat.js y los dos lanzadores con sus pruebas. Sin commit, push, publicación, DNS ni cambios de infraestructura. Issue canónico pendiente de vinculación antes de integrar. Rollback: revertir únicamente los cambios de este task_id tras revisar el diff, sin restaurar globalmente el checkout ni tocar originales.

---

## Antecedente histórico — revisión del 15 de septiembre

Fecha de revisión local: **2026-09-15**. Estado: **en evolución; no listo para cierre**.
Task ID: `P090-20260915-documentacion`. Responsable: Codex. Integration owner: Eduardo Vega.
Base revisada: `d51b1e7937502f66e24dddeccbcd0e56b289f489` (`main`).

## Punto de partida

Existe un catálogo referencial, un visualizador estático y herramientas de recolección. La presencia de registros en todas las comunas no demuestra que estén todas las ordenanzas ni que su vigencia esté resuelta. El asistente RAG (respuestas basadas en documentos recuperados) sigue siendo una evolución planificada.

Esta revisión actualiza documentación local. No acredita el estado del sitio público, DNS, VPS, automatizaciones ni enlaces remotos. El perfil `MYWORLD-HARNESS.json` declara `production`: es una declaración de infraestructura, no un criterio de término del producto.

## Evidencia local conciliada

| Medida | Resultado | Fuente y límite |
| --- | --- | --- |
| Registros del catálogo | 7.287 | Filas de `dashboard/status_data.json`; coincide con sus métricas y el CSV de descargas |
| BCN | 5.881 | Registros clasificados como BCN en el snapshot |
| Municipales con verificación registrada | 1.406 | `data/municipal_verified_records.json`; no se revalidaron las URLs en esta revisión |
| Comunas representadas | 346 de 346 | Al menos un registro por comuna; no exhaustividad |
| Comunas con 1 / 2 / 3 registros | 4 / 9 / 6 | Recuento directo del snapshot; 19 comunas con 1–3 registros |
| PDF locales | 10 | Archivos encontrados bajo `data/`; no equivale a 1.406 documentos descargados |
| Exhaustividad | No acreditada | `data/national_coverage_ledger.json`: `coverage_complete=false` |

El ledger fue generado el 30 de agosto y declara 3 de 345 municipios sin brechas. Es evidencia histórica pendiente de actualización, no una evaluación actual de los 1.406 registros municipales. Sus categorías de brechas pueden superponerse.

El manifiesto `data/document_inventory_manifest.json`, generado el 13 de septiembre, contiene 7.287 registros en sus mediciones y todavía 7.226 en `conclusions`. No usar esas conclusiones como cifra canónica. Los 19 textos externos y las 1.632 filas SQLite que allí aparecen no se volvieron a inspeccionar en esta revisión.

## Pendientes priorizados

| ID | Estado | Trabajo y criterio de aceptación |
| --- | --- | --- |
| DOC-01 / paquete 01 | Parcial | README e inventario documental conciliados. Falta demostrar que HTML, JS, mapas, XLSX y ZIP corresponden al mismo corte, mediante reconstrucción aislada y comparación |
| DOC-02 / paquete 02 | Abierto | Corregir el generador del inventario para derivar las conclusiones de sus recuentos; regenerar el manifiesto y verificar igualdad entre mediciones, conclusiones y reporte |
| DOC-03 / reproducibilidad | Abierto | Resolver módulos ausentes `src/anti_blocking.py`, `src/sync_dashboard.py`, `src/continuous_commune_crawler.py` y `src/classify_sinim_evidence_lmstudio.py`; revisar rutas absolutas y ejecutar un lote acotado antes de recomendar los lanzadores |
| DOC-04 / paquete 04 | Abierto | Reconciliar el ledger con la evidencia actual; cada brecha debe tener fuente, estado y siguiente acción; no inferir completitud desde presencia territorial |
| DOC-05 / paquetes 05–11 | Planificado | Preparar piloto de 50–100 documentos, extracción por página, recuperación y evaluación con citas y abstención ante falta de evidencia |
| DOC-06 / paquetes 18–20 | Pendiente de verificación | Comprobar alojamiento público, DNS/TLS y operación; decidir migración a VPS con respaldo y reversión antes de ejecutarla |

## Cómo retomar

**Primer bloque recomendado: cerrar la reproducibilidad del inventario y del snapshot (paquetes 01–02).**

1. Leer instrucciones locales y ejecutar `.myworld-harness/harness.ps1 preflight`.
2. Revisar rama, revisión y cambios previos. El archivo no seguido `data/bcn_sparql_all_orz.json` ya existía al comenzar esta tarea: conservarlo y revisar su procedencia antes de incorporarlo.
3. Trabajar sobre una copia del dashboard para probar `src/build_public_snapshot.py`; este programa sobrescribe JSON, JS, HTML y descargas del directorio recibido.
4. Corregir el inventario y comparar filas, fuentes y exportaciones; registrar fecha, revisión y resultados reales.
5. Actualizar los estados de los paquetes 01–02 solo cuando pasen sus criterios de aceptación. Luego priorizar cobertura y piloto documental.

No reanudar los lanzadores de crawler como paso automático de reentrada: además de los módulos ausentes, existe un [incidente documentado de LM Studio/GPU](MW-P090-0015-incidente-lmstudio-gpu.md). Revisar límites, recuperación y autorización antes de una nueva ejecución prolongada.

## Mapa de documentación

- [README en español](../README.md) y [en inglés](../README.en.md): entrada y uso local.
- [Inventario documental](INVENTARIO-DOCUMENTAL-P090.md): unidades y corte local.
- [Plan maestro](PLAN-MAESTRO-P090.md): arquitectura objetivo, decisiones y criterios.
- [Backlog](BACKLOG-P090.md): 24 paquetes; sus propuestas no prueban implementación.
- [Handoff Antigravity](HANDOFF-ANTIGRAVITY-P090.md) y [handoff de despliegue](CHECKOUT-HANDOFF-P090.md): antecedentes históricos; verificar antes de ejecutar.

## Entrega y límites

Superficie de escritura: `README.md`, `README.en.md` y documentación Markdown de `docs/`. Sin cambios de código, datos, configuración ni infraestructura. No se creó Issue externo ni se realizó commit, push o publicación; vincular el `task_id` a su Issue canónico antes de integrar, cuando se autorice.

Verificación: preflight aprobado con aviso de cambio previo; recuentos locales de snapshot, registro municipal (1.406 filas), CSV y PDF. `git diff --check`, enlaces relativos de los ocho documentos y ausencia de marcadores de conflicto: aprobados. Gate `quality`: aprobado (`python -m compileall -q src`, exit 0). La compilación no comprueba imports ni ejecución; esta revisión no equivale a una prueba funcional del pipeline ni del sitio.

Rollback: revertir únicamente el diff documental de `P090-20260915-documentacion`, preservando cambios posteriores y el archivo de datos preexistente. No usar restauración global del checkout.
