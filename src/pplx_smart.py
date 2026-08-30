# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

url = "https://www.perplexity.ai/search/bf27cbd0-c280-40ac-b5f1-9794483db988"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()
    try:
        page.goto(url, timeout=20000, wait_until="commit")
        time.sleep(6.0)
        # Extraer todo el contenido del DOM
        text = page.evaluate("() => document.body ? document.body.innerText : 'NO_BODY'")
        html = page.content()
        Path("data/pplx_smart_text.txt").write_text(text, encoding="utf-8")
        Path("data/pplx_smart_html.html").write_text(html, encoding="utf-8")
        print(f"Perplexity leido con exito. Longitud texto: {len(text)}")
        print(f"Inicio texto: {text[:300]}")
    except Exception as e:
        print(f"Error al abrir: {e}")
    browser.close()