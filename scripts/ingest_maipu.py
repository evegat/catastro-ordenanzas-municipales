import json
from collections import Counter

# Load status_data.js
with open('dashboard/status_data.js', 'r', encoding='utf-8') as f:
    text = f.read()

prefix = 'window.CATASTRO_DATA = '
suffix = ';\n'
json_text = text[len(prefix):].rstrip(';\n ')
data = json.loads(json_text)

# Load verified new ordinances
with open('scripts/maipu_verified_ordinances.json', 'r', encoding='utf-8') as fv:
    verified_ords = json.load(fv)

# Topic mapping
topic_mapping = {
    "MAIPU-ORD-2026-4193": ("mascotas_animales", "Tenencia Responsable y Mascotas"),
    "MAIPU-ORD-2026-2194": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2026-0272": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2026-0107": ("aseo_medioambiente", "Aseo, Ornato y Medio Ambiente"),
    "MAIPU-ORD-2025-5566": ("derechos_tarifas", "Derechos Municipales y Tarifas"),
    "MAIPU-ORD-2025-5534": ("aseo_medioambiente", "Aseo, Ornato y Medio Ambiente"),
    "MAIPU-ORD-2025-2586": ("administracion_interna", "Organización y Régimen Interno"),
    "MAIPU-ORD-2024-7251": ("derechos_tarifas", "Derechos Municipales y Tarifas"),
    "MAIPU-ORD-2024-6558": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2023-6013": ("derechos_tarifas", "Derechos Municipales y Tarifas"),
    "MAIPU-ORD-2023-3046": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2023-2464": ("seguridad_convivencia", "Seguridad y Convivencia"),
    "MAIPU-ORD-2023-1996": ("comercio_alcoholes", "Comercio, Alcoholes y Patentes"),
    "MAIPU-ORD-2023-1404": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2023-0314": ("seguridad_convivencia", "Seguridad y Convivencia"),
    "MAIPU-ORD-2023-0163": ("aseo_medioambiente", "Aseo, Ornato y Medio Ambiente"),
    "MAIPU-ORD-2022-7590": ("administracion_interna", "Organización y Régimen Interno"),
    "MAIPU-ORD-2022-3833": ("comercio_alcoholes", "Comercio, Alcoholes y Patentes"),
    "MAIPU-ORD-2021-2751": ("derechos_tarifas", "Derechos Municipales y Tarifas"),
    "MAIPU-ORD-2020-MASC": ("social_salud_deporte", "Salud, Deporte y Desarrollo Social"),
    "MAIPU-ORD-2019-2659": ("aseo_medioambiente", "Aseo, Ornato y Medio Ambiente")
}

formatted_new_ords = []
for vo in verified_ords:
    ord_id = vo["id"]
    mat_id, mat_nombre = topic_mapping[ord_id]
    
    formatted_new_ords.append({
        "cplt_code": "MU_maipu",
        "fuente": "Municipalidad",
        "numero": vo["numero"].replace("Decreto Alcaldicio N° ", "").replace("Decreto Alcaldicio Nº ", ""),
        "fecha": vo["fecha"],
        "titulo": vo["titulo"],
        "materia": mat_nombre,
        "materia_id": mat_id,
        "source_listing_url": vo["target_url"],
        "target_url": vo["target_url"],
        "verification": {
            "status": "verified",
            "http_status": 200,
            "resolved_url": vo["target_url"],
            "content_type": "application/pdf",
            "sha256": vo["verification"]["sha256"],
            "bytes": vo["verification"]["bytes"],
            "verified_at": "2026-09-25T08:00:00.000000+00:00"
        },
        "rdf_url": None
    })

# Find Maipu and update
maipu = next(c for c in data['comunas'] if c['comuna'] == 'Maipú')
print(f"Maipú before: total={maipu['total_count']}, bcn={maipu['bcn_count']}, muni={maipu['municipal_count']}, ords={len(maipu['ordenanzas'])}")

# Add new ords
maipu['ordenanzas'].extend(formatted_new_ords)

# Sort descending by fecha
maipu['ordenanzas'].sort(key=lambda x: x.get('fecha', ''), reverse=True)

# Update counts
maipu['municipal_count'] = len([o for o in maipu['ordenanzas'] if o.get('fuente') == 'Municipalidad'])
maipu['bcn_count'] = len([o for o in maipu['ordenanzas'] if o.get('fuente') == 'BCN'])
maipu['total_count'] = len(maipu['ordenanzas'])
maipu['last_update'] = maipu['ordenanzas'][0]['fecha']

print(f"Maipú after: total={maipu['total_count']}, bcn={maipu['bcn_count']}, muni={maipu['municipal_count']}, latest={maipu['last_update']}")

# Update global verified_municipal_records
if 'public_scope' in data:
    data['public_scope']['verified_municipal_records'] = sum(
        len([o for o in c.get('ordenanzas', []) if o.get('fuente') == 'Municipalidad'])
        for c in data['comunas']
    )
    print("New verified_municipal_records:", data['public_scope']['verified_municipal_records'])

# Recalculate topics counts
topic_counts = Counter()
for c in data['comunas']:
    for o in c.get('ordenanzas', []):
        mid = o.get('materia_id', 'general')
        topic_counts[mid] += 1

for t in data.get('topics', []):
    tid = t['id']
    t['count'] = topic_counts[tid]
    print(f"Topic {tid}: {t['count']}")

# Write back
new_json = json.dumps(data, indent=2, ensure_ascii=False)
with open('dashboard/status_data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + new_json + ';\n')

print("status_data.js successfully updated!")
