// Mapa Interactivo de Chile - Catastro Ordenanzas Municipales P090
// Leaflet.js + mapa_data.json - Cargado dinámicamente al activar el tab

(function () {
  'use strict';

  let mapaInstance = null;
  let allMarkers = [];
  let mapaData = [];

  const TOPIC_LABELS = {
    ALL: 'Todas las materias',
    derechos_tarifas: 'Derechos Municipales y Tarifas',
    comercio_alcoholes: 'Comercio, Alcoholes y Patentes',
    aseo_medioambiente: 'Aseo, Ornato y Medio Ambiente',
    transito_transporte: 'Tránsito y Transporte',
    urbanismo_obras: 'Urbanismo, Obras y Edificación',
    seguridad_convivencia: 'Seguridad y Convivencia',
    tenencia_mascotas: 'Tenencia Responsable de Mascotas',
    social_salud_deporte: 'Salud, Deporte y Desarrollo Social',
    participacion_ciudadana: 'Participación Ciudadana',
    administracion_interna: 'Organización y Régimen Interno',
    general: 'Normativa General y Otras Materias',
    alcoholes_comercio: 'Comercio, Alcoholes y Patentes',
    mascotas_animales: 'Tenencia Responsable de Mascotas',
  };

  const TOPIC_ALIASES = {
    alcoholes_comercio: 'comercio_alcoholes',
    comercio_alcoholes: 'alcoholes_comercio',
    tenencia_mascotas: 'mascotas_animales',
    mascotas_animales: 'tenencia_mascotas',
  };

  function getTopicCount(item, topicFilter) {
    if (!item || !item.topics) return 0;
    if (topicFilter === 'ALL') return item.total || 0;
    let count = item.topics[topicFilter] || 0;
    const alias = TOPIC_ALIASES[topicFilter];
    if (alias && item.topics[alias]) {
      count += item.topics[alias];
    }
    return count;
  }

  function getMarkerColor(item, topicFilter) {
    if (item.total === 0) return '#4b5563'; // sin datos - gris

    if (topicFilter === 'ALL') return '#54b995'; // verde catastro

    const count = getTopicCount(item, topicFilter);
    if (count === 0) return '#d97706'; // amber: tiene datos pero no en esta materia
    return '#54b995'; // verde: tiene datos en esta materia
  }

  function getMarkerRadius(item, topicFilter) {
    if (item.total === 0) return 4;
    if (topicFilter === 'ALL') return Math.min(5 + Math.sqrt(item.total) * 0.8, 14);
    const count = getTopicCount(item, topicFilter);
    if (count === 0) return 4;
    return Math.min(5 + Math.sqrt(count) * 1.5, 14);
  }

  function buildPopup(item, topicFilter) {
    const topicCount = topicFilter !== 'ALL' ? getTopicCount(item, topicFilter) : item.total;
    const topicLine = topicFilter !== 'ALL'
      ? `<tr><td style="color:#94a3b8;font-size:10px">Materia filtrada</td><td style="color:#54b995;font-weight:600">${topicCount} normas</td></tr>`
      : '';
    const topicsRows = Object.entries(item.topics || {})
      .filter(([, v]) => v > 0)
      .map(([k, v]) => `<tr><td style="color:#94a3b8;font-size:10px">${TOPIC_LABELS[k] || TOPIC_LABELS[TOPIC_ALIASES[k]] || k}</td><td style="color:#e2e8f0">${v}</td></tr>`)
      .join('');

    return `
      <div style="font-family:sans-serif;min-width:200px;background:#071f43;color:#e2e8f0;border-radius:8px;padding:10px 12px">
        <div style="font-size:13px;font-weight:700;color:#38bdf8;margin-bottom:4px">${item.comuna}</div>
        <div style="font-size:10px;color:#94a3b8;margin-bottom:6px">${item.region}</div>
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="color:#94a3b8;font-size:10px">Total ordenanzas</td><td style="color:#54b995;font-weight:700">${item.total}</td></tr>
          <tr><td style="color:#94a3b8;font-size:10px">Fuente BCN</td><td style="color:#e2e8f0">${item.bcn}</td></tr>
          <tr><td style="color:#94a3b8;font-size:10px">Verificadas municipal</td><td style="color:#e2e8f0">${item.municipal}</td></tr>
          ${topicLine}
        </table>
        ${topicsRows ? `<div style="margin-top:8px;border-top:1px solid #153b70;padding-top:6px"><table style="width:100%">${topicsRows}</table></div>` : ''}
      </div>`;
  }

  function renderMarkers(topicFilter) {
    allMarkers.forEach(m => mapaInstance.removeLayer(m));
    allMarkers = [];

    let countFiltered = 0;

    mapaData.forEach(item => {
      const color = getMarkerColor(item, topicFilter);
      const radius = getMarkerRadius(item, topicFilter);
      const circle = L.circleMarker([item.lat, item.lon], {
        radius,
        fillColor: color,
        color: '#0f172a',
        weight: 0.5,
        opacity: 0.9,
        fillOpacity: color === '#4b5563' ? 0.4 : 0.85,
      });
      circle.bindPopup(buildPopup(item, topicFilter), { maxWidth: 260 });
      circle.addTo(mapaInstance);
      allMarkers.push(circle);

      if (topicFilter !== 'ALL') {
        const count = getTopicCount(item, topicFilter);
        if (count > 0) countFiltered++;
      }
    });

    // Update stats
    const filtEl = document.getElementById('mapa-stat-filtrado');
    const labEl = document.getElementById('mapa-stat-label');
    if (filtEl && labEl) {
      if (topicFilter === 'ALL') {
        const totalConDatos = mapaData.filter(d => (d.total || 0) > 0).length;
        filtEl.textContent = totalConDatos.toString();
        labEl.textContent = 'Con ordenanzas';
      } else {
        filtEl.textContent = countFiltered;
        labEl.textContent = TOPIC_LABELS[topicFilter] || topicFilter;
      }
    }
  }

  function initMap() {
    if (mapaInstance) return; // ya inicializado

    const loading = document.getElementById('mapa-loading');

    // Dark tile layer compatible con el diseño
    mapaInstance = L.map('chile-map', {
      center: [-35.5, -71.0],
      zoom: 4,
      minZoom: 3,
      maxZoom: 12,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | CartoDB Dark',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(mapaInstance);

    function loadDataAndRender() {
      if (typeof MAPA_DATA !== 'undefined' && Array.isArray(MAPA_DATA) && MAPA_DATA.length > 0) {
        mapaData = MAPA_DATA;
        if (loading) loading.style.display = 'none';
        const filter = document.getElementById('mapa-topic-filter');
        renderMarkers(filter ? filter.value : 'ALL');
      } else {
        fetch('mapa_data.json')
          .then(r => r.json())
          .then(data => {
            mapaData = data;
            if (loading) loading.style.display = 'none';
            const filter = document.getElementById('mapa-topic-filter');
            renderMarkers(filter ? filter.value : 'ALL');
          })
          .catch(e => {
            console.error('Error loading mapa_data.json:', e);
            if (loading) loading.innerHTML = '<p style="color:#ef4444;font-size:12px">Error cargando datos del mapa.</p>';
          });
      }
    }

    loadDataAndRender();
  }

  window.initChileMap = function() {
    initMap();
    if (mapaInstance) {
      setTimeout(() => mapaInstance.invalidateSize(), 50);
    }
  };

  window.updateMapFilter = function () {
    const filter = document.getElementById('mapa-topic-filter');
    if (!filter || !mapaInstance) return;
    renderMarkers(filter.value);
  };

  // Hook into switchTab to init map when tab is activated
  const _origSwitchTab = window.switchTab;
  window.switchTab = function (tabId) {
    if (_origSwitchTab) _origSwitchTab(tabId);
    if (tabId === 'mapa') {
      setTimeout(() => {
        window.initChileMap();
      }, 100);
    }
  };
})();
