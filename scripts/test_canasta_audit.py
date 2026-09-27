import json
import re
import unicodedata
from collections import defaultdict, Counter

def norm(text):
    if not text:
        return ''
    t = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    return t.lower()

PATTERNS = {
    '1_derechos': {
        'name': 'Derechos Municipales y Tarifas',
        'legal_base': 'DL 3.063 / Rentas Municipales (arts. 41-42)',
        'regex': re.compile(r'\b(derecho|derechos|tarifa|tarifas|arancel|aranceles|rentas?\s*municipales|concesiones,?\s*permisos\s*y\s*servicios|cobro\s*de\s*derechos|derechos\s*municipales|derecho\s*de\s*aseo|exencion\s*de\s*derechos|pagos?\s*de\s*derechos)\b'),
        'mats': {'derechos_tarifas', 'derechos_municipales'}
    },
    '2_aseo_ambiente': {
        'name': 'Aseo, Gestión de Residuos y Protección Ambiental',
        'legal_base': 'Ley 18.695 (art. 3f) / Ley 20.920 REP',
        'regex': re.compile(r'\b(aseo|ornato|residuos?|basuras?|medio\s*ambiente|ambiental|vertederos?|escombros?|reciclaje|recoleccion|desechos?|limpieza|microbasurales?|areas?\s*verdes?|arbolado|humedales?|bolsas?\s*plasticas?|sustentabilidad|sustentable)\b'),
        'mats': {'aseo_medioambiente', 'aseo_residuos', 'medio_ambiente'}
    },
    '3_seguridad_ruidos': {
        'name': 'Seguridad, Convivencia y Ruidos Molestos',
        'legal_base': 'DS 38 MMA / Ley 18.695 (arts. 4h y 4j)',
        'regex': re.compile(r'\b(ruidos?|sonidos?\s*molestos?|contaminacion\s*acustica|acustica|fuentes\s*sonoras|seguridad|convivencia|tranquilidad|orden\s*publico|incivilidades?|acoso\s*callejero|cierre\s*de\s*calles?|cierre\s*de\s*pasajes?|camaras|televigilancia|rayados?|graffitis?|vigilancia|guardias|seguridad\s*ciudadana|seguridad\s*publica)\b'),
        'mats': {'seguridad_convivencia', 'convivencia_seguridad', 'convivencia_ruidos'}
    },
    '4_mascotas': {
        'name': 'Tenencia Responsable de Mascotas y Animales de Compañía',
        'legal_base': 'Ley 21.020 (Ley Cholito, art. 7)',
        'regex': re.compile(r'\b(mascotas?|animales?\s*de\s*compania|tenencia\s*responsable|canino|canina|perros?|felinos?|gatos?|zoosanitari[ao]|bienestar\s*animal|proteccion\s*animal|veterinari[ao]|ley\s*cholito|control\s*canino|mordeduras?)\b'),
        'mats': {'mascotas_animales', 'tenencia_mascotas', 'mascotas', 'tenencia_responsable_mascotas'}
    },
    '5_participacion': {
        'name': 'Participación Ciudadana',
        'legal_base': 'Ley 20.500 / Ley 18.695 (art. 93)',
        'regex': re.compile(r'\b(participacion\s*ciudadana|participacion\s*(?:de\s*la\s*)?comunidad|participacion\s*vecinal|cosoc\b|consejo\s*comunal\s*de\s*la\s*sociedad\s*civil|consejo\s*economico\s*y\s*social|cesco\b|plebiscitos?|consultas?\s*ciudadanas?|audiencias?\s*publicas?|cabildos?\s*(?:comunales?|ciudadanos?)|presupuestos?\s*participativos?|organizaciones\s*comunitarias)\b'),
        'mats': {'participacion_ciudadana'}
    }
}

def classify_ord(ord_item):
    t = norm(ord_item.get('titulo', ''))
    m = norm(ord_item.get('materia', ''))
    mid = ord_item.get('materia_id', '')
    
    matches = set()
    for cat_key, cat_data in PATTERNS.items():
        if cat_data['regex'].search(t):
            matches.add(cat_key)
        elif mid in cat_data['mats']:
            # Exception filter for false positive materia_id
            if cat_key == '3_seguridad_ruidos' and ('denominacion de poblaciones' in t or 'cambio de nombre' in t):
                pass
            else:
                matches.add(cat_key)
        elif cat_data['regex'].search(m):
            matches.add(cat_key)
    return matches

def main():
    with open('dashboard/status_data.json', encoding='utf-8') as f:
        data = json.load(f)
        
    comunas = data['comunas']
    print(f"Total comunas: {len(comunas)}")
    
    for k, v in PATTERNS.items():
        matched_ords = 0
        matched_comunas = set()
        matched_recent_comunas = set()
        for c in comunas:
            c_has = False
            c_has_recent = False
            for o in c.get('ordenanzas', []):
                t = norm(o.get('titulo', ''))
                m = norm(o.get('materia', ''))
                mid = o.get('materia_id', '')
                
                is_match = False
                if v['regex'].search(t):
                    is_match = True
                elif mid in v['mats']:
                    if k == '3_seguridad_ruidos' and ('denominacion de poblaciones' in t or 'cambio de nombre' in t):
                        pass
                    else:
                        is_match = True
                elif v['regex'].search(m):
                    is_match = True
                    
                if is_match:
                    matched_ords += 1
                    c_has = True
                    f = str(o.get('fecha') or '')
                    if len(f) >= 4 and f[:4].isdigit() and 2021 <= int(f[:4]) <= 2026:
                        c_has_recent = True
            if c_has:
                matched_comunas.add(c['comuna'])
            if c_has_recent:
                matched_recent_comunas.add(c['comuna'])
        print(f"--- {v['name']} ({v['legal_base']}) ---")
        print(f"  Ordenanzas detectadas: {matched_ords}")
        print(f"  Comunas con la materia (histórico 346): {len(matched_comunas)} ({len(matched_comunas)/346*100:.1f}%)")
        print(f"  Comunas con la materia vigente 2021-2026: {len(matched_recent_comunas)} ({len(matched_recent_comunas)/204*100:.1f}% de 204 recientes, {len(matched_recent_comunas)/346*100:.1f}% nacional)\n")

if __name__ == '__main__':
    main()
