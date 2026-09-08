# Handoff para Antigravity — P090

Fecha: 2026-09-08.
Task ID: `P090-20260908-plan-publico`.
Integration owner: Eduardo Vega.
Repositorio: `D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN`.
Base exacta revisada: `34a1034893564e6c1d6a96cb487d020cb87c130a`.
Estado entregado: **plan documentado, sin implementación ni publicación**.

## Instrucción de inicio

Lee `AGENTS.md`, `MYWORLD-HARNESS.json`, [PLAN-MAESTRO-P090.md](PLAN-MAESTRO-P090.md) y [BACKLOG-P090.md](BACKLOG-P090.md). Eduardo quiere preparar el catastro para difusión pública: corpus reproducible, RAG con citas, expansión de fuentes mediante subagentes económicos, interfaz clara cálida próxima a evegat.cl y analítica de uso con ubicación aproximada.

**Destino confirmado por Eduardo:** todo el servicio en la VPS junto al software actual de `https://ordenanzas.evegat.cl`; RAG como **pestaña Asistente en ese mismo sitio**. No construir una aplicación pública separada ni elegir otro alojamiento como supuesto. Inspeccionar despliegue real antes de editar: el perfil local todavía menciona GitHub Pages. La inferencia local en VPS frente a API externa requiere dimensionamiento y decisión; no asumir GPU ni capacidad suficiente.

Esta entrega prepara el trabajo; no constituye un envío a Antigravity ni inicia agentes externos. Cuando Eduardo te indique comenzar, ejecuta los paquetes autorizados, por dependencias y con evidencia. No vuelvas a producir solo otro plan cuando exista una orden de implementación.

## Primer bloque recomendado

1. Confirmar repositorio real, revisión, estado Git, instrucciones y custodias activas; correr `.myworld-harness/harness.ps1 preflight` antes de escribir. Usar RTK conforme a instrucciones globales del equipo.
2. Verificar los datos vivos: los números del plan son un corte observado, no una constante.
3. Abrir paquete 02 (inventario) y diagnóstico de 01 (cifras). Preparar 03 (subagentes) y 21 (medición) en paralelo solo si sus superficies están aisladas.
4. Entregar una conciliación de filas, fuentes, archivos originales y texto disponible. Corregir cifras únicamente desde una definición canónica comprobada.
5. Dejar checkpoint antes de pasar al lote documental. No iniciar recolección nacional masiva, instalación productiva o inferencia persistente para resolver este bloque.

## Distribución sugerida

- Integrador: decisiones, maestros, README/snapshot, aceptación y handoff.
- Agente A: inventario y evidencia, sin edición del snapshot.
- Agente B: contrato de analítica o revisión de fuentes en lote aislado.
- Al terminar inventario, reutilizar agentes con contexto nuevo y pequeño para extracción/implementación.

Verificar modelos disponibles en Antigravity y asignar por capacidad. Los nombres luna/terra del plan son ejemplos del entorno Codex, no una afirmación de disponibilidad aquí. Preferir scripts para tareas deterministas. No copiar el historial completo a todos los agentes. Si no hay multiagente, ejecutar secuencialmente con los mismos contratos.

## Coordinación y permisos

- Un paquete, responsable y superficie declarada por agente; usar worktrees para escritura paralela según el Harness.
- Antes de usar una rama nueva, comprobar colisiones; prefijo predeterminado `EduCodex/` salvo instrucción explícita distinta.
- Usar el mecanismo de custodia/lock vigente del proyecto; no inventar ni borrar locks de otros. Si esta revisión no tiene lock activo, adquirir uno nuevo antes de editar con otro agente.
- La custodia de esta entrega documental terminó; no se mantiene un lock activo de Codex sobre los tres archivos entregados.
- Conservar cambios ajenos. No resetear el repositorio ni limpiar datos para comenzar.
- Mantener Task ID en Issue canónico si existe. Su creación o publicación requiere autorización aplicable; documentar la ausencia como pendiente, no fabricar un número.
- Instalaciones productivas, arquitectura base, gasto, autenticación, publicación, envío y cambios de permisos conservan los requisitos de autorización de `AGENTS.md`.
- No enviar correos ni mensajes a terceros por inferencia desde este plan.
- Preparar candidato exacto y RDD antes de commit/push/PR/deploy cuando corresponda. Commits y PR en español; PR como borrador mientras requiera revisión humana.
- Revisar `.github/workflows/deploy-pages.yml` antes de cualquier push: hay publicación a Pages configurada. Conciliarla con el destino VPS sin alterar producción ni deshabilitar flujos por mera inferencia. Probar que la operación del chat no dependa del PC de Eduardo.
- Leer `docs/MW-P090-0015-incidente-lmstudio-gpu.md` antes de considerar LM Studio/GPU. No reactivar el watchdog histórico. Los controles térmicos y la autorización de ejecución persistente siguen pendientes de comprobación actual.

