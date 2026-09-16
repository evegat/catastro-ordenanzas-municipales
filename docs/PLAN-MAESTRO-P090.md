# Plan maestro P090: corpus, RAG, experiencia pública y analítica

> **Revisión 2026-09-15:** ver [estado y reentrada](ESTADO-Y-REENTRADA-P090.md) para evidencia local vigente y prioridades. El contenido inferior conserva el plan o reporte histórico; sus cifras y pruebas no se revalidan por esta actualización. Proyecto en evolución.

Fecha: 2026-09-08. Estado: **plan listo para ejecución; implementación pendiente**.
Task ID: `P090-20260908-plan-publico`.
Base revisada: `34a1034893564e6c1d6a96cb487d020cb87c130a` (main).
Responsable de integración: Eduardo Vega. Destinatario operativo: Antigravity.
Superficie de esta entrega: exclusivamente estos tres documentos en `docs/`.

## Cómo usar este paquete

1. Leer este documento para entender decisiones, arquitectura y límites.
2. Ejecutar [BACKLOG-P090.md](BACKLOG-P090.md) por dependencias. Sus números conservan la lista acordada con Eduardo.
3. Usar [HANDOFF-ANTIGRAVITY-P090.md](HANDOFF-ANTIGRAVITY-P090.md) como instrucción de inicio y formato de continuidad.

La solicitud actual autoriza preparar este plan local. Este documento no otorga por sí mismo permisos de publicación, gasto, instalación productiva o cambios de credenciales. Al recibir una orden de implementación, avanzar con el trabajo local reversible autorizado y preparar candidatos concretos antes de pedir autorizaciones externas pendientes.

## Resultado que se quiere alcanzar

Un catastro público de ordenanzas municipales de Chile que permita encontrar y descargar documentos oficiales, comprender cobertura y límites, y consultar un asistente que responda con evidencia documental verificable. La analítica debe informar quiénes llegan en términos agregados, desde dónde, cómo usan el producto y dónde encuentran problemas.

**Aclaración de Eduardo del 2026-09-08:** alojar el conjunto en la VPS junto al software actual de `https://ordenanzas.evegat.cl`. El RAG será una **pestaña del mismo sitio**, no un producto separado. Este destino está decidido; capacidad, distribución actual de servicios y configuración de producción siguen pendientes de inspección. La referencia a GitHub Pages en el perfil local es evidencia de configuración histórica y debe reconciliarse con el despliegue vigente informado por Eduardo.

El lanzamiento no exige demostrar exhaustividad nacional. Sí exige consistencia de cifras, trazabilidad, límites visibles y evaluación del asistente. El objetivo de recolección exhaustiva se conserva como programa de trabajo incremental.

## Base de evidencia y brechas

Lectura local realizada durante esta conversación; revalidar al comenzar cada lote:

| Fuente | Estado observado | Consecuencia |
|---|---|---|
| `dashboard/status_data.json` | 7.226 filas en 346 comunas: 5.881 BCN, 1.335 Municipalidad y 10 Diario Oficial / BCN | El agregado de 1.345 no debe interpretarse como 1.345 ordenanzas municipales distintas y vigentes |
| `README.md` | Conviven 3.015 y 7.186 registros | Reconciliar documentación con un corte canónico |
| `data/official_pdfs/` | 10 PDF dentro del repositorio durante el inventario | Separar referencias, verificaciones remotas y originales archivados; inventariar también rutas externas documentadas |
| `data/national_coverage_ledger.json` | Corte 2026-08-30; 345 municipalidades; 142 con documentos verificados; 3 sin brechas; `coverage_complete=false` | Ledger y snapshot tienen cortes distintos; no mezclar sus conteos |
| Mismo ledger | 153 sin fuente candidata; 153 sin extracción; 203 sin documento municipal verificado; 50 listados no agotados; 43 sitios no verificados; 28 documentos sin resolver | Las categorías pueden superponerse; no sumar como municipalidades diferentes |
| Revisión de arquitectura | No se identificó un flujo completo de texto, chunks, embeddings, PostgreSQL y chat | Implementar y evaluar un recorrido completo antes de escalar |
| `docs/MW-P090-0015-incidente-lmstudio-gpu.md` | Incidente histórico y condiciones de reanudación | No reactivar cargas persistentes ni watchdog anterior sin controles y autorización específica |

