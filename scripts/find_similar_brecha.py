import json
import csv
import sys

# Configurar salida utf-8
sys.stdout.reconfigure(encoding='utf-8')

content = open('dashboard/status_data.js', encoding='utf-8').read()
prefix = 'window.CATASTRO_DATA = '
data = json.loads(content[len(prefix):].rstrip(';\n'))
comunas = data.get('comunas', [])

maestro = {}
try:
    with open('data/maestro_comunas_chile.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            maestro[r.get('comuna_nombre', '').strip().lower()] = r
except Exception as e:
    pass

en_las_mismas = []

for c in comunas:
    name = c.get('comuna', '')
    reg = c.get('region_nombre', '')
    ords = c.get('ordenanzas', [])
    
    bcn_ords = [o for o in ords if o.get('fuente') == 'BCN']
    muni_ords = [o for o in ords if o.get('fuente') == 'Municipalidad']
    
    years = [int(str(o.get('fecha', ''))[:4]) for o in ords if str(o.get('fecha', ''))[:4].isdigit()]
    max_year = max(years) if years else 0
    recent_5y = [y for y in years if y >= 2021]
    
    # Patrón "en las mismas":
    # Fuerte presencia histórica BCN (>=15), pero casi nula municipal (<=5) y rezago reciente (<=3)
    if len(bcn_ords) >= 15 and len(muni_ords) <= 5 and len(recent_5y) <= 3:
        m_info = maestro.get(name.lower(), {})
        en_las_mismas.append({
            'comuna': name,
            'region': reg,
            'total_ords': len(ords),
            'bcn_ords': len(bcn_ords),
            'muni_ords': len(muni_ords),
            'recent_5y': len(recent_5y),
            'max_year': max_year,
            'web_municipal': m_info.get('web_municipal', ''),
            'url_transparencia': m_info.get('url_transparencia', '')
        })

print(f"Total comunas detectadas en la misma condición de brecha: {len(en_las_mismas)}\n")
en_las_mismas.sort(key=lambda x: x['bcn_ords'], reverse=True)

with open('data/comunas_en_las_mismas_condiciones.json', 'w', encoding='utf-8') as f:
    json.dump(en_las_mismas, f, indent=2, ensure_ascii=False)

# Mostrar tabla formateada
print(f"{'#':<3} | {'Comuna':<18} | {'Región':<24} | {'Total':<6} | {'BCN':<5} | {'Muni':<5} | {'2021-2026':<10} | {'Último Año'}")
print("-" * 85)
for idx, x in enumerate(en_las_mismas, 1):
    c_nom = x['comuna'][:18]
    r_nom = (x['region'] or '')[:24]
    print(f"{idx:<3} | {c_nom:<18} | {r_nom:<24} | {x['total_ords']:<6} | {x['bcn_ords']:<5} | {x['muni_ords']:<5} | {x['recent_5y']:<10} | {x['max_year']}")
