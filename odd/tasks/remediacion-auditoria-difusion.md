---
type: odd-feature
feature_id: FEAT-P090-REMEDIACION-AUDITORIA
task_id: AUD-P090-DIFUSION-20260930-REMEDIACION
project: P090
status: in_progress
created_at: 2026-09-30
updated_at: 2026-09-30
tdd_mode: on
tdd_runner: python scripts/test_audit_remediation.py
engram_topic: odd/P090/remediacion-auditoria-difusion/tasks
---

# Remediación de Bloqueantes de Auditoría Independiente P090

## 1. Problema y Objetivo
La auditoría técnica independiente (Task `AUD-P090-DIFUSION-20260930`) emitió dictamen NO-GO para la difusión pública masiva debido a:
- C01: Desfase entre mapa/resumen (7.321) y snapshot (7.482), además de cifras 7.450 y 204/219 desalineadas.
- C02: Inclusión de roles de avalúo SII (ej. Villa Alegre) no correspondientes a ordenanzas municipales.
- C03: Fabricación de fechas `2026-01-01` y comodín `-01-01` en `src/promote_extracted_evidence.py`.
- C04: Botón de Chatcito oculto dentro del modal de descargas y búsqueda territorial con falsos positivos por subcadena (Talca/Talcahuano, etc.).
- C05: Desbordamiento horizontal móvil (600px en viewports 360px), barreras de teclado y contraste inferior a 4.5:1.

## 2. Plan de Trabajo TDD (RED -> GREEN -> REFACTOR)
1. C02: Crear política de admisibilidad, cuarentenar roles SII y documentos ajenos a ordenanzas.
2. C03: Eliminar fallbacks artificiales de fechas en `src/promote_extracted_evidence.py` y `src/build_markdown_corpus.py`. Conservar S/F.
3. C01: Regenerar mapa, resumen comunal, microdatos, XLSX, ZIP y snapshot conciliando todas las superficies con un único corte depurado.
4. C04: Reparar DOM del chat y desambiguación territorial por longitud/delimitación de tokens en `dashboard/asistente_chat.js`.
5. C05: Reparar reflujo móvil en CSS/HTML, atributos y ciclo de foco del modal, etiquetas y ratios de contraste WCAG AA.
6. Pruebas de regresión automatizadas y manuales.
