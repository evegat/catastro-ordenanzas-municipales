// Ejecuta el módulo real con un adaptador Leaflet mínimo, sin red ni navegador.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'dashboard/mapa_data.json')));
const markers = [];
const filter = { value: 'ALL' };
const elements = { 'mapa-topic-filter': filter, 'mapa-loading': { style: {} },
  'mapa-stat-filtrado': {}, 'mapa-stat-label': {} };
const map = { removeLayer(marker) { markers.splice(markers.indexOf(marker), 1); },
  invalidateSize() {} };
const context = {
  MAPA_DATA: data,
  window: {},
  document: { getElementById(id) { return elements[id]; } },
  setTimeout(fn) { fn(); },
  L: {
    map() { return map; },
    tileLayer() { return { addTo() {} }; },
    circleMarker(coords, options) {
      return { coords, options, bindPopup(html) { this.html = html; },
        addTo() { markers.push(this); } };
    },
  },
};
vm.runInNewContext(fs.readFileSync(path.join(root, 'dashboard/mapa_chile.js'), 'utf8'), context);
context.window.initChileMap();
assert.equal(markers.length, data.length);
assert.ok(markers.every(marker => !marker.html.includes('undefined')));
// Un alias sin etiqueta directa provocaba ReferenceError y dejaba el mapa vacío.
const arica = markers.find(marker => marker.html.includes('>Arica</div>'));
assert.ok(arica.html.includes('Normativa General y Otras Materias'));
assert.ok(!arica.html.includes('>normativa_general<'));
filter.value = 'tenencia_mascotas';
context.window.updateMapFilter();
const expected = data.filter(row => ['tenencia_mascotas', 'mascotas_animales', 'mascotas']
  .reduce((sum, key) => sum + (row.topics[key] || 0), 0) > 0).length;
assert.equal(markers.length, data.length);
assert.equal(markers.filter(marker => marker.options.fillColor === '#54b995').length, expected);
assert.equal(Number(elements['mapa-stat-filtrado'].textContent), expected);
console.log(`PASS: ${markers.length} marcadores; ${expected} comunas con mascotas; alias resueltos.`);
