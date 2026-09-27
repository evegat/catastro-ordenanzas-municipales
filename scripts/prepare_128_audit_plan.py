import json
import csv
import os

# 1. Cargar las 128 comunas faltantes
missing = json.load(open('scripts/missing_5y_communes.json', encoding='utf-8'))
print(f"Total comunas faltantes: {len(missing)}")

# 2. Cargar directorio CPLT
cplt_data = json.load(open('data/cplt_municipal_directory.json', encoding='utf-8'))
cplt_munis = cplt_data.get('municipalities', [])

def normalize(name):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn').lower().strip()

cplt_by_name = {}
for m in cplt_munis:
    org = m.get('organism_name', '')
    key = m.get('municipality_key', '')
    cplt_by_name[normalize(org.replace('Municipalidad de ', '').replace('Ilustre Municipalidad de ', ''))] = m
    cplt_by_name[normalize(key)] = m

# 3. Cruzar datos
enriched = []
for m in missing:
    comuna = m['comuna']
    norm_c = normalize(comuna)
    cplt_info = cplt_by_name.get(norm_c, {})
    
    # Enlaces probables
    clean_slug = norm_c.replace(' ', '')
    probable_sites = [
        f"https://www.municipalidad{clean_slug}.cl",
        f"https://www.muni{clean_slug}.cl",
        f"https://www.{clean_slug}.cl",
        f"https://www.im{clean_slug}.cl",
        f"https://www.munide{clean_slug}.cl"
    ]
    
    item = {
        'comuna': comuna,
        'region_id': m['region_id'],
        'region': m['region'],
        'last_year_in_catastro': m['last_year'],
        'total_historic_records': m['total_ords'],
        'cplt_code': cplt_info.get('cplt_code', ''),
        'cplt_ta_link': cplt_info.get('ta_link', ''),
        'cplt_sai_link': cplt_info.get('sai_link', ''),
        'probable_sites': probable_sites
    }
    enriched.append(item)

out_file = 'scripts/enriched_128_communes.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(enriched, f, indent=2, ensure_ascii=False)

print(f"Plan enriquecido guardado en {out_file} ({len(enriched)} comunas)")
print(f"Comunas con CPLT code asociado: {sum(1 for e in enriched if e['cplt_code'])} / {len(enriched)}")
