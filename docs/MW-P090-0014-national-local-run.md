# MW-P090-0014 — Ejecución nacional local

La recolección usa dos rutas complementarias y sin APIs pagadas:

1. el crawler LM Studio recorre el universo oficial CPLT de 345 municipalidades, prueba sitios municipales y Transparencia Activa y deja candidatos en cuarentena;
2. `run_sinim_discovery.ps1` obtiene desde SINIM/SUBDERE las webs institucionales, verifica identidad, descubre fuentes y construye semillas reproducibles.

SINIM se ejecuta en diez shards reanudables. Cada shard válido queda conservado; una falla se reintenta una vez y luego detiene esa vía sin borrar progreso. El merge exige 345 códigos CPLT únicos. A continuación, las fuentes validadas se extraen en otros diez shards reanudables y se consolidan en cuarentena. Ninguna ruta declara cobertura completa ni publica resultados.

Evidencia operativa:

- `logs/continuous_crawler.log`
- `logs/local_crawler_watchdog.log`
- `logs/sinim_discovery_runner.log`
- `data/crawler_state.json`
- `data/sinim_seed_enrichment.json`
- `data/sinim_validated_extraction_seeds.json`
