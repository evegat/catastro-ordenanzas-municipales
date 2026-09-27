import json
import re

import sys
sys.stdout.reconfigure(encoding='utf-8')

def inspect_transcript(path, label, keywords):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"\n=== {label} (total steps: {len(lines)}) ===")
    found = set()
    for l in lines:
        matches = re.findall(r'https?://[^\s"\'<>]+\.pdf', l)
        for m in matches:
            if any(k in m.lower() for k in keywords):
                found.add(m)
    print(f"Found {len(found)} candidate PDF URLs:")
    for u in sorted(found):
        print("  ", u)

rm_kw = ['conchali', 'bosque', 'huechuraba', 'cisterna', 'espejo', 'loprado', 'pedroaguirre', 'quintanormal', 'pirque', 'lampa', 'calera', 'elmonte', 'islademaipo', 'padrehurtado', 'mph', 'bcn.cl', 'diariooficial']
inspect_transcript(r'C:\Users\evega\.gemini\antigravity\brain\5ee30e8a-212e-4329-887e-89cd268d4e38\.system_generated\logs\transcript.jsonl', 'Subagent 1 (RM)', rm_kw)

reg_kw = ['rancagua', 'talca', 'coquimbo', 'copiapo', 'coyhaique', 'osorno', 'talcahuano', 'coronel', 'chiguayante', 'sanpedro', 'bcn.cl', 'diariooficial']
inspect_transcript(r'C:\Users\evega\.gemini\antigravity\brain\aca51e39-e3db-4739-8af0-e40c974c497b\.system_generated\logs\transcript.jsonl', 'Subagent 2 (Capitales)', reg_kw)
