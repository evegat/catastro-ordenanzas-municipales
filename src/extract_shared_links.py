from playwright.sync_api import sync_playwright
import time, json

urls = [
    ("perplexity", "https://www.perplexity.ai/search/bf27cbd0-c280-40ac-b5f1-9794483db988"),
    ("gemini", "https://share.gemini.google/f1fO0DFUy33N")
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for name, url in urls:
        print(f"Abriendo {name}: {url}...")
        try:
            page = browser.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(4.0)
            text = page.evaluate("() => document.body.innerText")
            out_file = f"data/{name}_dump_2.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Guardado {out_file}. Longitud: {len(text)}")
            page.close()
        except Exception as e:
            print(f"Error en {name}: {e}")
    browser.close()