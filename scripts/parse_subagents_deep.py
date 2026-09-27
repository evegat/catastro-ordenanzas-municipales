import json
import re

for cid, label in [('b42f4835-0ce7-4129-b438-82eaa5765e6b', 'Centro'), ('5876b6c9-fd6a-4a27-90a8-ea18988e8ac6', 'NorteSur')]:
    path = rf"C:\Users\evega\.gemini\antigravity\brain\{cid}\.system_generated\logs\transcript_full.jsonl"
    lines = [json.loads(l) for l in open(path, encoding='utf-8')]
    print(f"\n=================== SUBAGENT {label} ===================")
    
    found_urls = set()
    for idx, l in enumerate(lines):
        text = str(l.get('content', ''))
        # find pdf urls
        for u in re.findall(r'https?://[^\s"\'<>]+(?:\.pdf|[0-9a-zA-Z_/%\.-]+\.pdf)', text):
            if u not in found_urls and not u.endswith('live_dashboard_screenshot.png'):
                found_urls.add(u)
                print(f"[{label} step {idx}] PDF: {u}")
                
        # find structured JSON if any
        if '```json' in text:
            for block in re.findall(r'```json\s*(\[[\s\S]*?\])\s*```', text):
                try:
                    data = json.loads(block)
                    print(f"[{label} step {idx}] Found JSON array with {len(data)} items!")
                    for item in data:
                        print("  ->", item.get('comuna'), "|", item.get('numero'), "|", item.get('fecha'), "|", item.get('titulo', '')[:45])
                except:
                    pass
