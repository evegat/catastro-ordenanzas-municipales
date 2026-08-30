import json, re

text = open("data/gemini_dump_2.txt", encoding="utf-8").read()

# Buscar bloques de código JSON
pattern = r'```json\s*(.*?)\s*```'
matches = re.findall(pattern, text, re.DOTALL)
print(f"Bloques ```json encontrados: {len(matches)}")

all_parsed = []
for idx, m in enumerate(matches):
    try:
        obj = json.loads(m)
        if isinstance(obj, list):
            all_parsed.extend(obj)
            print(f"Bloque {idx+1}: {len(obj)} registros")
        elif isinstance(obj, dict):
            all_parsed.append(obj)
            print(f"Bloque {idx+1}: 1 registro")
    except Exception as e:
        print(f"Bloque {idx+1} no es JSON estricto: {e}")

print(f"Total registros estructurados válidos: {len(all_parsed)}")
comunas_found = set(r.get("comuna") for r in all_parsed if "comuna" in r)
print(f"Comunas únicas encontradas ({len(comunas_found)}):", sorted(list(comunas_found)))