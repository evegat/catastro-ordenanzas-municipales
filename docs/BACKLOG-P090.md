# Backlog ejecutable P090

Task ID padre: `P090-20260908-plan-publico`. Fecha: 2026-09-08.
Todos los paquetes están **pendientes**. Este archivo describe trabajo; no acredita implementación.
Cada paquete usa `P090-20260908-plan-publico-NN` como identificador estable. Si hay Issue canónico, conservar ese identificador y registrar su URL antes de integrar; no crear Issues externos sin autorización vigente.

Consultar [plan maestro](PLAN-MAESTRO-P090.md) y [handoff](HANDOFF-ANTIGRAVITY-P090.md).
Superficies siguientes son propuestas de trabajo futuro; confirmar archivos existentes antes de crear estructuras nuevas.

## 01. Corregir cifras públicas

- Entradas: README en ambos idiomas, snapshot, generador, mapa y descargas.
- Trabajo: definir unidades y corte; derivar cifras de filas elegibles; quitar cifras manuales divergentes y distinguir cobertura territorial/exhaustividad.
- Salida: generador y superficies públicas coherentes, reporte de conciliación.
- Aceptación: conteos por fuente/comuna y total coinciden; descargas corresponden al mismo corte; ninguna promesa de exhaustividad sin evidencia.
- Dependencias: inventario 02 para cifra de archivos; puede comenzar en paralelo.
- Responsable/superficie: integrador con modelo intermedio; archivos compartidos de generación y presentación.

## 02. Inventario documental

- Entradas: registros, directorios documentados y datos externos usados por scripts.
- Trabajo: contar registros, binarios, hashes únicos, normas/versiones y texto disponible; registrar archivos faltantes y rutas no portables.
- Salida: manifiesto de inventario y conciliación con snapshot; no mover originales.
- Aceptación: cada categoría tiene definición, fecha y origen; referencias remotas no cuentan como PDF local.
- Dependencias: ninguna. Responsable: código sin LLM; superficie de reporte de inventario.

## 03. Protocolo de subagentes y ahorro

- Trabajo: comprobar modelos disponibles en el ejecutor, asignar por capacidad y definir presupuesto por lote, custodia y formato de salida.
- Salida: matriz proveedor/modelo/capacidad/costo vigente y plantilla de lote.
- Aceptación: tareas sin superposición, presupuestos explícitos, medición real o aproximación declarada y responsable de integración.
- Dependencias: ninguna. Responsable: coordinador; documentación operativa.

## 04. Priorización de cobertura

- Entradas: ledger, fuentes verificadas y manifiesto 02.
- Trabajo: ordenar municipios según brechas, recuperabilidad, equilibrio territorial y temas; no sumar categorías superpuestas.
- Salida: cola de lotes de 10–15 municipios con fuente y motivo de prioridad.
- Aceptación: cada municipio tiene responsable, estado y siguiente acción verificable.
- Dependencias: 02. Responsable: agente económico; salida separada de datos maestros.

## 05. Descargar lote piloto

- Trabajo: elegir 50–100 documentos variados; descargar con controles y guardar originales/manifiesto; incluir escaneados y modificaciones.
- Salida: lote reanudable con hashes, bytes, URL, fechas y fallos.
- Aceptación: archivos válidos, repetición idempotente, ningún error silencioso ni original sobrescrito.
- Dependencias: 02, 03. Responsable: código; almacenamiento de originales y manifiesto del lote.

## 06. Extraer texto y Markdown

- Trabajo: extracción por página; OCR selectivo; Markdown derivado sin perder la referencia al original.
- Salida: texto/JSON por página, Markdown y versión del extractor.
- Aceptación: documentos fallidos identificados; páginas y secciones rastreables; tablas revisadas.
- Dependencias: 05. Responsable: implementación intermedia; módulo de extracción y derivados.

## 07. Validar texto

- Trabajo: controles automáticos y revisión visual de casos digitales, escaneados, tablas y fallos; ampliar revisión si se detecta patrón.
- Salida: informe por documento con elegibilidad para índice y cola de reparación.
- Aceptación: no indexar páginas vacías o texto defectuoso como extracción exitosa; muestra y limitaciones declaradas.
- Dependencias: 06. Responsable: revisor separado; informe de calidad.

## 08. Generar fragmentos

- Trabajo: segmentar por estructura y conservar encabezados, páginas, artículo, versión, hash y URL.
- Salida: chunks versionados con identificadores estables.
- Aceptación: trazabilidad al original, ausencia de cruces entre documentos y repetición sin duplicados.
- Dependencias: 07. Responsable: código/intermedio; segmentador y derivados.

