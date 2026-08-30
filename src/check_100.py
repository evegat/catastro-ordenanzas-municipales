import json, sys

with open("dashboard/status_data.json", encoding="utf-8") as f:
    data = json.load(f)

faltantes = [c for c in data["comunas"] if c.get("total_count", 0) == 0]
cubiertas = len(data["comunas"]) - len(faltantes)
total = len(data["comunas"])
pct = (cubiertas / total) * 100

print("=" * 60)
print(f"TOTAL COMUNAS DE CHILE: {total}")
print(f"COMUNAS CUBIERTAS: {cubiertas} / {total}")
print(f"PORCENTAJE DE COBERTURA: {pct:.1f}%")
print(f"TOTAL ORDENANZAS CONSOLIDADAS: {data['metrics']['total_ordenanzas']}")
print(f"FUENTES MUNICIPALES VERIFICADAS SHA-256: {data['metrics']['ordenanzas_municipales_verificadas']}")
print(f"FUENTES BCN / LEYCHILE: {data['metrics']['ordenanzas_bcn']}")
print("=" * 60)
if faltantes:
    print("Comunas pendientes:", [c["comuna"] for c in faltantes])
else:
    print("¡COBERTURA DEL 100% DE CHILE COMPLETADA CON ÉXITO!")