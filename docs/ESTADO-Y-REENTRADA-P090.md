# P090 — Estado y reentrada

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