No se volvió a descargar cada URL ni se verificó jurídicamente la vigencia de cada norma. La fecha `updated_at` del snapshot tampoco constituye prueba de verificación actual de todas sus filas. La etiqueta `verified` existente prueba el contrato que la produjo, no exhaustividad, vigencia ni calidad textual.

## Orden de ejecución y puntos de aceptación

| Etapa | Ítems | Resultado exigido para avanzar |
|---|---|---|
| A. Base confiable | 1, 2, 3, 4 y 21 | Cifras reconciliadas, inventario, protocolo de agentes, brechas priorizadas y contrato de medición |
| B. Recorrido documental | 5, 6, 7, 8 | Lote de 50–100 documentos con originales, texto, páginas y fragmentos trazables |
| C. RAG local | 9, 10, 11; esquema mínimo de 13 | Recuperación híbrida y respuestas evaluadas, con citas y abstención |
| D. Producto | 14, 15, 16, 17 | Diseño elegido, flujos verificados, metodología y descargas coherentes |
| E. Operación y medición | 18, 22, 23, 24 | Infraestructura elegida, presupuesto, eventos probados y tablero privado operativo |
| F. Presentación | 19, 20 | Candidato revisado, demostraciones reproducibles, autorización de publicación y comprobación posterior |
| Programa continuo | 12 y profundización de 13 | Nuevos documentos aceptados y relaciones normativas sin inflar conteos |

No bloquear el prototipo visual por el corpus ni la investigación de fuentes por el chat. No integrar resultados dependientes antes de superar su punto de aceptación. Evitar promesas de duración hasta medir el primer lote, la proporción de OCR y la infraestructura disponible.

## Arquitectura propuesta

```text
BCN / sitios municipales / Transparencia / otras fuentes oficiales validadas
  -> manifiesto de candidatos y evidencias
  -> originales inmutables identificados por SHA-256
  -> texto por página + Markdown derivado + control de extracción
  -> fragmentos por estructura normativa
  -> PostgreSQL: metadatos + búsqueda textual + pgvector
  -> servicio de consulta y generación
  -> catálogo público + ficha documental + chat con fuentes

Eventos de uso -> analítica agregada
Métricas del servidor -> costo, latencia, errores y evaluación del RAG
```

Mantener la tecnología del frontend inicialmente y agregar un servicio pequeño para el chat en **la misma VPS del sitio actual**. No migrar de framework por motivos cosméticos. Inspeccionar cómo está servido `ordenanzas.evegat.cl` antes de definir cambios. No asumir Docker, Coolify, GPU, PostgreSQL ni capacidad libre por el solo hecho de que exista la VPS.

### Topología objetivo en la VPS

```text
Internet -> HTTPS ordenanzas.evegat.cl -> proxy actual
  /                 -> frontend actual: Explorar | Asistente | Datos y metodología
  /api/rag/*        -> servicio RAG privado detrás del proxy
                       -> PostgreSQL + pgvector en red privada
                       -> originales y derivados en almacenamiento persistente
                       -> proveedor de generación o inferencia local aprobada

Analítica Umami -> servicio en la VPS + base/usuario separados
                  panel administrativo protegido; ingestión pública limitada
Trabajos de ingestión/OCR -> proceso por lotes con límites y checkpoints
```

Rutas propuestas sujetas a compatibilidad con el proxy existente. Mantener el mismo origen para el chat evita una aplicación pública adicional; la API sigue siendo un componente separado internamente. No exponer PostgreSQL, credenciales ni consola de administración a Internet. Evitar colisiones con servicios existentes; no tocar puertos, DNS o reglas del proxy sin revisar estado y preparar rollback.

La pestaña **Asistente** comparte navegación, diseño y filtros con el catálogo. Desde una ficha, “Preguntar sobre esta ordenanza” abre esa pestaña con el documento seleccionado. El backend devuelve respuesta y citas; las fuentes se abren desde la propia interfaz. Estado de carga, cancelación, falta de evidencia e indisponibilidad deben ser visibles.

La revisión del subagente identificó `.github/workflows/deploy-pages.yml` con publicación configurada al hacer push a main. Antes de cualquier push, inspeccionar ese flujo y acordar su conciliación con VPS: no disparar publicación involuntaria ni asumir que refleja el sitio vigente. No se encontró configuración de VPS en la búsqueda local acotada; verificarla en el servidor durante la implementación autorizada.

