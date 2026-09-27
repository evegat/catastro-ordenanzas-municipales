import json
import os

subs = [
    ('b42f4835-0ce7-4129-b438-82eaa5765e6b', 'Centro'),
    ('5876b6c9-fd6a-4a27-90a8-ea18988e8ac6', 'NorteSur')
]

for cid, name in subs:
    p = rf"C:\Users\evega\.gemini\antigravity\brain\{cid}\.system_generated\logs\transcript.jsonl"
    if not os.path.exists(p):
        continue
    lines = [json.loads(l) for l in open(p, encoding='utf-8')]
    print(f"=== Subagent {name} ({len(lines)} steps) ===")
    
    # Check scratch files
    scratch_dir = rf"C:\Users\evega\.gemini\antigravity\brain\{cid}\scratch"
    if os.path.exists(scratch_dir):
        files = os.listdir(scratch_dir)
        print(f"  Scratch files: {files}")
        for f in files:
            if f.endswith('.json') or f.endswith('.txt'):
                fp = os.path.join(scratch_dir, f)
                try:
                    content = open(fp, encoding='utf-8', errors='ignore').read()
                    print(f"    {f} ({len(content)}b): {content[:150]}...")
                except Exception as e:
                    print(f"    {f} error: {e}")

    for l in lines[-5:]:
        tc = l.get('tool_calls', [])
        for c in tc:
            args = c.get('args', {})
            cmd = args.get('CommandLine', '') or args.get('query', '')
            print(f"  Tool {c.get('name')}: {cmd[:100]}")
