import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/comunas_en_las_mismas_condiciones.json', encoding='utf-8') as f:
    comunas = json.load(f)

tipos = {}
for c in comunas:
    url = c.get('url_transparencia', '')
    if 'portaltransparencia.cl' in url:
        tipos.setdefault('CPLT Estándar (portaltransparencia.cl)', []).append(c['comuna'])
    elif url:
        tipos.setdefault('Portal Propio Municipal', []).append(f"{c['comuna']} ({url})")
    else:
        tipos.setdefault('Sin URL Transparencia registrada', []).append(c['comuna'])

for k, v in tipos.items():
    print(f"=== {k}: {len(v)} comunas ===")
    for item in v[:10]:
        print(f"  - {item}")
    if len(v) > 10:
        print(f"  ... y {len(v)-10} más.\n")
