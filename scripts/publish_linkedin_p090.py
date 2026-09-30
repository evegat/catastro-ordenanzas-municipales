#!/usr/bin/env python3
"""
publish_linkedin_p090.py
Script oficial para publicación en LinkedIn del Catastro Nacional de Ordenanzas Municipales (P090)
con imagen real adjunta vía LinkedIn REST API (v202503).
"""

import os
import sys
import json
from pathlib import Path
import requests

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Rutas clave
ENV_PATH = Path(r"C:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P137 - Teletrabajo y Compras Publicas 4D\.env")
IMAGE_PATH = Path(r"D:\Proyectos\P090 - Catastro Ordenanzas Municipales BCN\dashboard\captura_producto_real.png")

POST_TEXT = """Haciendo clases de Presupuesto en la U. Alberto Hurtado, guiando proyectos en la U. de Chile o apoyando a una colega a comparar cómo comunas como Maipú regulan el arbolado urbano y la mantención de áreas verdes frente a otros municipios, siempre aparecía la misma pregunta: ¿cómo saber qué ordenanzas tienen otras comunas para comparar?

La respuesta siempre era frustrante: decretos dispersos en cientos de sitios web, enlaces caídos, PDFs escaneados y registros que se pierden con cada cambio de alcalde.

Para resolver esa asimetría de raíz, crucé los registros de la Biblioteca del Congreso Nacional (BCN) y fuentes comunales en un Catastro Nacional de Ordenanzas Municipales abierto y verificable:

📌 7.462 normas catalogadas (5.881 de BCN LeyChile + 1.581 de municipios con verificación documental SHA-256).

📌 346 comunas cubiertas con trazabilidad de su brecha temporal.

📌 Explorador temático de materias clave (Derechos Municipales, Aseo, Medio Ambiente, Áreas Verdes, Mascotas y Convivencia).

📌 Asistente normativo local que corre en tu navegador (sin costo ni fuga de datos).

📌 Datos abiertos en CSV y notebook didáctico en Python para docencia e investigación aplicada.

Pongo esta herramienta al servicio de concejales, administradores públicos, investigadores y estudiantes:

🔗 https://ordenanzas.evegat.cl/?utm_source=linkedin&utm_medium=social&utm_campaign=lanzamiento_ordenanzas

El catastro es colaborativo: si en tu comuna falta alguna norma vigente, puedes sumarla directo al buzón para seguir completando el mapa.

#GestionPublica #Municipalidades #MedioAmbiente #AreasVerdes #GovTech #DatosAbiertos #Transparencia #Chile #FAGOB #UAH"""

def escape_linkedin_little_text(text: str) -> str:
    """
    Escapa caracteres de control reservados en el formato Little Text Format de LinkedIn
    para prevenir que la API mutile o trunque silenciosamente el texto en paréntesis o símbolos.
    Caracteres reservados de control: ( ) [ ] { } < > @ | ~ * \\
    Nota: Se preserva '#' para hashtags y '_' para enlaces/texto normal.
    """
    import re
    # 1. Escapar barras invertidas primero
    escaped = text.replace('\\', '\\\\')
    # 2. Escapar paréntesis, corchetes, llaves, arroba, pipes, asteriscos, tildes, menor/mayor que
    chars_to_escape = r'([|{}[\]()<>@*~])'
    return re.sub(chars_to_escape, r'\\\1', escaped)

def load_env() -> dict:
    config = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

def upload_image_to_linkedin(token: str, author_urn: str, image_path: Path) -> str:
    """Sube una imagen a LinkedIn y retorna su URN (urn:li:image:...)."""
    if not image_path.exists():
        raise FileNotFoundError(f"No existe la imagen en {image_path}")

    # Paso 1: Initialize Upload
    init_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "initializeUploadRequest": {
            "owner": author_urn
        }
    }
    
    print("1. Inicializando carga de imagen en LinkedIn API...")
    r = requests.post(init_url, headers=headers, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Fallo al inicializar imagen ({r.status_code}): {r.text}")
    
    init_data = r.json().get("value", {})
    upload_url = init_data.get("uploadUrl")
    image_urn = init_data.get("image")
    
    print(f"   -> Image URN asignado: {image_urn}")
    print(f"2. Subiendo binario ({image_path.stat().st_size} bytes)...")
    
    # Paso 2: Subir archivo binario al endpoint firmado
    image_bytes = image_path.read_bytes()
    put_headers = {
        "Content-Type": "image/png"
    }
    r_upload = requests.put(upload_url, headers=put_headers, data=image_bytes)
    if r_upload.status_code not in (200, 201):
        raise RuntimeError(f"Fallo al subir bytes ({r_upload.status_code}): {r_upload.text}")
    
    print("   -> Binario subido con éxito (HTTP 200/201).")
    return image_urn

def publish_post(dry_run: bool = True) -> dict:
    env = load_env()
    token = env.get("LINKEDIN_ACCESS_TOKEN")
    author_urn = env.get("LINKEDIN_AUTHOR_URN")
    
    if not token or not author_urn:
        return {"success": False, "error": "Faltan credenciales en .env"}
    
    print(f"Author URN: {author_urn}")
    print(f"Longitud texto: {len(POST_TEXT)} caracteres")
    print(f"Modo: {'DRY-RUN (Simulación)' if dry_run else 'EN VIVO (Publicación Real)'}")
    
    if dry_run:
        return {
            "success": True,
            "mode": "DRY_RUN",
            "author": author_urn,
            "text_length": len(POST_TEXT),
            "image_path": str(IMAGE_PATH),
            "preview": POST_TEXT
        }
    
    # Subir imagen
    image_urn = upload_image_to_linkedin(token, author_urn, IMAGE_PATH)
    
    # Crear post
    post_url = "https://api.linkedin.com/rest/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202503",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    post_payload = {
        "author": author_urn,
        "commentary": POST_TEXT,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "id": image_urn,
                "title": "MuniData GovTech - Catastro Nacional de Ordenanzas Municipales"
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    
    print("3. Publicando post en LinkedIn...")
    r_post = requests.post(post_url, headers=headers, json=post_payload)
    if r_post.status_code in (200, 201):
        post_urn = r_post.headers.get("x-restli-id", "")
        # Extraer ID limpio para la URL
        post_id = post_urn.replace("urn:li:share:", "").replace("urn:li:ugcPost:", "")
        web_url = f"https://www.linkedin.com/feed/update/{post_urn}"
        print(f"\n¡PUBLICACIÓN EXITOSA!")
        print(f"Post URN: {post_urn}")
        print(f"Enlace en vivo: {web_url}")
        return {
            "success": True,
            "status_code": r_post.status_code,
            "post_urn": post_urn,
            "url": web_url
        }
    else:
        print(f"\nError al publicar ({r_post.status_code}): {r_post.text}")
        return {
            "success": False,
            "status_code": r_post.status_code,
            "error": r_post.text
        }

if __name__ == "__main__":
    is_live = "--live" in sys.argv
    res = publish_post(dry_run=not is_live)
    print(json.dumps(res, indent=2, ensure_ascii=False))
