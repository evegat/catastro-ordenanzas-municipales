import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Ratio 16:9 de alta resolución para feed de LinkedIn
        context = await browser.new_context(viewport={'width': 1200, 'height': 675}, device_scale_factor=2)
        page = await context.new_page()
        # Usar archivo local para asegurar versión exacta saneada (7.462 normas)
        html_file = 'file:///D:/Proyectos/P090%20-%20Catastro%20Ordenanzas%20Municipales%20BCN/dashboard/index.html'
        await page.goto(html_file, wait_until='networkidle')
        await page.wait_for_timeout(1000)
        
        # Activar modo oscuro institucional
        await page.evaluate("setTheme('dark')")
        await page.wait_for_timeout(800)
        
        # Captura de la vista principal con buscador y métricas
        await page.screenshot(path='dashboard/captura_producto_real.png')
        print("Captura de producto real guardada en dashboard/captura_producto_real.png")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(capture())