“Todo en la VPS” incluye frontend, API, base, documentos, trabajos de ingestión y analítica. La **inferencia del modelo** requiere una decisión explícita: comprobar si el usuario exige también inferencia íntegramente en VPS o acepta API externa. No asumir que un servidor sin GPU puede servir adecuadamente un modelo generativo. Preparar dimensionamiento de ambas opciones y no contratar ni conectar un proveedor externo por defecto. El servicio de chat debe estar alojado en la VPS en cualquiera de las dos opciones.

Tomar inferencia y embeddings en VPS como hipótesis inicial a dimensionar. Una API externa sería una excepción explícita al alojamiento íntegro, no una dependencia introducida silenciosamente. En ningún caso la operación pública puede depender del computador de Eduardo. GA4 se conserva como comparación solicitada; la preferencia coherente con autohospedaje es Umami, y elegir GA4 requiere aceptar expresamente el procesamiento externo.

Antes de desplegar: inventario de CPU/RAM/disco, servicios y puertos, almacenamiento y copias, versiones y estado del proxy/TLS; medir un lote OCR y una carga de chat acotada. Limitar CPU/memoria/concurrencia de ingestión para que no degrade el sitio actual. Separar configuración, usuarios de base y volúmenes; probar restauración en entorno aislado. Primero preparar entorno de prueba sin sustituir el sitio público, luego promover un candidato exacto autorizado.

Gate VPS: prueba conjunta de catálogo, chat e ingestión con recursos y latencias registrados; acceso por mismo dominio; reinicio recuperable; restauración probada; no dependencia del PC; PostgreSQL y panel administrativo protegidos; rollback conserva originales y permite reconstruir índice. Definir umbrales de recursos sobre el inventario real antes de ejecutar la carga.

### Contrato documental

Separar identidad de la norma, versión del documento, archivo descargado y fragmento. Un hash identifica bytes; dos PDF diferentes pueden contener la misma norma, y un mismo archivo puede mencionar varias normas.

Campos mínimos propuestos:

- `document_id`, `version_id`, `source_record_id`, `municipality_id`, `commune_codes`.
- `title`, `act_type`, `number`, `publication_date`, `effective_date`, con valores nulos cuando se desconocen.
- `source_listing_url`, `original_url`, `resolved_url`, `retrieved_at`, `sha256`, `mime_type`, `bytes`, `storage_key`.
- `verification_status`, `verification_method`, `extraction_status`, `extractor_version`, `page_count`, `quality_flags`.
- `legal_status`: desconocido, vigente verificado, modificado o derogado con evidencia; nunca asignar vigencia por defecto.
- Relaciones `modifies`, `repeals`, `approves`, `replaces`, con fuente y estado de revisión.

Preservar datos brutos. Tratar fecha deducida de un nombre de archivo como inferencia, no como fecha oficial. Contar por separado registros, archivos únicos, normas y versiones.

### Descarga, extracción e indexación

- Reusar scripts válidos; resolver dependencias y rutas externas documentadas antes de sustituirlos.
- Descargar con límites por dominio, tiempo máximo, tamaño máximo y como máximo dos reintentos transitorios. Respetar restricciones de acceso; no eludir bloqueos.
- Guardar checkpoint por lote. No sobrescribir originales; un cambio de contenido genera otra versión.
- Preferir texto oficial estructurado cuando exista. Para PDF digital, probar la extracción disponible; enviar a OCR solo páginas que lo requieran.
- Mantener JSON por página además de Markdown. Preservar encabezados, tablas, artículos y referencias; registrar pérdidas.
- Fragmentar por título/capítulo/artículo/inciso. Tamaño inicial orientativo: 400–800 tokens, ajustable por evaluación; no partir una tabla o artículo corto sin necesidad. Conservar jerarquía, páginas, identificador y hash.
- Elegir un embedding multilingüe según evaluación en español, licencia y recursos. Registrar nombre, revisión y dimensión. No mezclar vectores incompatibles; recalcular solo lo cambiado.
- PostgreSQL + búsqueda textual en español + pgvector. Combinar ranking lexical y semántico; aplicar filtros territoriales y documentales. Empezar sin reranker; añadirlo solo si mejora el conjunto de evaluación a costo aceptable.
- La carga debe ser idempotente: repetir un lote no aumenta documentos ni chunks. Un cambio de extractor o segmentación queda versionado.

### Servicio y experiencia del chat