## 09. PostgreSQL y búsqueda híbrida

- Trabajo: registrar decisión de infraestructura, esquema, migraciones y carga idempotente; elegir embedding mediante evaluación acotada.
- Salida: base local de prueba, índice textual/vectorial, consulta con filtros y guía de reproducción.
- Aceptación: reconciliación de conteos, filtros territoriales correctos y recuperación evaluable; registrar modelo/dimensión/revisión.
- Dependencias: 08; autorización aplicable para dependencias/infraestructura. Responsable: intermedio; esquema y módulo de búsqueda.

## 10. Chat piloto

- Trabajo: API limitada, recuperación, generación con citas y pestaña Asistente del sitio actual; separar conteos estructurados de preguntas documentales.
- Salida: recorrido pregunta-respuesta-fuente local y preparado para VPS; abrir pestaña desde ficha con contexto documental.
- Aceptación: navegación integrada en ordenanzas.evegat.cl, sin claves en navegador, citas construidas desde resultados, errores seguros, catálogo utilizable sin chat; no entregar una aplicación pública separada.
- Dependencias: 09 y contrato mínimo 13. Responsable: backend y frontend en superficies aisladas.

## 11. Evaluación del RAG

- Trabajo: conjunto de 30–50 preguntas, partición de prueba, evaluación de recuperación, citas, abstención, territorio y vigencia; pruebas de instrucciones maliciosas en documentos.
- Salida: resultados reproducibles con modelo, corpus, costos, latencias y fallos.
- Aceptación: criterios del plan maestro; no declarar calidad general desde una demostración aislada.
- Dependencias: 10. Responsable: revisor independiente; conjunto e informe de evaluación.

## 12. Ampliación con subagentes

- Trabajo: ejecutar cola 04 con lotes aislados, agotar listados y verificar documentos candidatos.
- Salida: nuevos originales y evidencias, exclusiones y pendientes; promoción centralizada.
- Aceptación: medir documentos nuevos aceptados, duplicados, costo y mejora de cobertura; no promover por mera clasificación de un LLM.
- Dependencias: 03, 04 y descarga idempotente 05. Responsable: agentes económicos por municipio; integrador único para maestros.

## 13. Versiones y relaciones normativas

- Trabajo: separar norma/documento/versión; incorporar relaciones de aprobación, modificación y derogación con evidencia.
- Salida: esquema mínimo antes del chat; enriquecimiento progresivo posterior.
- Aceptación: fecha o vigencia desconocida permanece desconocida; relaciones inferidas diferenciadas de verificadas.
- Dependencias: 02 para esquema, 07 para enriquecimiento. Responsable: intermedio + revisor de casos ambiguos; modelo de datos.

## 14. Propuestas visuales

- Trabajo: tres variantes del plan maestro con mismos datos y estados; escritorio y móvil, buscador, ficha y chat.
- Salida: propuestas revisables y recomendación; referencia evegat.cl comprobada al diseñar.
- Aceptación: Eduardo elige estilo antes de implementación completa; contraste y legibilidad considerados.
- Dependencias: puede comenzar con datos sintéticos rotulados; cifras públicas finales dependen de 01.
- Responsable: diseño; prototipos aislados del sitio actual.

## 15. Implementación visual

- Trabajo: aplicar propuesta elegida al catálogo, filtros, ficha, mapa, metodología y chat.
- Salida: candidato local navegable; evitar migración de framework innecesaria.
- Aceptación: flujos y estados vacíos/error comprobados, cifras derivadas, sin pérdida de funciones existentes.
- Dependencias: 01, 14 elegido; integración de chat depende de 10. Responsable: frontend.

## 16. Rendimiento y accesibilidad

- Trabajo: medir antes/después, diferir mapa/datos cuando convenga, revisar teclado, foco, contraste, móvil y errores.
- Salida: informe y correcciones de impacto demostrado.
- Aceptación: búsqueda/lectura/descarga operan a 360 px y con teclado; reportar métricas, entorno y límites de la prueba.
- Dependencias: 15. Responsable: revisor frontend; evitar edición simultánea con 15.

## 17. Metodología pública

- Trabajo: describir fuentes, unidades, cobertura, corte, límites de vigencia, licencias y canal de corrección.
- Salida: metodología, ficha de dataset, aviso de privacidad propuesto y descargas consistentes.
- Aceptación: distinguir licencia de código/documentos; no prometer exhaustividad; canal probado sin enviar mensajes externos no autorizados.
- Dependencias: 01, 02; privacidad final depende de 22. Responsable: documentación.