## Entrega documental recibida

Archivos nuevos previstos y únicos en esta entrega:

- `docs/PLAN-MAESTRO-P090.md`: arquitectura, decisiones, criterios, riesgos, analítica y fuentes.
- `docs/BACKLOG-P090.md`: los 24 paquetes con entradas, salidas, dependencias y aceptación.
- `docs/HANDOFF-ANTIGRAVITY-P090.md`: este protocolo de inicio y continuidad.

No se cambió código, datos, dependencias ni configuración pública. No se hizo commit, push o despliegue. Los tres documentos se entregan en el directorio de trabajo, por lo que no existe aún un SHA de commit que los incluya; verificar estado y contenido al recibirlos.

## Evidencia de preparación

- Preflight del Harness: PASS el 2026-09-08; rama main y árbol limpio antes de crear estos documentos.
- Lectura de instrucciones, perfil y registro del incidente de GPU.
- Revisión de evidencia local realizada en la conversación y fuentes oficiales de analítica consultadas para el plan.
- Validación documental de cierre: PASS en lectura UTF-8 sin caracteres de reemplazo, 24 paquetes únicos y ordenados, enlaces locales existentes y dominio VPS en los tres documentos. Estado Git: exclusivamente los tres documentos nuevos sin seguimiento; sin modificaciones a archivos existentes. `git diff --check` sin errores para archivos seguidos; los nuevos se comprobaron por lectura directa.
- Subagente de revisión VPS: revisión completada e incorporada; detectó flujo Pages configurado y exigió convivencia de servicios, pestaña integrada, límites de ingestión, restauración y ausencia de dependencia del PC.
- No se ejecutaron pruebas del RAG, build del sitio ni descarga masiva: no hubo implementación.

## Decisiones abiertas que no deben inventarse

Capacidad de la VPS actual y presupuesto incremental; inferencia en VPS o API externa; modelo de embeddings/generación; elección final de analítica y retención; selección visual. El alojamiento web en la VPS actual y la pestaña RAG ya están decididos. Avanzar con preparación y prototipos independientes mientras las decisiones restantes se resuelven. No tratar silencio como aprobación de gasto o publicación.

## Formato de checkpoint de cada paquete

```yaml
task_id: P090-20260908-plan-publico-NN
estado: pendiente
responsable: por_asignar
integration_owner: Eduardo Vega
base_revision: por_verificar
revision_candidata: sin_commit
rama_worktree: por_verificar
superficie: []
cambios: []
archivos: []
pruebas_ejecutadas: []
resultados: []
presupuesto_y_consumo: pendiente
riesgos: []
pendientes: []
rollback: por_definir_segun_cambios
siguiente_accion: iniciar_verificacion_local
```

Un bloqueo incluye causa, evidencia, trabajo independiente posible y decisión necesaria. No marcar completo por agotamiento de contexto. Antes de cambiar de agente, guardar checkpoint, liberar solo la custodia propia y hacer que el receptor verifique revisión y adquiera la suya.

## Rollback de esta entrega

La entrega solo añade tres documentos. Para deshacerla, retirar o archivar exclusivamente esos archivos tras comprobar que no tienen cambios posteriores ajenos y contar con autorización para borrado. No revertir el repositorio entero. Para implementaciones futuras, definir rollback específico por paquete y probar recuperación de datos antes de migraciones destructivas.