- Entrada: pregunta y filtros explícitos, con límites de longitud. Salida: respuesta, citas estructuradas, documentos utilizados y estado de suficiencia de evidencia.
- Pedir comuna o fecha si cambia materialmente la respuesta. No mezclar reglas de distintas comunas sin explicarlo.
- Citar documento, artículo o página y enlace original. La aplicación construye citas desde identificadores recuperados; no aceptar enlaces inventados por el modelo.
- Contestar que no hay evidencia suficiente cuando corresponda. Separar ausencia en el corpus de inexistencia de una ordenanza.
- Consultas de conteos y cobertura usan datos estructurados, no generación probabilística.
- Tratar texto recuperado como datos no confiables: ignorar instrucciones incrustadas; herramientas y secretos no quedan disponibles por orden de un documento.
- Claves solo en servidor. Límites de solicitudes, concurrencia, tokens y presupuesto; mensajes de indisponibilidad sin filtrar trazas.
- No descargar URLs arbitrarias proporcionadas por el visitante. Reutilizar documentos registrados y verificar redirecciones durante ingestión para evitar acceso a redes privadas.
- El catálogo y las descargas siguen funcionando si el chat está deshabilitado.

### Evaluación inicial propuesta

Crear 30–50 preguntas con documentos y pasajes esperados: búsquedas exactas, paráfrasis, comparación territorial, artículos extensos, tablas, preguntas temporales y casos sin respuesta. Separar un conjunto de prueba que no se use para ajustar prompts.

Umbrales iniciales del piloto, a revisar explícitamente después del primer resultado:

- 100% de documentos indexados con hash, fuente y referencias de página/sección; los fallidos quedan fuera y registrados.
- Cero duplicaciones en una repetición del lote; conteos del manifiesto, texto e índice reconciliados.
- Pasaje pertinente en los primeros 10 resultados en al menos 90% de preguntas respondibles del conjunto.
- 100% de citas emitidas resolubles; al menos 95% de afirmaciones sustantivas sustentadas según revisión manual.
- Cero afirmaciones de vigencia sin evidencia y cero confusiones territoriales en el conjunto de lanzamiento.
- Al menos 90% de abstención correcta en los casos sin evidencia.
- Medir p50/p95 de latencia y costo por respuesta; acordar umbral de servicio y presupuesto antes de abrir acceso público.

Estos porcentajes son criterios propuestos, no resultados logrados ni garantía general. Conservar fallos y tamaño del conjunto junto a los resultados.

## Recolección ampliada

Lotes iniciales de 10–15 municipalidades sin superposición. Priorizar enlaces recuperables y listados incompletos, luego fuentes faltantes, considerando además equilibrio territorial y variedad temática. El piloto técnico no reemplaza la política de exhaustividad.

Cada lote entrega candidatos, fuentes oficiales comprobadas, documentos recuperados, duplicados, exclusiones justificadas y pendientes. Registrar paginación e índices recorridos: no marcar un municipio completo por encontrar un PDF. Revisar semánticamente ordenanza, decreto aprobatorio, modificación, tarifa y documento ajeno antes de contar.

Medir documentos nuevos aceptados por hora y costo, tasa de duplicados, fallos y mejora de cobertura. Los agentes de descubrimiento no escriben el snapshot maestro: un integrador valida y promueve.

## Diseño y producto

Referencia visual observada en evegat.cl durante esta conversación: fondo marfil, azul profundo, acentos verdes, títulos serif y separadores finos. Crear alternativas propias; no asumir que copiar estructura completa funciona para un catálogo.

1. **Archivo cívico (preferencia inicial):** marfil, azul profundo, verde discreto; énfasis en búsqueda y documentos.
2. **Atlas territorial:** gris cálido, petróleo y mapa más visible; énfasis comunal.
3. **Biblioteca normativa:** arena, grafito y terracota; énfasis en lectura y comparación.

Presentar las tres con los mismos datos y estados de escritorio/móvil. La elección visual de Eduardo antecede a la implementación completa. No requiere detener inventario o extracción.

Navegación propuesta: Explorar, Asistente, Datos y metodología. **Asistente es la pestaña RAG dentro de ordenanzas.evegat.cl.** Ficha con título, comuna, tipo, fecha conocida, estado de evidencia, original y consulta contextual. Mostrar corte del corpus y límites. Corregir cifras manuales y caracteres dañados después de comprobar la codificación real, sin convertir a ciegas.

