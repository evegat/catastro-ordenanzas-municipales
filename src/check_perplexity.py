# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

url = "https://www.perplexity.ai/search/bf27cbd0-c280-40ac-b5f1-9794483db988"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000, wait_until="networkidle")
    time.sleep(4.0)
    text = page.evaluate("() => document.body.innerText")
    page.screenshot(path="data/perplexity_screenshot.png")
    Path("data/pplx_raw.txt").write_text(text, encoding="utf-8")
    print(f"Perplexity descargado. Longitud de texto: {len(text)}")
    print(f"Primeros 200 caracteres:\n{text[:200]}")
    browser.close()