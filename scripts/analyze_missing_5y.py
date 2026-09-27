import json

content = open('dashboard/status_data.js', encoding='utf-8').read()
prefix = 'window.CATASTRO_DATA = '
data = json.loads(content[len(prefix):].rstrip(';\n'))
comunas = data.get('comunas', [])

missing_5y = []
for c in comunas:
    ords = c.get('ordenanzas', [])
    years = [int(str(o.get('fecha', ''))[:4]) for o in ords if str(o.get('fecha', ''))[:4].isdigit()]
    max_y = max(years) if years else 0
    if max_y < 2021:
        missing_5y.append({
            'comuna': c.get('comuna'),
            'region_id': c.get('region_id'),
            'region': c.get('region_nombre'),
            'last_year': max_y,
            'total_ords': len(ords)
        })

print(f"Total comunas sin ordenanza en 2021-2026: {len(missing_5y)}")

# Group by region
by_reg = {}
for m in missing_5y:
    reg = m['region'] or 'Sin Región'
    by_reg.setdefault(reg, []).append(m)

for reg, coms in sorted(by_reg.items(), key=lambda x: len(x[1]), reverse=True):
    sample = ", ".join([f"{c['comuna']} ({c['last_year']})" for c in coms[:6]])
    print(f"{reg} ({len(coms)} comunas): {sample}")

# Guardar lista estructurada para uso de subagentes
with open('scripts/missing_5y_communes.json', 'w', encoding='utf-8') as f:
    json.dump(missing_5y, f, indent=2, ensure_ascii=False)
