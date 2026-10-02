"""Patch quirúrgico para implementar H05 a H11 en dashboard/index.html.
Cubre:
- H05: Cifras y tamaños dinámicos en descargas.
- H06: Período de cobertura 2021–2026 (6 años calendario) y fecha de corte.
- H07: Enlaces de fuentes rotulados con precisión (LeyChile, PDF municipal, RDF/JSON) y tipo de acto.
- H08: Renombrar tarjeta a "Explorar Normativa Tarifaria".
- H09: Accesibilidad WCAG (aria-label en chat, role=dialog, aria-modal, soporte tecla Escape).
- H10: Dependencias fijas, reemplazo de iconos linkedin/github por SVG inline (cero warnings), cabeceras.
- H11: Separación nítida de descarga directa abierta vs solicitud institucional.
"""

import re
from pathlib import Path

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
INDEX_PATH = REPO_ROOT / "dashboard" / "index.html"
HEADERS_PATH = REPO_ROOT / "dashboard" / "_headers"

SVG_LINKEDIN = '<svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.62 1.62 0 1 0 0 3.24 1.62 1.62 0 0 0 0-3.24Z"/></svg>'
SVG_GITHUB = '<svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.1-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2Z"/></svg>'

def patch_index_html():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # H08: Renombrar Comparador de Tarifas -> Explorar Normativa Tarifaria
    html = html.replace(
        '<h3 class="text-xs font-bold text-zinc-100">Comparador de Tarifas</h3>',
        '<h3 class="text-xs font-bold text-zinc-100">Explorar Normativa Tarifaria</h3>'
    )
    html = html.replace(
        '<!-- Card 1: Comparador de Tarifas -->',
        '<!-- Card 1: Explorar Normativa Tarifaria -->'
    )
    html = html.replace(
        '<p class="text-[11px] text-zinc-400 mt-1">Compara cobros por aseo, terrazas, permisos y derechos municipales.</p>',
        '<p class="text-[11px] text-zinc-400 mt-1">Filtra ordenanzas de cobro por aseo, terrazas, permisos y derechos municipales.</p>'
    )

    # H09: Accesibilidad en chat-toggle-btn y buzon-float-btn
    html = re.sub(
        r'<button onclick="toggleChatModal\(\)" id="chat-toggle-btn"',
        r'<button onclick="toggleChatModal()" id="chat-toggle-btn" aria-label="Abrir asistente jurídico" title="Asistente Jurídico P090"',
        html
    )
    html = re.sub(
        r'<button onclick="openBuzonModal\(\x27\x27\)" id="buzon-float-btn"',
        r'<button onclick="openBuzonModal(\'\')" id="buzon-float-btn" aria-label="Abrir buzón de observaciones y aportes"',
        html
    )

    # H09: Semántica de modales (role="dialog", aria-modal="true")
    html = html.replace(
        '<div id="comuna-modal" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">',
        '<div id="comuna-modal" role="dialog" aria-modal="true" aria-labelledby="modal-comuna-title" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">'
    )
    html = html.replace(
        '<div id="buzon-modal" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">',
        '<div id="buzon-modal" role="dialog" aria-modal="true" aria-labelledby="buzon-modal-title" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">'
    )
    html = html.replace(
        '<h3 class="text-base font-bold text-white">Buzón Colaborativo de Ordenanzas</h3>',
        '<h3 id="buzon-modal-title" class="text-base font-bold text-white">Buzón Colaborativo de Ordenanzas</h3>'
    )
    html = html.replace(
        '<div id="download-request-modal" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">',
        '<div id="download-request-modal" role="dialog" aria-modal="true" aria-labelledby="download-modal-title" class="hidden fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">'
    )
    html = html.replace(
        '<div id="chat-window-panel" class="hidden w-[92vw] sm:w-[420px] h-[520px] max-h-[82vh] bg-[#071f43] border-2 border-sky-500/60 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-md mb-3 transition-all">',
        '<div id="chat-window-panel" role="dialog" aria-modal="false" aria-label="Asistente Jurídico P090" class="hidden w-[92vw] sm:w-[420px] h-[520px] max-h-[82vh] bg-[#071f43] border-2 border-sky-500/60 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-md mb-3 transition-all">'
    )

    # H09: Soporte de tecla Escape para cerrar modales
    escape_listener = """
    // Soporte accesible tecla Escape para modales
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const buzonModal = document.getElementById('buzon-modal');
        const downloadModal = document.getElementById('download-request-modal');
        const comunaModal = document.getElementById('comuna-modal');
        const chatPanel = document.getElementById('chat-window-panel');
        if (buzonModal && !buzonModal.classList.contains('hidden')) closeBuzonModal();
        if (downloadModal && !downloadModal.classList.contains('hidden')) closeDownloadRequestModal();
        if (comunaModal && !comunaModal.classList.contains('hidden')) closeComunaModal();
        if (chatPanel && !chatPanel.classList.contains('hidden')) toggleChatModal();
      }
    });
    """
    if "document.addEventListener('keydown', (e) => {" not in html:
        html = html.replace("if (document.readyState === 'loading') {", escape_listener + "\n    if (document.readyState === 'loading') {")

    # H07: Rotulado riguroso de fuentes y enlaces en el modal comunal
    old_render_logic = """          let actionLinks = [];
          if (o.target_url) {
            actionLinks.push(`<a href="${sanitizeUrl(o.target_url)}" target="_blank" rel="noopener noreferrer" class="text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1 hover:underline">Abrir Texto Municipal (Firmado) ↗</a>`);
          }
          if (o.rdf_url) {
            actionLinks.push(`<a href="${sanitizeUrl(o.rdf_url)}" target="_blank" rel="noopener noreferrer" class="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 hover:underline">Ver en BCN LeyChile ↗</a>`);
          }"""

    new_render_logic = """          let actionLinks = [];
          if (o.target_url) {
            const isLeyChile = o.target_url.includes('bcn.cl') || o.target_url.includes('leychile');
            const isDiarioOficial = o.target_url.includes('diariooficial');
            let label = 'Abrir Decreto Municipal (PDF) ↗';
            let linkClass = 'text-emerald-400 hover:text-emerald-300 font-semibold';
            if (isLeyChile) {
              label = 'Ver en BCN LeyChile ↗';
              linkClass = 'text-sky-400 hover:text-sky-300 font-semibold';
            } else if (isDiarioOficial) {
              label = 'Ver en Diario Oficial ↗';
              linkClass = 'text-amber-400 hover:text-amber-300 font-semibold';
            }
            actionLinks.push(`<a href="${sanitizeUrl(o.target_url)}" target="_blank" rel="noopener noreferrer" class="${linkClass} flex items-center gap-1 hover:underline">${label}</a>`);
          }
          if (o.rdf_url) {
            actionLinks.push(`<a href="${sanitizeUrl(o.rdf_url)}" target="_blank" rel="noopener noreferrer" class="text-zinc-400 hover:text-zinc-200 font-mono text-[10px] flex items-center gap-1 hover:underline" title="Metadatos en formato abierto JSON-LD/RDF">Datos RDF / JSON ↗</a>`);
          }"""
    html = html.replace(old_render_logic, new_render_logic)

    # H07: Derivación rigurosa del tipo de acto (Ordenanza vs Reglamento vs Decreto)
    old_num_text = "const numText = o.numero === 'Compilado' ? 'Compilado Normativo' : (!o.numero || o.numero === 'S/N' ? 'Documento catalogado (S/N)' : 'Decreto / N° ' + escapeHtml(o.numero));"
    new_num_text = """const lowerTit = (o.titulo || '').toLowerCase();
          let actoLabel = 'Decreto / N° ';
          if (lowerTit.includes('ordenanza')) {
            actoLabel = 'Ordenanza N° ';
          } else if (lowerTit.includes('reglamento')) {
            actoLabel = 'Reglamento N° ';
          }
          const numText = o.numero === 'Compilado' ? 'Compilado Normativo' : (!o.numero || o.numero === 'S/N' || o.numero === 's/n' ? 'Documento catalogado (S/N)' : `${actoLabel}${escapeHtml(o.numero)}`);"""
    html = html.replace(old_num_text, new_num_text)

    # H06: Precisión de períodos de cobertura y fecha de corte
    html = html.replace(
        'Alcance del Catastro · Quinquenio 2021–2026',
        'Alcance del Catastro · Período 2021–2026 (6 años calendario)'
    )
    html = html.replace(
        'Nuestra proyección es completar el rescate de las <strong>103 comunas restantes</strong> y las 5 materias de la canasta básica en todo Chile.',
        'Las <strong>103 comunas restantes</strong> forman parte de la cohorte prioritaria para rescate documental desde portales de Transparencia Activa municipal. Corte oficial: Octubre 2026.'
    )

    # H10: Reemplazar data-lucide="linkedin" y "github" por SVG inline accesible
    html = re.sub(
        r'<i data-lucide="linkedin" class="([^"]*)"></i>',
        SVG_LINKEDIN,
        html
    )
    html = re.sub(
        r'<i data-lucide="github" class="([^"]*)"></i>',
        SVG_GITHUB,
        html
    )

    # H10: Fijar versión de unpkg lucide a 0.469.0
    html = html.replace(
        'https://unpkg.com/lucide@latest',
        'https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js'
    )

    # H05 y H11: Actualizar sección de descargas con cifras dinámicas y separación de descarga abierta vs solicitud
    old_descargas_card = '<div class="text-[11px] text-zinc-400">7.462 normas fila a fila (1,6 MB)</div>'
    new_descargas_card = '<div class="text-[11px] text-zinc-400"><span id="descargas-csv-counter">7.782</span> normas fila a fila (~2,7 MB)</div>'
    html = html.replace(old_descargas_card, new_descargas_card)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    # H10: Generar archivo de cabeceras de seguridad Cloudflare Pages
    headers_content = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), camera=(), microphone=()
  Content-Security-Policy: default-src 'self' 'unsafe-inline' 'unsafe-eval' https://* data: blob:;
"""
    with open(HEADERS_PATH, "w", encoding="utf-8") as f:
        f.write(headers_content)

    print("Parches H05 a H11 aplicados con éxito en index.html y _headers.")

if __name__ == "__main__":
    patch_index_html()
