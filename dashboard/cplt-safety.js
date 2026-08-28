(() => {
  'use strict';

  const PORTAL_TRANSPARENCIA = 'https://www.portaltransparencia.cl/PortalPdT/';
  const WARNING_TEXT = 'Referencia histórica de Transparencia Activa/municipal. El enlace directo almacenado no ha sido verificado y puede haber cambiado, redirigir o devolver 404.';

  function replaceText(selector, from, to) {
    document.querySelectorAll(selector).forEach((el) => {
      if ((el.textContent || '').includes(from)) el.textContent = to;
    });
  }

  function sanitizeCpltCards() {
    const container = document.getElementById('drawer-ordinances-list');
    if (!container) return;

    Array.from(container.children).forEach((card) => {
      const spans = Array.from(card.querySelectorAll('span'));
      const cpltBadge = spans.find((span) => /CPLT\s+VIGENTE/i.test(span.textContent || ''));
      if (!cpltBadge || card.dataset.cpltSafetyApplied === '1') return;

      card.dataset.cpltSafetyApplied = '1';
      cpltBadge.textContent = 'CPLT / MUNICIPAL · ENLACE NO VERIFICADO';
      cpltBadge.title = WARNING_TEXT;

      const actionArea = Array.from(card.querySelectorAll('div')).find((div) =>
        (div.className || '').includes('border-t') && div.querySelector('button')
      );

      const buttons = Array.from(card.querySelectorAll('button'));
      const openButton = buttons.find((button) => /Abrir Documento CPLT/i.test(button.textContent || ''));
      if (openButton) {
        openButton.onclick = (event) => {
          event.stopPropagation();
          window.open(PORTAL_TRANSPARENCIA, '_blank', 'noopener,noreferrer');
        };
        openButton.title = 'Abrir el Portal de Transparencia oficial para buscar el organismo y verificar el documento.';
        const label = openButton.querySelector('span');
        if (label) label.textContent = 'Consultar Portal de Transparencia ↗';
      }

      const copyButton = buttons.find((button) => /Copiar link/i.test(button.textContent || ''));
      if (copyButton) {
        copyButton.title = WARNING_TEXT;
        const label = copyButton.querySelector('span');
        if (label) label.textContent = 'Copiar URL histórica';
      }

      if (actionArea && !card.querySelector('[data-cplt-warning]')) {
        const warning = document.createElement('p');
        warning.dataset.cpltWarning = '1';
        warning.className = 'text-[11px] leading-relaxed text-amber-300/90 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2';
        warning.textContent = WARNING_TEXT;
        actionArea.parentNode.insertBefore(warning, actionArea);
      }
    });
  }

  function patchStaticLabels() {
    replaceText(
      '#commune-drawer p',
      'Listado de ordenanzas oficiales disponibles (BCN & Transparencia Activa CPLT).',
      'Registros BCN y referencias complementarias de Transparencia Activa municipal. Los enlaces CPLT se verifican por separado.'
    );
    replaceText(
      '#commune-drawer span',
      'Fuentes: BCN LeyChile & Transparencia CPLT',
      'Fuentes: BCN LeyChile & referencias de Transparencia Activa municipal'
    );
  }

  function boot() {
    patchStaticLabels();
    sanitizeCpltCards();

    const container = document.getElementById('drawer-ordinances-list');
    if (container) {
      const observer = new MutationObserver(() => sanitizeCpltCards());
      observer.observe(container, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