Medir carga inicial antes de optimizar. El snapshot observado ronda 6 MB; evaluar carga por demanda y mapa diferido. Revisar teclado, foco, contraste, estados vacíos, errores y lectura a 360 px. Evitar que la presentación inicial dependa de cargar todos los datos.

## Analítica: alcance y elección

### Recomendación provisional

**Umami autohospedado en la misma VPS** como primera alternativa, condicionado a confirmar capacidad, mantenimiento y versión elegida. La decisión final se registra antes de instrumentar producción. Código abierto no significa costo operativo cero.

| Opción | Encaje | Trabajo o límite a considerar |
|---|---|---|
| Umami autohospedado | Analítica de páginas, procedencia, dispositivos y eventos; control del despliegue | Actualizaciones, copias, acceso privado y configuración geográfica/proxy |
| Plausible Community Edition | Alternativa abierta para analítica sencilla | Comprobar funciones concretas de la edición y versión; no asumir paridad con Cloud |
| Google Analytics 4 | Alternativa si se prioriza el ecosistema Google | Configurar cuenta, tratamiento de datos y controles; operación con un tercero |

No activar varias herramientas en paralelo sin una razón medida. No se fijan precios sin cotización actual. Preparar cálculo de costo mensual de alojamiento, almacenamiento, inferencia, copias y mantenimiento.

### Qué significa ubicación de acceso

País, región y ciudad son **aproximaciones derivadas de la conexión** cuando el proveedor dispone de datos. VPN, redes móviles, proxies y bases geográficas pueden producir errores o valores desconocidos. No pedir GPS ni deducir domicilio, institución o comuna real de una persona.

Separar siempre:

- `visitor_country/region/city`: ubicación aproximada de acceso, gestionada por la herramienta.
- `selected_commune_code`: comuna consultada dentro del catálogo.

Verificar que la configuración elegida entrega región/ciudad: su presencia en la documentación no garantiza que el proxy del despliegue aporte esa resolución. En tableros compartidos, agrupar ubicaciones con pocos accesos; umbral inicial propuesto de 10 visitas, sujeto a revisión.

### Dimensiones y eventos

Visitas y páginas, procedencia/referrer saneado, campañas UTM permitidas, dispositivo, navegador, sistema operativo, ubicación aproximada y tendencias temporales. No interpretar visitantes estimados como personas únicas comprobadas ni prometer identificar quién visitó.

| Evento | Propiedades permitidas propuestas | Utilidad |
|---|---|---|
| `search_submitted` | cantidad de resultados, filtros, tipo de búsqueda | Uso del buscador |
| `search_no_results` | filtros, tipo de búsqueda | Brechas de recuperación |
| `filter_applied` | nombre del filtro, valor catalogado | Interés territorial/temático |
| `document_opened` | document_id, fuente, materia | Documentos consultados |
| `source_opened` | document_id, dominio oficial | Acceso a evidencia original |
| `download_requested` | document_id o dataset_id, formato | Intención de descarga; no prueba de descarga terminada |
| `chat_submitted` | conversation_id efímero, filtros | Demanda del chat |
| `chat_completed` | request_id efímero, suficiencia, número de citas | Respuestas entregadas |
| `chat_feedback` | request_id efímero, valoración cerrada | Utilidad percibida |
| `client_error` | código saneado, sección | Problemas de interfaz |

Definir `event_version` y un responsable de emisión por evento para evitar duplicados entre navegador y servidor. No incluir texto libre de preguntas/búsquedas, IP sin procesar, correo, identificador personal, URL con consultas sensibles ni contenido normativo completo en la analítica. Las búsquedas fallidas orientarán brechas por filtros; conocer su texto requeriría una decisión adicional de captura y privacidad.

La telemetría del servidor guarda por solicitud: modelo/revisión, tokens de entrada/salida, costo estimado con versión de tarifa, latencia, errores, versión del corpus y resultado de recuperación. No necesita guardar conversaciones completas. No enviar esta telemetría detallada a Google por defecto.

Retención inicial propuesta: eventos 90 días y agregados mensuales 12 meses, configurable y validada antes de producción. Dashboard de uso privado. Revisar aviso de privacidad y requisitos aplicables al despliegue antes de activar captación real; la herramienta por sí sola no demuestra cumplimiento. Revisar también logs del proxy, que pueden almacenar IP aunque el panel no la muestre.

### Tablero y pruebas

