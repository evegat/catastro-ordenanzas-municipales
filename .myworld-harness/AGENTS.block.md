## Harness MyWorld v1

<!-- Este contenido está administrado por MyWorld. Las reglas locales adicionales se conservan. -->

- Antes de escribir, lee `MYWORLD-HARNESS.json` y ejecuta `.myworld-harness/harness.ps1 preflight`.
- Toda tarea no trivial debe tener un `task_id` estable. En repositorios GitHub, el Issue es el ticket canónico y debe conservar ese `task_id`.
- Un agente trabaja en una tarea, rama o worktree y superficie de escritura declarada; el lock representa custodia temporal, no propiedad permanente.
- No mezcles, reviertas ni elimines cambios ajenos.
- Si cambia el agente responsable, genera un handoff estructurado con el mismo `task_id`, revisión exacta, cambios, archivos, pruebas, riesgos, pendientes, rollback e `integration_owner`; libera el lock y el receptor adquiere uno nuevo tras verificar la revisión.
- Ejecuta los gates aplicables y entrega evidencia verificable; no declares pruebas no ejecutadas.
- Tests/verify comprueban comportamiento; RDD autoriza el candidato exacto revisado antes de commit/push/PR/deploy cuando corresponda.
- No imprimas ni almacenes secretos, tokens, cookies o datos personales innecesarios.
- Enviar, publicar, desplegar, borrar, pagar o modificar credenciales/permisos requiere autorización vigente, explícita y específica.
- Todo impedimento se registra como pendiente estructurado y no detiene trabajo independiente.
- Antes de integrar, entrega `task_id`, base revision, cambios, archivos, pruebas, riesgos, pendientes y rollback.
