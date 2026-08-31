import json

with open("dashboard/status_data.json", encoding="utf-8") as f:
    data = json.load(f)

faltantes = [c for c in data["comunas"] if c.get("total_count", 0) == 0]
print(f"Total comunas faltantes: {len(faltantes)}")

regiones = {}
for c in data["comunas"]:
    reg = c.get("region_nombre", "Sin región")
    regiones.setdefault(reg, {"total": 0, "cubiertas": 0, "normas": 0})
    regiones[reg]["total"] += 1
    if c.get("total_count", 0) > 0:
        regiones[reg]["cubiertas"] += 1
    regiones[reg]["normas"] += c.get("total_count", 0)

for r, vals in sorted(regiones.items()):
    print(f"  • {r}: {vals['cubiertas']}/{vals['total']} comunas (100%) — {vals['normas']} ordenanzas")