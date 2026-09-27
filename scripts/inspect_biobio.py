import urllib.request
import json
import ssl

ctx = ssl._create_unverified_context()
headers = {'User-Agent': 'Mozilla/5.0'}

targets = [
    ('Coronel', '08', 'MU053', 'https://coronel.cl/wp-json/wp/v2/media?search=ordenanza&per_page=20'),
    ('Arauco', '08', 'MU011', 'https://muniarauco.cl/wp-json/wp/v2/media?search=ordenanza&per_page=20')
]

for name, reg, cplt, url in targets:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read())
            print(f"\n=== {name} ({len(data)} items) ===")
            for it in data:
                date = it.get('date', '')[:10]
                title = it.get('title', {}).get('rendered', '')
                src = it.get('source_url', '')
                mime = it.get('mime_type', '')
                if 'pdf' in mime or src.endswith('.pdf'):
                    print(f"  {date} | {title} | {src}")
    except Exception as e:
        print(f"Error {name}: {e}")