## 18. Alojamiento y costo operativo

- Trabajo: inspeccionar VPS actual de ordenanzas.evegat.cl, servicios, proxy, puertos, recursos y copias; dimensionar backend, PostgreSQL/pgvector, originales, ingestión y Umami en esa VPS. Comparar inferencia local frente a API externa como decisión pendiente, sin cambiar el destino del servicio web.
- Salida: topología compatible con software existente, entorno de prueba, costo incremental fechado, presupuesto solicitado, copias/restauración, límites y apagado independiente del chat.
- Aceptación: destino VPS y pestaña RAG respetados; base no expuesta; ingestión acotada; sitio actual preservado; restauración ensayada antes de producción; no desplegar ni cambiar permisos al preparar el diseño.
- Dependencias: 09–11 para medición; puede investigar antes. Responsable: coordinador técnico.

## 19. Presentación pública

- Trabajo: relato del problema, utilidad, alcance y límites; tres consultas demostrables, capturas, guía y texto de difusión.
- Salida: paquete de presentación basado en el candidato real.
- Aceptación: cifras del corte y demostraciones reproducibles; textos listos, todavía sin enviar/publicar.
- Dependencias: 11, 15–17. Responsable: documentación/producto.

## 20. Verificación y lanzamiento

- Trabajo: revisar candidato exacto, gates, enlaces, descargas, pestaña Asistente, seguridad, analítica y recuperación; preparar RDD y rollback del despliegue en la VPS actual.
- Salida: acta de candidato y, tras autorización explícita, publicación con comprobación posterior.
- Aceptación: evidencia de cada gate; SHA exacto; sin pendientes críticos; comprobar HTTPS, navegación y API en ordenanzas.evegat.cl, convivencia con servicios actuales y no exposición de base/panel; si falla, aplicar rollback autorizado.
- Dependencias: 11, 16–19, 22–24. Responsable: integrador; ninguna publicación automática por marcar este ítem.

## 21. Contrato de medición

- Trabajo: definir eventos, dimensiones, denominadores, ubicación aproximada y diferencia con comuna consultada; retención y propiedades permitidas.
- Salida: diccionario versionado basado en el plan maestro y ejemplos de payload saneado.
- Aceptación: no preguntas completas ni datos personales; eventos con emisor único; explicar estimaciones y ausencia de datos.
- Dependencias: ninguna. Responsable: coordinador producto; contrato de eventos.

## 22. Herramienta de analítica

- Trabajo: validar Umami en la VPS actual como preferencia, comparar Plausible CE/GA4 y elegir versión; integrar primero en entorno de prueba y separar base/usuario de los datos RAG.
- Salida: decisión y configuración documentada, exclusión de tráfico interno y aviso de privacidad coherente.
- Aceptación: país/región/ciudad comprobados cuando disponibles, desconocido soportado, sin GPS, sin duplicación, panel privado, sitio funciona con bloqueador.
- Dependencias: 18, 21; autorización de infraestructura/captación productiva. Responsable: implementación intermedia; analítica y configuración aisladas.

## 23. Calidad y costo del chat

- Trabajo: registrar modelo, tokens, tarifa versionada, costo, latencia, suficiencia, citas y feedback, sin conversación íntegra por defecto.
- Salida: telemetría por solicitud con IDs efímeros y redacción de errores.
- Aceptación: una solicitud contabilizada una vez; prueba de cálculo y fallos; no confundir costo estimado con factura.
- Dependencias: 10, 21. Responsable: backend; coordinar superficie con 10.

## 24. Tablero de seguimiento

- Trabajo: vistas de adquisición, uso, calidad y operación; filtros por período; ubicaciones agregadas y volúmenes pequeños protegidos.
- Salida: tablero privado y guía de lectura/revisión mensual, sin crear automatizaciones por defecto.
- Aceptación: acciones controladas conciliadas con eventos; fórmulas y denominadores visibles; métricas útiles para priorizar trabajo.
- Dependencias: 22, 23. Responsable: analítica; tablero/configuración.

## Estados y cierre de paquetes

Estados: pendiente -> en curso -> en revisión -> verificado. Alternativas: bloqueado (con causa y siguiente acción) o descartado (con decisión de Eduardo).

Por paquete registrar: ID, estado, responsable, worktree/rama, base SHA, superficie, presupuesto, inicio, resultado, archivos, pruebas ejecutadas, fallos, pendientes, rollback y siguiente paso. Un archivo nuevo no basta para marcar verificado. Actualizar el estado solo con evidencia, conservando el historial de cambios.
