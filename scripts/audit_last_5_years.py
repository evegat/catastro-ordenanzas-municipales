import json

with open('dashboard/status_data.js', 'r', encoding='utf-8') as f:
    text = f.read()
data = json.loads(text[len('window.CATASTRO_DATA = '):].rstrip(';\n '))

missing_recent = []
has_recent = 0

for c in data['comunas']:
    latest = c.get('last_update')
    # if last_update is not set or < 2021
    if not latest or latest < '2021-01-01':
        missing_recent.append({
            'comuna': c['comuna'],
            'region_id': c['region_id'],
            'region_nombre': c['region_nombre'],
            'total_count': c['total_count'],
            'latest': latest or 'SIN_FECHA'
        })
    else:
        has_recent += 1

print(f"Total comunas analizadas: {len(data['comunas'])}")
print(f"Comunas CON ordenanzas en los últimos 5 años (>= 2021): {has_recent} ({(has_recent/346)*100:.1f}%)")
print(f"Comunas SIN ordenanzas en los últimos 5 años (< 2021): {len(missing_recent)} ({(len(missing_recent)/346)*100:.1f}%)")

# Group by region
by_region = {}
for m in missing_recent:
    reg = m['region_nombre']
    by_region.setdefault(reg, []).append(m)

for reg, list_c in sorted(by_region.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n--- {reg} ({len(list_c)} comunas) ---")
    for c in sorted(list_c, key=lambda x: x['latest'], reverse=True)[:6]:
        print(f"  {c['comuna']}: último registro={c['latest']} (total {c['total_count']})")
    if len(list_c) > 6:
        print(f"  ... y {len(list_c) - 6} más")

# Save missing list to json for batch extraction
with open('scripts/missing_5_years.json', 'w', encoding='utf-8') as f:
    json.dump(missing_recent, f, indent=2, ensure_ascii=False)
