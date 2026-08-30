# MW-P090-0014 — Watchdog local del crawler

`scripts/watch_local_crawler.ps1` vigila los runners nacionales de este proyecto. Comprueba cada 60 segundos que LM Studio exponga el modelo configurado, que exista una sola instancia del crawler exacto y que `data/crawler_state.json` o `logs/continuous_crawler.log` mantengan actividad. Mientras no exista el ledger final de semillas SINIM, también mantiene activo su runner reanudable.

Si el runner no existe, lo inicia. Si permanece sin actividad por 12 minutos, detiene sólo el PID cuya línea de comando contiene la ruta absoluta exacta de `scripts/run_local_crawler.ps1` e intenta iniciarlo de nuevo. Nunca modifica ni promueve candidatos, corpus o dashboard. Si LM Studio deja de responder, el watchdog termina con código 2 y no toca procesos. Ante runners duplicados termina con código 4.

## Inicio en primer plano

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/watch_local_crawler.ps1
```

## Observación

```powershell
Get-Content logs/local_crawler_watchdog.log -Wait -Tail 30
```

El mutex `Local\MW-P090-0014-local-crawler-watchdog` impide dos watchdogs simultáneos. Si queda un proceso Python exacto del crawler sin runner, no inicia otra copia y registra el bloqueo para evitar procesamiento duplicado. El watchdog no instala servicios ni tareas programadas.

Rollback: detener el proceso PowerShell correspondiente a `watch_local_crawler.ps1`; no hay configuración persistente que retirar.
