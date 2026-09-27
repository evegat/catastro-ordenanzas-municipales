import urllib.request
import json
import ssl

ctx = ssl._create_unverified_context()
headers = {'User-Agent': 'Mozilla/5.0'}

targets = [
    ('Villa Alemana', '05', 'MU338', 'https://www.villalemana.cl/wp-json/wp/v2/media?search=ordenanza&per_page=20'),
    ('La Calera', '05', 'MU023', 'https://lacalera.cl/wp-json/wp/v2/media?search=ordenanza&per_page=20'),
    ('Quintero', '05', 'MU239', 'https://muniquintero.cl/wp-json/wp/v2/media?search=ordenanza&per_page=20')
]

results = {}
for name, reg, cplt, url in targets:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read())
            results[name] = {
                'region_id': reg,
                'cplt_code': cplt,
                'items': data
            }
            print(f"{name}: {len(data)} items retrieved")
    except Exception as e:
        print(f"Error {name}: {e}")

with open('scripts/valpo_details.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
