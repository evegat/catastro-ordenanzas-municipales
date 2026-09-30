from playwright.sync_api import sync_playwright
from pathlib import Path

p_urn = 'urn:li:share:7511144282653843457'
url = f'https://www.linkedin.com/feed/update/{p_urn}'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1200})
    page.goto(url, wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(4000)
    
    # Click en 'ver más'
    try:
        btns = page.locator("button, span").filter(has_text="más").all()
        for b in btns:
            try:
                b.click(timeout=500)
            except Exception:
                pass
    except Exception:
        pass
    
    page.wait_for_timeout(1000)
    shot_path = Path('reports/verificacion_en_vivo_exitosa.png')
    shot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shot_path), full_page=False)
    
    content = page.content()
    print('Has link:', 'ordenanzas.evegat.cl' in content)
    print('Has hashtags:', 'GestionPublica' in content)
    print('Has 7.462:', '7.462' in content)
    print('Screenshot saved to:', shot_path)
    browser.close()
