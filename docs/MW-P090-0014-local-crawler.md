# MW-P090-0014 — Crawler local reanudable con LM Studio

El crawler usa la API OpenAI-compatible de LM Studio para clasificar enlaces encontrados en portales cuya identidad municipal fue verificada. Es sólo discovery: escribe candidatos en `data/local_crawler_candidates.json` y no modifica el corpus verificado, el dashboard ni la cobertura.

Estados: `done` (pasada terminada), `review` (requiere revisión) y `retry` (falla transitoria). Todos conservan `coverage_complete: false`. Una falla se reintenta hasta tres veces; luego pasa a revisión para no bloquear indefinidamente el resto de la cola.

## Uso

Validación local sin consultar municipios:

`python src/continuous_commune_crawler.py --model qwen/qwen3.5-9b --dry-run`

Prueba acotada:

`python src/continuous_commune_crawler.py --model qwen/qwen3.5-9b --max 1 --retry-failed`

Ejecución continua en primer plano:

`powershell -ExecutionPolicy Bypass -File scripts/run_local_crawler.ps1 -Model qwen/qwen3.5-9b -BatchSize 10`

Revisar `data/local_crawler_candidates.json`, `data/crawler_state.json` y `logs/continuous_crawler.log`. El launcher se detiene si LM Studio o el modelo no están disponibles. No instala servicios ni crea tareas programadas.

Los candidatos `review_status: pending` no son publicables. Antes de promoverlos se deben descargar y validar como PDF, registrar URL oficial de listado, estado HTTP, URL resuelta, MIME, bytes, SHA-256 y fecha, y pasar por el flujo canónico de promoción y build.
