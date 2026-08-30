from playwright.sync_api import sync_playwright
import time

url = "https://municipalidadmaipu.cl/ordenanzas/"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=30000, wait_until="domcontentloaded")
    time.sleep(3.0)
    links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => ({href: a.href, text: a.innerText || ''}))")
    print(f"Total enlaces encontrados en Maipu: {len(links)}")
    pdf_links = []
    for l in links:
        if "pdf" in l["href"].lower() or "ordenanza" in l["text"].lower():
            print(f"{l['text']} -> {l['href']}")
            pdf_links.append(l)
    print(f"Total PDFs de ordenanzas en Maipu: {len(pdf_links)}")
    browser.close()