# MW-P090-0009 — Barrido nacional de fuentes municipales

## Política

- **NO SAMPLING**.
- Discovery no implica cobertura completa.
- La ausencia de un hallazgo no implica ausencia de ordenanzas.
- El directorio oficial CPLT define el universo institucional.
- `data/maestro_comunas_chile.csv:web_municipal` se usa solo como semilla y debe superar verificación de identidad municipal antes de aceptar enlaces.

## Evidencia canónica de discovery

- Workflow: `National Municipal Discovery`
- Run: `33259256827`
- Head: `f1603ed2651608bcd592bb66ea15b503f084cde1`
- Artifact agregado: `9716779792`
- SHA-256 artifact: `4ada6f6ff0ba295b45d207adef8d2a1cec4e859964f5b602fa66c062a5a9cbe9`
- MyWorld Harness: run `33259256823`, PASS.

## Resultado nacional

- 345 municipalidades / 346 comunas en el ledger.
- 15 municipalidades con fuentes candidatas descubiertas en sitios cuya identidad institucional fue verificada.
- 14 sitios municipales verificados sin candidato en la pasada genérica.
- 6 semillas alcanzables rechazadas por identidad insuficiente.
- 289 organismos con candidato de Portal CPLT no verificable desde el runner por bloqueo de acceso; no se interpreta como ausencia documental.
- 16 sin fuente resuelta en esta fase.
- 5 con fuentes parciales ya registradas por recovery anterior.
- 64 fuentes candidatas detectadas: 33 custom/static, 23 Joomla, 7 WordPress y 1 no clasificada.

## Municipios con candidatos propios validados en esta pasada

- Alhué (MU002)
- Antofagasta (MU009)
- Calama (MU019)
- Calbuco (MU020)
- Casablanca (MU030)
- Castro (MU031)
- Cobquecura (MU048)
- Colbún (MU055)
- Curacaví (MU073)
- Maipú (MU163)
- Panguipulli (MU200)
- Pica (MU217)
- Ránquil (MU261)
- Taltal (MU314)
- Tucapel (MU329)

## Siguiente contrato

La siguiente fase debe convertir las fuentes candidatas en adaptadores exhaustivos por familia, descargar/verificar documentos, tipificar el acto jurídico y deduplicar contra BCN/LeyChile antes de promover registros al corpus público.