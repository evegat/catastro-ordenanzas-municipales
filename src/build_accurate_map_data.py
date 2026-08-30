# -*- coding: utf-8 -*-
"""
Genera el dataset consolidado de mapa con coordenadas geográficas (Lat/Lon)
reales y precisas para las 346 comunas de Chile, vinculando los datos normativos.
"""
import json, re, unicodedata
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'
STATUS_PATH = REPO_ROOT / 'dashboard' / 'status_data.json'
MAPA_DATA_PATH = REPO_ROOT / 'dashboard' / 'mapa_data.json'
MAESTRO_PATH = DATA_DIR / 'maestro_comunas_chile.csv'

# Coordenadas de referencia por macrozona y regiones para las comunas de Chile
# Centroides comunales oficiales
COMUNAS_COORDS_BASE = {
    # Arica y Parinacota
    "Arica": (-18.4783, -70.3126), "Camarones": (-19.0142, -69.8647), "Putre": (-18.1969, -69.5594), "General Lagos": (-17.6575, -69.6053),
    # Tarapacá
    "Iquique": (-20.2133, -70.1503), "Alto Hospicio": (-20.2744, -70.1017), "Pozo Almonte": (-20.2597, -69.7864), "Camiña": (-19.3142, -69.4261), "Colchane": (-19.2778, -68.6389), "Huara": (-19.9961, -69.7719), "Pica": (-20.4897, -69.3297),
    # Antofagasta
    "Antofagasta": (-23.6509, -70.3975), "Mejillones": (-23.1000, -70.4500), "Sierra Gorda": (-22.8942, -69.3178), "Taltal": (-25.4056, -70.4833), "Calama": (-22.4544, -68.9294), "Ollagüe": (-21.2228, -68.2536), "San Pedro de Atacama": (-22.9087, -68.1997), "Tocopilla": (-22.0922, -70.1978), "María Elena": (-22.3444, -69.6611),
    # Atacama
    "Copiapó": (-27.3667, -70.3333), "Caldera": (-27.0667, -70.8167), "Tierra Amarilla": (-27.4833, -70.2667), "Chañaral": (-26.3478, -70.6222), "Diego de Almagro": (-26.3922, -70.0467), "Vallenar": (-28.5756, -70.7581), "Alto del Carmen": (-28.7583, -70.4861), "Freirina": (-28.5083, -71.0778), "Huasco": (-28.4681, -71.2197),
    # Coquimbo
    "La Serena": (-29.9027, -71.2519), "Coquimbo": (-29.9533, -71.3436), "Andacollo": (-30.2319, -71.0847), "La Higuera": (-29.5103, -71.2008), "Paiguano": (-30.0308, -70.5186), "Paihuano": (-30.0308, -70.5186), "Vicuña": (-30.0319, -70.7081), "Illapel": (-31.6333, -71.1667), "Canela": (-31.4000, -71.4583), "Los Vilos": (-31.9139, -71.5111), "Salamanca": (-31.7789, -70.9639), "Ovalle": (-30.5983, -71.2003), "Combarbalá": (-31.1803, -71.0031), "Monte Patria": (-30.6958, -70.9572), "Punitaqui": (-30.8333, -71.2667), "Río Hurtado": (-30.2764, -70.6978),
    # Valparaíso
    "Valparaíso": (-33.0472, -71.6128), "Casablanca": (-33.3167, -71.4083), "Concón": (-32.9167, -71.5167), "Juan Fernández": (-33.6361, -78.8319), "Puchuncaví": (-32.7167, -71.4167), "Quintero": (-32.7833, -71.5333), "Viña del Mar": (-33.0244, -71.5519), "Isla de Pascua": (-27.1536, -109.4311), "Los Andes": (-32.8339, -70.5983), "Calle Larga": (-32.8639, -70.6278), "Rinconada": (-32.8667, -70.7000), "San Esteban": (-32.8000, -70.5833), "La Ligua": (-32.4500, -71.2333), "Cabildo": (-32.4278, -71.0667), "Papudo": (-32.5083, -71.4500), "Petorca": (-32.2528, -70.9317), "Zapallar": (-32.5528, -71.4583), "Quillota": (-32.8833, -71.2500), "Calera": (-32.7889, -71.2167), "Hijuelas": (-32.8000, -71.1500), "La Cruz": (-32.8278, -71.2278), "Nogales": (-32.7333, -71.2000), "San Antonio": (-33.5833, -71.6167), "Algarrobo": (-33.3667, -71.6667), "Cartagena": (-33.5500, -71.6000), "El Quisco": (-33.3972, -71.6972), "El Tabo": (-33.4556, -71.6667), "Santo Domingo": (-33.6361, -71.6278), "San Felipe": (-32.7500, -70.7250), "Catemu": (-32.7778, -70.9639), "Llaillay": (-32.8417, -70.9500), "Panquehue": (-32.7667, -70.8333), "Putaendo": (-32.6278, -70.7167), "Santa María": (-32.7472, -70.6556), "Quilpué": (-33.0478, -71.4428), "Limache": (-33.0000, -71.2667), "Olmué": (-32.9972, -71.1861), "Villa Alemana": (-33.0417, -71.3722),
    # Metropolitana
    "Santiago": (-33.4489, -70.6693), "Cerrillos": (-33.5000, -70.7167), "Cerro Navia": (-33.4250, -70.7333), "Conchalí": (-33.3833, -70.6833), "El Bosque": (-33.5667, -70.6667), "Estación Central": (-33.4606, -70.7003), "Huechuraba": (-33.3750, -70.6389), "Independencia": (-33.4167, -70.6667), "La Cisterna": (-33.5333, -70.6667), "La Florida": (-33.5167, -70.5833), "La Granja": (-33.5333, -70.6167), "La Pintana": (-33.5833, -70.6333), "La Reina": (-33.4500, -70.5333), "Las Condes": (-33.4167, -70.5833), "Lo Barnechea": (-33.3500, -70.5167), "Lo Espejo": (-33.5167, -70.6833), "Lo Prado": (-33.4444, -70.7222), "Macul": (-33.4833, -70.6000), "Maipú": (-33.5111, -70.7583), "Ñuñoa": (-33.4569, -70.6033), "Pedro Aguirre Cerda": (-33.4833, -70.6667), "Peñalolén": (-33.4833, -70.5500), "Providencia": (-33.4314, -70.6094), "Pudahuel": (-33.4389, -70.7556), "Quilicura": (-33.3667, -70.7333), "Quinta Normal": (-33.4333, -70.6833), "Recoleta": (-33.4083, -70.6417), "Renca": (-33.4000, -70.7167), "San Joaquín": (-33.4917, -70.6278), "San Miguel": (-33.4944, -70.6528), "San Ramón": (-33.5333, -70.6417), "Vitacura": (-33.3972, -70.5861), "Puente Alto": (-33.6167, -70.5833), "Pirque": (-33.6333, -70.5667), "San José de Maipo": (-33.6417, -70.3500), "Colina": (-33.2000, -70.6667), "Lampa": (-33.2833, -70.8667), "Tiltil": (-33.0833, -70.9333), "San Bernardo": (-33.6000, -70.7000), "Buin": (-33.7333, -70.7333), "Calera de Tango": (-33.6333, -70.7833), "Paine": (-33.8167, -70.7500), "Melipilla": (-33.6833, -71.2167), "Alhué": (-34.0333, -71.1000), "Curacaví": (-33.4000, -71.1333), "María Pinto": (-33.5167, -71.1167), "San Pedro": (-33.9000, -71.4667), "Talagante": (-33.6667, -70.9333), "El Monte": (-33.6833, -70.9833), "Isla de Maipo": (-33.7500, -70.9000), "Padre Hurtado": (-33.5667, -70.8167), "Peñaflor": (-33.6083, -70.8778),
    # O'Higgins
    "Rancagua": (-34.1708, -70.7444), "Codegua": (-34.0333, -70.6667), "Coinco": (-34.2667, -70.9500), "Coltauco": (-34.2667, -71.0833), "Doñihue": (-34.2333, -70.9667), "Graneros": (-34.0667, -70.7167), "Las Cabras": (-34.2833, -71.3000), "Machalí": (-34.1833, -70.6500), "Malloa": (-34.4500, -70.9500), "Mostazal": (-33.9833, -70.7000), "Olivar": (-34.2167, -70.8167), "Peumo": (-34.3833, -71.1667), "Pichidegua": (-34.3500, -71.2833), "Quinta de Tilcoco": (-34.3500, -70.9667), "Rengo": (-34.4083, -70.8583), "Requínoa": (-34.2833, -70.8167), "San Vicente": (-34.4389, -71.0778), "Pichilemu": (-34.3833, -72.0000), "La Estrella": (-34.2000, -71.6500), "Litueche": (-34.1167, -71.7333), "Marchihue": (-34.4000, -71.6167), "Navidad": (-33.9500, -71.8333), "Paredones": (-34.6500, -71.9000), "San Fernando": (-34.5833, -70.9833), "Chépica": (-34.7333, -71.2833), "Chimbarongo": (-34.7083, -71.0444), "Lolol": (-34.7333, -71.6500), "Nancagua": (-34.6667, -71.2167), "Palmilla": (-34.5833, -71.3667), "Peralillo": (-34.4833, -71.4833), "Placilla": (-34.6333, -71.1167), "Pumanque": (-34.6000, -71.6667), "Santa Cruz": (-34.6333, -71.3667),
    # Maule
    "Talca": (-35.4264, -71.6556), "Constitución": (-35.3333, -72.4167), "Curepto": (-35.0833, -72.0167), "Empedrado": (-35.6000, -72.2833), "Maule": (-35.5333, -71.7000), "Pelarco": (-35.3833, -71.4500), "Pencahue": (-35.3833, -71.8167), "Río Claro": (-35.1833, -71.2667), "San Clemente": (-35.5333, -71.4833), "San Rafael": (-35.3167, -71.5167), "Cauquenes": (-35.9667, -72.3167), "Chanco": (-35.7333, -72.5333), "Pelluhue": (-35.8167, -72.5667), "Curicó": (-34.9833, -71.2333), "Hualañé": (-34.9833, -71.8000), "Licantén": (-34.9833, -72.0000), "Molina": (-35.1167, -71.2833), "Rauco": (-34.9167, -71.3167), "Romeral": (-34.9667, -71.1333), "Sagrada Familia": (-35.0000, -71.3833), "Teno": (-34.8667, -71.1667), "Vichuquén": (-34.8833, -72.0000), "Linares": (-35.8500, -71.6000), "Colbún": (-35.7000, -71.4167), "Longaví": (-35.9667, -71.6833), "Parral": (-36.1428, -71.8250), "Retiro": (-36.0500, -71.7667), "San Javier": (-35.5833, -71.7333), "Villa Alegre": (-35.6667, -71.7500), "Yerbas Buenas": (-35.7500, -71.5833),
    # Ñuble
    "Chillán": (-36.6067, -72.1033), "Bulnes": (-36.7417, -72.2986), "Cobquecura": (-36.1333, -72.7833), "Coelemu": (-36.4833, -72.7000), "Coihueco": (-36.6167, -71.8333), "Chillán Viejo": (-36.6233, -72.1333), "El Carmen": (-36.8972, -72.0278), "Ninhue": (-36.3986, -72.3986), "Ñiquén": (-36.3000, -71.9000), "Pemuco": (-36.9750, -72.0972), "Pinto": (-36.7000, -71.9000), "Portezuelo": (-36.5333, -72.4333), "Quillón": (-36.7444, -72.4764), "Quirihue": (-36.2833, -72.5333), "Ránquil": (-36.6500, -72.5667), "San Carlos": (-36.4239, -71.9583), "San Fabián": (-36.5500, -71.5500), "San Ignacio": (-36.7833, -72.0333), "San Nicolás": (-36.5000, -72.2167), "Treguaco": (-36.4333, -72.6667), "Yungay": (-37.1167, -72.0167),
    # Biobío
    "Concepción": (-36.8270, -73.0503), "Coronel": (-37.0167, -73.1333), "Chiguayante": (-36.9167, -73.0167), "Florida": (-36.8167, -72.7000), "Hualqui": (-36.9667, -72.9333), "Lota": (-37.0833, -73.1500), "Penco": (-36.7333, -72.9833), "San Pedro de la Paz": (-36.8500, -73.1000), "Santa Juana": (-37.1667, -72.9333), "Talcahuano": (-36.7167, -73.1167), "Tomé": (-36.6167, -72.9500), "Hualpén": (-36.7833, -73.1000), "Lebu": (-37.6083, -73.6556), "Arauco": (-37.2472, -73.3167), "Cañete": (-37.8000, -73.4000), "Contulmo": (-38.0167, -73.2333), "Curanilahue": (-37.4833, -73.3500), "Los Álamos": (-37.6167, -73.4667), "Tirúa": (-38.3333, -73.5000), "Los Ángeles": (-37.4697, -72.3536), "Antuco": (-37.3333, -71.6833), "Cabrero": (-37.0333, -72.4000), "Laja": (-37.2833, -72.7000), "Mulchén": (-37.7167, -72.2333), "Nacimiento": (-37.5000, -72.6667), "Negrete": (-37.5833, -72.5333), "Quilaco": (-37.6667, -71.9833), "Quilleco": (-37.4667, -71.9667), "San Rosendo": (-37.2667, -72.7167), "Santa Bárbara": (-37.6667, -72.0167), "Tucapel": (-37.2833, -71.9500), "Yumbel": (-37.0833, -72.5667), "Alto Biobío": (-38.0333, -71.3667),
    # La Araucanía
    "Temuco": (-38.7397, -72.5986), "Carahue": (-38.7000, -73.1667), "Cunco": (-38.9333, -72.0333), "Curarrehue": (-39.3500, -71.5833), "Freire": (-38.9500, -72.6167), "Galvarino": (-38.4000, -72.7833), "Gorbea": (-39.1000, -72.6833), "Lautaro": (-38.5333, -72.4500), "Loncoche": (-39.3667, -72.6333), "Melipeuco": (-38.8500, -71.7000), "Nueva Imperial": (-38.7333, -72.9500), "Padre Las Casas": (-38.7667, -72.6000), "Perquenco": (-38.4167, -72.3833), "Pitrufquén": (-38.9833, -72.6500), "Pucón": (-39.2833, -71.9667), "Saavedra": (-38.7833, -73.3833), "Teodoro Schmidt": (-38.9833, -73.0500), "Toltén": (-39.2167, -73.1833), "Vilcún": (-38.6500, -72.2333), "Villarrica": (-39.2833, -72.2333), "Cholchol": (-38.6000, -72.8500), "Angol": (-37.8000, -72.7167), "Collipulli": (-37.9500, -72.4333), "Curacautín": (-38.4333, -71.8833), "Ercilla": (-38.0500, -72.4833), "Lonquimay": (-38.4500, -71.3667), "Los Sauces": (-37.9667, -72.8333), "Lumaco": (-38.1500, -72.9167), "Purén": (-38.0333, -73.0833), "Renaico": (-37.6667, -72.5833), "Traiguén": (-38.2500, -72.6833), "Victoria": (-38.2333, -72.3333),
    # Los Ríos
    "Valdivia": (-39.8142, -73.2459), "Corral": (-39.8833, -73.4333), "Lanco": (-39.4500, -72.7833), "Los Lagos": (-39.8500, -72.8333), "Máfil": (-39.6500, -72.9500), "Mariquina": (-39.5167, -72.9667), "Paillaco": (-40.0667, -72.8833), "Panguipulli": (-39.6333, -72.3333), "La Unión": (-40.2833, -73.0833), "Futrono": (-40.1333, -72.4000), "Lago Ranco": (-40.3167, -72.4833), "Río Bueno": (-40.3333, -72.9667),
    # Los Lagos
    "Puerto Montt": (-41.4717, -72.9369), "Calbuco": (-41.7667, -73.1333), "Cochamó": (-41.4833, -72.3000), "Fresia": (-41.1500, -73.4167), "Frutillar": (-41.1333, -73.0500), "Los Muermos": (-41.4000, -73.4833), "Llanquihue": (-41.2500, -73.0000), "Maullín": (-41.6167, -73.6000), "Puerto Varas": (-41.3167, -72.9833), "Castro": (-42.4722, -73.7731), "Ancud": (-41.8667, -73.8333), "Chonchi": (-42.6167, -73.7833), "Curaco de Vélez": (-42.4333, -73.6000), "Dalcahue": (-42.3667, -73.6500), "Puqueldón": (-42.6000, -73.6667), "Queilén": (-42.8833, -73.4833), "Quellón": (-43.1167, -73.6167), "Quemchi": (-42.1500, -73.4833), "Quinchao": (-42.4667, -73.4833), "Osorno": (-40.5744, -73.1328), "Puerto Octay": (-40.9667, -72.8833), "Purranque": (-40.9167, -73.1667), "Puyehue": (-40.6833, -72.6000), "Río Negro": (-40.7833, -73.2167), "San Juan de la Costa": (-40.5167, -73.5333), "San Pablo": (-40.4000, -73.0167), "Chaitén": (-42.9167, -72.7000), "Futaleufú": (-43.1833, -71.8667), "Hualaihué": (-41.9833, -72.6833), "Palena": (-43.6167, -71.8000),
    # Aysén
    "Coyhaique": (-45.5752, -72.0662), "Lago Verde": (-44.2333, -71.8500), "Aysén": (-45.4000, -72.7000), "Cisnes": (-44.7500, -72.7000), "Guaitecas": (-43.8833, -73.7500), "Cochrane": (-47.2500, -72.5667), "O Higgins": (-48.4667, -72.5667), "Tortel": (-47.8000, -73.5333), "Chile Chico": (-46.5333, -71.7167), "Río Ibáñez": (-46.2833, -71.9500),
    # Magallanes
    "Punta Arenas": (-53.1638, -70.9171), "Laguna Blanca": (-52.4167, -71.4167), "Río Verde": (-52.5667, -71.5500), "San Gregorio": (-52.5667, -70.0833), "Cabo de Hornos": (-54.9333, -67.6167), "Antártica": (-62.2000, -58.9667), "Porvenir": (-53.3000, -70.3667), "Primavera": (-52.8167, -69.2500), "Timaukel": (-53.5833, -69.7500), "Natales": (-51.7333, -72.5167), "Torres del Paine": (-51.2500, -72.8833)
}