Cuatro vistas: adquisición (ubicación/procedencia/dispositivo), uso (búsquedas/documentos/descargas), calidad (sin resultados/errores/valoraciones) y operación RAG (latencia/costo/suficiencia).

Definir denominadores: tasa sin resultados = búsquedas sin resultados / búsquedas; tasa de feedback positivo = valoraciones positivas / valoraciones recibidas; costo medio = costo de solicitudes / solicitudes contabilizadas. Mostrar período y volumen; no extrapolar desde pocas valoraciones.

Pruebas en entorno separado: un evento por acción, filtros internos activos, propiedades saneadas, ubicación desconocida aceptada, navegación con bloqueador funcional y concordancia entre acciones controladas y panel. No eludir bloqueadores. La falta de medición no debe impedir buscar, leer o descargar.

## Subagentes y ahorro

El proveedor/modelo disponible en Antigravity debe verificarse; no asumir que ofrece los nombres de Codex. Política por capacidad:

- Sin LLM: descarga, hash, conteos, deduplicación exacta, inventario y comprobaciones deterministas.
- Modelo económico: clasificación de candidatos y extracción estructurada acotada.
- Modelo intermedio: implementación y reparación de extractores.
- Modelo más capaz: arquitectura, contradicciones, revisión de evidencia y decisiones de integración.

Si se trabaja desde Codex, candidatos a validar son luna para tareas acotadas, terra para implementación y el principal para revisión. No se afirma disponibilidad en Antigravity ni ahorro porcentual garantizado.

Máximo inicial: dos agentes de implementación y un integrador. Worktrees y superficies separadas; un responsable por paquete. No entregar historial completo: objetivo, entradas, restricciones, salida y criterio de aceptación bastan. Reportes de máximo 500 palabras más evidencia estructurada. No usar varios agentes para leer repetidamente el corpus completo.

Cada lote declara presupuesto de tokens/costo y tiempo antes de ejecutar. Si no se pueden medir tokens, registrar llamadas, duración y proveedor como aproximación explícita. No inventar presupuesto monetario aprobado. Dos reintentos transitorios como máximo; fallos persistentes pasan a pendientes y se continúa trabajo independiente.

## Riesgos y decisiones pendientes

| Riesgo o decisión | Tratamiento |
|---|---|
| Fuente inaccesible o cambiada | Conservar evidencia anterior y pendiente; no fingir actualización |
| OCR deficiente | Excluir fragmentos defectuosos y revisar muestras/documentos marcados |
| Confusión jurídica | Identidad/versiones, citas, estado desconocido y evaluación |
| Costos del chat o abuso | Cupos, límites y apagado del chat independiente del catálogo |
| Inferencia local sostenida | Respetar documento del incidente, probar controles antes de reactivar |
| Analítica incompleta | Explicitar bloqueadores, geografía aproximada y visitantes estimados |
| Cambios concurrentes | Worktree, custodia temporal y revisión antes de integración |
| Infraestructura y dependencias | Decisión documentada y autorización aplicable antes de instalar en producción |

Destino decidido: VPS actual y dominio `ordenanzas.evegat.cl`, con RAG integrado como pestaña. Quedan por decidir: dimensionamiento y presupuesto incremental, inferencia en VPS o API externa, modelo de embeddings/generación, alternativa analítica definitiva, retención final y estilo visual. Preparar pruebas locales e información comparativa sin bloquear tareas independientes.

## Fuentes técnicas consultadas el 2026-09-08

- [pgvector: búsqueda híbrida](https://github.com/pgvector/pgvector#hybrid-search).
- [PostgreSQL: búsqueda textual](https://www.postgresql.org/docs/current/textsearch-intro.html).
- [Umami: introducción y autohospedaje](https://docs.umami.is/docs).
- [Umami: datos y alcance](https://docs.umami.is/docs/faq).
- [Umami: configuración de geolocalización y exclusiones](https://docs.umami.is/docs/environment-variables).
- [Plausible: países, regiones y ciudades](https://plausible.io/docs/countries).
- [Plausible: Community Edition](https://ingest.plausible.io/blog/community-edition).
- [GA4: tratamiento regional de datos y geolocalización](https://support.google.com/analytics/answer/11598602?hl=en).

Verificar versiones y costos nuevamente al implementar. Las decisiones de arquitectura y privacidad de este plan son propuestas del proyecto, no características garantizadas por esas fuentes.
