import sys

sys.stdout.reconfigure(encoding='utf-8')
with open('dashboard/index.html', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'tab-btn' in l or 'id="tab-' in l or 'renderMatriz' in l:
        print(f"{i+1}: {l.strip()[:110]}")