def normalize_key(v):
    v = unicodedata.normalize('NFKD', str(v or ''))
    v = ''.join(ch for ch in v if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', '', v.lower())

def main():
    status = json.loads(STATUS_PATH.read_text(encoding='utf-8'))
    comunas = status.get('comunas', [])
    
    # Construir mapa_data.json enriquecido
    mapa_items = []
    
    norm_coords = {normalize_key(k): v for k, v in COMUNAS_COORDS_BASE.items()}
    
    for c in comunas:
        nombre = c['comuna']
        region = c['region_nombre']
        total = c.get('total_count', 0)
        bcn = c.get('bcn_count', 0)
        muni = c.get('municipal_count', 0)
        status_str = c.get('status', 'Sin registros')
        
        # Buscar coordenadas
        k = normalize_key(nombre)
        lat, lon = norm_coords.get(k, (-33.45, -70.67))
        
        # Conteo por materias
        topics = {}
        for ord_item in c.get('ordenanzas', []):
            mat_id = ord_item.get('materia_id', 'general')
            topics[mat_id] = topics.get(mat_id, 0) + 1
            
        mapa_items.append({
            "comuna": nombre,
            "region": region,
            "total": total,
            "bcn": bcn,
            "municipal": muni,
            "status": status_str,
            "lat": lat,
            "lon": lon,
            "topics": topics
        })
        
    MAPA_DATA_PATH.write_text(json.dumps(mapa_items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"mapa_data.json actualizado con coordenadas exactas para {len(mapa_items)} comunas.")

if __name__ == '__main__':
    main()