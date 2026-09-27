const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const messages = [];
const events = [];
const input = { value: '' };
const log = { appendChild(message) { messages.push(message.innerHTML); } };
const payload = '<img src=x onerror=alert(1)>';
const context = {
  URL,
  setTimeout(fn) { fn(); },
  document: {
    getElementById(id) { return id === 'chat-input-text' ? input : log; },
    createElement() { return {}; },
  },
  window: {
    CATASTRO_DATA: { comunas: [{ comuna: "O'Higgins", region_nombre: 'Aysén',
      total_count: 1, bcn_count: 1, municipal_count: 0,
      ordenanzas: [{ titulo: payload, target_url: 'javascript:alert(1)', fecha: '2026-01-01' }] }] },
    umami: { track(...args) { events.push(args); } },
  },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../dashboard/asistente_chat.js'), 'utf8'), context);
context.window.enviarConsultaChat(payload);
assert.equal(messages.length, 2);
assert.ok(messages.every(message => !message.includes('<img')));
assert.ok(messages[0].includes('&lt;img'));
assert.ok(messages[1].includes('&lt;img'));
assert.ok(!messages[1].includes('href="javascript:'));
assert.equal(events[0].length, 1, 'No transmitir consultas ni propiedades de la consulta a analítica');
context.window.enviarConsultaChat("Ordenanzas de O'Higgins");
assert.ok(messages[3].includes('showComunaModal(&quot;O&#39;Higgins&quot;)'));
assert.ok(!messages[3].includes('<img'));
console.log('PASS: texto literal, enlaces seguros, comuna con apóstrofo y analítica sin consultas.');
