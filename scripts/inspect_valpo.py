import json

with open('scripts/valpo_details.json', 'r', encoding='utf-8') as f:
    valpo = json.load(f)

for comuna, data in valpo.items():
    items = data.get('items', [])
    print(f"\n=== {comuna} ({len(items)} items) ===")
    for it in items:
        date = it.get('date', '')[:10]
        title = it.get('title', {}).get('rendered', '')
        url = it.get('source_url', '')
        mime = it.get('mime_type', '')
        if 'pdf' in mime or url.endswith('.pdf'):
            print(f"  {date} | {title} | {url}")
