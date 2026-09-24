"""Generador de banner oficial OpenGraph (1200x630 px) para P090."""
from PIL import Image, ImageDraw, ImageFont
import os

def create_og_banner(output_path: str):
    width, height = 1200, 630
    img = Image.new("RGBA", (width, height), (4, 20, 43, 255))
    draw = ImageDraw.Draw(img)

    # Fondo decorativo: gradiente o capas de profundidad
    for y in range(height):
        # Gradiente suave de #04142b a #071f43
        r = int(4 + (7 - 4) * (y / height))
        g = int(20 + (31 - 20) * (y / height))
        b = int(43 + (67 - 43) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Resplandor radial o círculo de acento en la esquina superior derecha
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for radius in range(350, 0, -5):
        alpha = int(35 * (1 - radius / 350))
        glow_draw.ellipse(
            [(950 - radius, 120 - radius), (950 + radius, 120 + radius)],
            fill=(2, 132, 199, alpha)
        )
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Marco exterior sutil
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(21, 59, 112, 200), width=2)
    draw.rectangle([(24, 24), (width - 24, height - 24)], outline=(2, 132, 199, 40), width=1)

    # Fuentes
    font_dir = "C:/Windows/Fonts"
    font_pill = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 18)
    font_title = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 52)
    font_subtitle = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 24)
    font_stat_num = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 46)
    font_stat_lbl = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 16)
    font_footer_bold = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 18)
    font_footer = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 18)

    # 1. Pill superior
    pill_text = "DATOS ABIERTOS & GOBIERNO LOCAL  ·  CHILE 2026"
    draw.rounded_rectangle([(60, 60), (530, 96)], radius=18, fill=(7, 31, 67, 230), outline=(56, 189, 248, 120), width=1)
    # Punto verde en el pill
    draw.ellipse([(76, 74), (86, 84)], fill=(16, 185, 129, 255))
    draw.text((98, 68), pill_text, font=font_pill, fill=(56, 189, 248, 255))

    # 2. Título principal
    draw.text((60, 120), "Catastro Nacional de", font=font_title, fill=(255, 255, 255, 255))
    draw.text((60, 182), "Ordenanzas Municipales", font=font_title, fill=(56, 189, 248, 255))

    # 3. Subtítulo
    draw.text((60, 255), "Primer catálogo exhaustivo con verificación criptográfica SHA-256 y asistente jurídico", font=font_subtitle, fill=(203, 213, 225, 255))

    # 4. Cajas de Métricas (3 cards)
    cards = [
        ("7.321", "Normas Oficiales Consolidadas", (56, 189, 248, 255)),
        ("346 / 346", "Comunas (100% Nacional)", (16, 185, 129, 255)),
        ("6 por Ley", "Auditor Normas Obligatorias", (245, 158, 11, 255)),
    ]

    card_y = 320
    card_w = 340
    card_h = 140
    gap = 25
    start_x = 60

    for i, (num, label, color) in enumerate(cards):
        cx = start_x + i * (card_w + gap)
        # Fondo card
        draw.rounded_rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], radius=16, fill=(7, 31, 67, 200), outline=(21, 59, 112, 230), width=2)
        # Línea de acento superior
        draw.line([(cx + 20, card_y), (cx + card_w - 20, card_y)], fill=color, width=3)
        # Número grande
        draw.text((cx + 24, card_y + 24), num, font=font_stat_num, fill=color)
        # Label
        draw.text((cx + 24, card_y + 88), label, font=font_stat_lbl, fill=(148, 163, 184, 255))

    # 5. Barra inferior / Footer de Autoría
    draw.line([(60, 520), (width - 60, 520)], fill=(21, 59, 112, 180), width=1)

    draw.text((60, 545), "Investigador Principal: ", font=font_footer, fill=(148, 163, 184, 255))
    draw.text((230, 545), "Eduardo Vega Toro", font=font_footer_bold, fill=(255, 255, 255, 255))
    draw.text((400, 545), "·  Universidad de Chile (FAGOB)", font=font_footer, fill=(148, 163, 184, 255))

    url_text = "https://ordenanzas.evegat.cl"
    draw.text((width - 340, 545), url_text, font=font_footer_bold, fill=(56, 189, 248, 255))

    # Guardar
    rgb_img = img.convert("RGB")
    rgb_img.save(output_path, "PNG", quality=95)
    print(f"[OK] Banner generado exitosamente en: {output_path}")

if __name__ == "__main__":
    out = os.path.abspath("dashboard/og-image.png")
    create_og_banner(out)
