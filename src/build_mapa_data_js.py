import json
from pathlib import Path

p = Path("dashboard/mapa_data.json")
data = json.loads(p.read_text(encoding="utf-8"))

js_content = "const MAPA_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
Path("dashboard/mapa_data.js").write_text(js_content, encoding="utf-8")
print(f"mapa_data.js generado con {len(data)} comunas.")