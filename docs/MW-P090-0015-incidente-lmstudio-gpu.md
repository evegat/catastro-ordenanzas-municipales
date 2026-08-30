# MW-P090-0015 — Incidente LM Studio, GPU y reinicios inesperados

Fecha: 2026-08-30  
Estado: contenido y automatización pausados  
Alcance: diagnóstico local; sin cambios en datos, checkpoints, código, publicación ni credenciales

## Resumen

La automatización de seguimiento `vigilar-crawler-p090`, programada cada 15 minutos, detectó que LM Studio no respondía y lo inició de forma oculta junto con su servidor local, el watchdog de P090 y el clasificador `qwen/qwen3.5-9b`. La carga sostenida llevó la RTX 4080 Laptop a 90–100 % de utilización, aproximadamente 8,6 GB de VRAM y 87–89 °C. Durante ese periodo el equipo presentó lentitud progresiva del puntero y teclado y dos reinicios inesperados.

Windows registró eventos `Kernel-Power 41` y `EventLog 6008`, sin pantalla azul, minidump, error WHEA, alerta térmica registrada ni fallo NVMe. La ejecución de P090 y los reinicios tienen una correlación temporal fuerte, pero los registros no permiten atribuir con certeza el corte final a protección térmica, energía, controlador gráfico o congelamiento del sistema.

## Causa operacional confirmada

- LM Studio se ejecutó con `--run-as-service`, sin ventana visible.
- `lms server start` abrió la API local en `127.0.0.1:1234`.
- La carga JIT inició `qwen/qwen3.5-9b` al recibir solicitudes del clasificador de P090.
- Detener solo `llama-server.exe` no bastó: el servicio residente volvió a cargar el modelo.
- La automatización había sido creada en la tarea Codex `Automatiza revisión de ordenanzas` para mantener el crawler local operando sin intervención.
- La automatización no incorporaba límites térmicos, presupuesto de potencia, ventana máxima de ejecución ni cortacircuito contra relanzamientos.

## Contención aplicada

- Automatización `vigilar-crawler-p090`: `PAUSED`.
- Procesos exactos de LM Studio, `llama-server`, watchdog, runner SINIM y clasificador P090: detenidos.
- Puerto local `1234`: sin listener al verificar.
- Estado posterior de la RTX 4080: 0 % de uso, estado de reposo y descenso progresivo desde 89 °C hasta aproximadamente 53 °C.
- Datos, resultados parciales, logs y checkpoints del crawler: conservados.

## Condiciones para reanudar

No reactivar la automatización vigente sin una revisión específica. Una versión segura debe incluir, como mínimo:

1. modelo y cuantización ajustados a la capacidad térmica del notebook;
2. contexto, batch y concurrencia acotados;
3. límite térmico de detención y periodo obligatorio de enfriamiento;
4. tiempo máximo por ejecución;
5. máximo de reintentos y prohibición de relanzamiento indefinido;
6. checkpoint antes de detener el proceso;
7. monitor de GPU, VRAM, temperatura y respuesta del sistema;
8. autorización explícita antes de volver a habilitar ejecución headless persistente.

Como prueba inicial, usar un modelo de 3B–7B en Q4, contexto de 4.096–8.192 tokens, una solicitud concurrente y una ventana controlada de 10–15 minutos. Si el equipo vuelve a reiniciarse sin LM Studio activo, abrir una investigación separada de controladores, refrigeración y alimentación eléctrica.

## Rollback

La contención es reversible: reactivar la automatización y volver a iniciar los runners. No hacerlo hasta implementar y validar los controles anteriores.
