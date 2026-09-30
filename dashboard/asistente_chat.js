// Asistente Jurídico Municipal P090 - Motor de Búsqueda y Consulta Normativa Trazable
// Consulta en tiempo real sobre el corpus canónico de ordenanzas oficiales de Chile (346 comunas)
// Compatible con Umami Analytics y 100% ejecución local en el navegador del usuario.

(function() {
  'use strict';

  let chatIsOpen = false;
  let chatHistory = [];

  // BASE DOCTRINAL Y JURÍDICA NACIONAL (VERIFICADA)
  const CONOCIMIENTO_JURIDICO = {
    obligatorias: `
**Ordenanzas y regulaciones comunales con mandato o fundamento legal específico:**

1. **Derechos Municipales y Tarifas** *(Art. 42 DL 3.063 y Art. 12 Ley N° 18.695 LOCM)*: Fija anualmente los cobros por permisos de edificación, ocupación de bienes nacionales de uso público, patentes y servicios municipales.
2. **Participación Ciudadana** *(Art. 93 Ley N° 18.695 y Ley N° 20.500)*: Mandato expreso para regular consultas vecinales, audiencias públicas, cabildos comunales y el funcionamiento del COSOC.
3. **Cobro y Exenciones de Aseo Domiciliario** *(Arts. 7, 8 y 9 DL N° 3.063)*: Periodicidad al menos trienal. Fija la tarifa por extracción de residuos y las causales de exención social según Registro Social de Hogares (RSH).
4. **Tenencia Responsable de Mascotas** *(Art. 7 Ley N° 21.020 "Ley Cholito" y D.S. N° 1.007 Interior)*: Mandato legal expreso que regula registro con microchip, esterilización, paseo y multas de hasta 30 UTM en JPL.
5. **Plan Regulador Comunal (Ordenanza Local)** *(Arts. 41 a 43 LGUC DFL 458 Minvu y OGUC)*: Instrumento normativo que fija zonificación, usos de suelo y condiciones de edificación comunal.
6. **Otorgamiento de Subvenciones Municipales** *(Art. 5° letra g y Art. 65 letra g Ley N° 18.695 LOCM)*: Regula criterios de asignación y rendición de cuentas, operando la inscripción en el registro de la Ley N° 19.862 como condición habilitante para la transferencia de fondos públicos.
    `,
    placma: `
**¿El Plan Comunal de Medio Ambiente (PLACMA) es una ordenanza?**

**No.** Son instrumentos jurídicamente distintos:

• **El PLACMA:** Es un *instrumento de planificación estratégica territorial* impulsado por el municipio en el marco del SCAM (Ministerio del Medio Ambiente). Fija diagnósticos, metas de reciclaje y líneas de acción comunitaria. **No tiene fuerza punitiva ni sancionatoria contra terceros**.
• **La Ordenanza Ambiental Comunal:** Es un *acto normativo de potestad reglamentaria externa* (Art. 12 LOCM), aprobado por el Concejo y dictado por Decreto Alcaldicio. **Es obligatoria para todos los habitantes y faculta al Juzgado de Policía Local (JPL) para cursar multas de hasta 5 UTM**.

*Conclusión práctica:* Un municipio puede tener certificación ambiental de excelencia, pero si sorprende a alguien botando escombros o talando un árbol protegido, **no puede multarlo citando el PLACMA**; requiere obligatoriamente una **Ordenanza de Medio Ambiente**.
    `,
    multas_jpl: `
**Régimen de Sanciones y Multas en Ordenanzas Municipales:**
• Conforme al **Art. 12 de la Ley N° 18.695 (LOCM)**, las ordenanzas municipales pueden fijar multas por infracción que no excedan de **5 UTM** (Unidades Tributarias Mensuales), las que son aplicadas privativamente por el **Juzgado de Policía Local (JPL)** competente.
• *Excepción sectorial:* La **Ley N° 21.020 (Ley Cholito)** faculta a las ordenanzas comunales para sancionar infracciones graves a la tenencia responsable con multas de **hasta 30 UTM**.
    `
  };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[char]);
  }

  function normalize(str) {
    return (str || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Detectar si la consulta menciona una comuna de Chile (resolución desambiguada por especificidad)
  function findComunaEnConsulta(text) {
    if (!window.CATASTRO_DATA || !window.CATASTRO_DATA.comunas) return null;
    const normText = normalize(text);

    // Casos especiales abreviados primero si son exactos
    if (/\b(?:vina del mar|vina)\b/i.test(normText)) {
      const vina = window.CATASTRO_DATA.comunas.find(c => normalize(c.comuna) === 'vina del mar');
      if (vina) return vina;
    }
    if (/\b(?:stgo|santiago)\b/i.test(normText)) {
      const stgo = window.CATASTRO_DATA.comunas.find(c => normalize(c.comuna) === 'santiago');
      if (stgo) return stgo;
    }

    // Ordenar comunas por longitud descendente para que 'Talcahuano' se evalúe antes que 'Talca',
    // 'Calera de Tango' antes que 'Calera', y 'San Pedro de la Paz' antes que 'San Pedro'.
    const comunasOrdenadas = [...window.CATASTRO_DATA.comunas].sort((a, b) => {
      return normalize(b.comuna).length - normalize(a.comuna).length;
    });

    for (const c of comunasOrdenadas) {
      const normC = normalize(c.comuna);
      if (normC.length < 3) continue;
      const regex = new RegExp(`(?:^|[^a-z0-9])${escapeRegex(normC)}(?:$|[^a-z0-9])`, 'i');
      if (regex.test(normText)) {
        return c;
      }
    }
    return null;
  }

  // Generador de respuestas inteligentes basadas en evidencia
  function responderPregunta(pregunta) {
    if (!window.CATASTRO_DATA || !window.CATASTRO_DATA.comunas) {
      return '⚠️ **Catálogo no disponible:** La base de datos normativos aún se está sincronizando o no se encuentra disponible en memoria. Por favor recarga la página o inténtalo en unos segundos.';
    }

    const norm = normalize(pregunta);

    // 1. Pregunta sobre PLACMA o Planes Ambientales
    if (norm.includes('placma') || (norm.includes('plan') && norm.includes('medio ambiente')) || norm.includes('scam')) {
      return CONOCIMIENTO_JURIDICO.placma;
    }

    // 2. Pregunta sobre Ordenanzas Obligatorias por Ley / Mandato Legal
    if (norm.includes('obligatoria') || norm.includes('obligacion') || norm.includes('por ley') || norm.includes('cuales son las 6') || norm.includes('deben tener') || norm.includes('mandato legal') || norm.includes('mandato') || norm.includes('marco legal') || norm.includes('exigid')) {
      return CONOCIMIENTO_JURIDICO.obligatorias;
    }

    // 3. Pregunta sobre Multas o Juzgado de Policía Local
    if (norm.includes('multa') || norm.includes('jpl') || norm.includes('juzgado') || norm.includes('sancion') || norm.includes('utm')) {
      return CONOCIMIENTO_JURIDICO.multas_jpl;
    }

    // 4. Pregunta focalizada en una comuna específica
    const comunaMatch = findComunaEnConsulta(pregunta);
    if (comunaMatch) {
      const total = comunaMatch.total_count || 0;
      const bcn = comunaMatch.bcn_count || 0;
      const muni = comunaMatch.municipal_count || 0;
      const ordenanzas = comunaMatch.ordenanzas || [];

      // Evaluar las 6 materias obligatorias en esta comuna
      const matSet = new Set(ordenanzas.map(o => o.materia_id || ''));
      const tieneDerechos = matSet.has('derechos_tarifas');
      const tieneAseo = matSet.has('aseo_medioambiente') || matSet.has('aseo_residuos') || matSet.has('medio_ambiente');
      const tieneMascotas = matSet.has('tenencia_mascotas') || matSet.has('mascotas_animales') || matSet.has('mascotas');
      const tieneParticipacion = matSet.has('participacion_ciudadana');
      const tieneComercio = matSet.has('comercio_alcoholes') || matSet.has('comercio_patentes') || matSet.has('alcoholes_comercio');
      const tieneSeguridad = matSet.has('seguridad_convivencia') || matSet.has('convivencia_seguridad');

      let detalleNormas = '';
      if (ordenanzas.length > 0) {
        detalleNormas = '\n\n**Últimas ordenanzas registradas con enlace oficial:**\n' +
          ordenanzas.slice(0, 4).map(o => {
            const num = o.numero ? ` (N° ${escapeHtml(o.numero)})` : '';
            const link = o.target_url ? ` — [Consultar fuente ↗](${o.target_url})` : '';
            return `• **${o.fecha ? o.fecha.substring(0, 4) : 'S/F'}**: ${escapeHtml(o.titulo)}${num}${link}`;
          }).join('\n');
      }

      return `
🏛️ **Comuna de ${escapeHtml(comunaMatch.comuna)}** (${escapeHtml(comunaMatch.region_nombre)})

• **Total de normas catalogadas:** ${total} registros normativos (${bcn} en BCN LeyChile + ${muni} verificadas directamente en la Municipalidad con hash SHA-256).
• **Cobertura de materias con fundamento legal en el catastro:**
  - Derechos Municipales: ${tieneDerechos ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Aseo / Medio Ambiente: ${tieneAseo ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Tenencia de Mascotas: ${tieneMascotas ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Participación Ciudadana: ${tieneParticipacion ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Comercio / Alcoholes: ${tieneComercio ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Convivencia / Seguridad: ${tieneSeguridad ? '✅ Detectada' : '⚠️ No registrada aún'}
${detalleNormas}

<div class="pt-2">
  <button onclick="window.showComunaModal(${escapeHtml(JSON.stringify(comunaMatch.comuna))})" class="w-full px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-sm">
    <span>Abrir Expediente de ${escapeHtml(comunaMatch.comuna)}</span>
    <span>↗</span>
  </button>
</div>
      `;
    }

    // 5. Pregunta sobre humedales
    if (norm.includes('humedal') || norm.includes('humedales')) {
      const comunasHumedales = [];
      if (window.CATASTRO_DATA && window.CATASTRO_DATA.comunas) {
        window.CATASTRO_DATA.comunas.forEach(c => {
          (c.ordenanzas || []).forEach(o => {
            if (normalize(o.titulo).includes('humedal')) {
              comunasHumedales.push({ comuna: c.comuna, titulo: o.titulo, url: o.target_url });
            }
          });
        });
      }
      if (comunasHumedales.length > 0) {
        const ejemplos = comunasHumedales.slice(0, 5).map(h => `• **${escapeHtml(h.comuna)}**: ${escapeHtml(h.titulo)}${h.url ? ` [Fuente ↗](${h.url})` : ''}`).join('\n');
        return `
🌿 **Ordenanzas de Protección de Humedales Urbanos en Chile:**

Hemos identificado **${comunasHumedales.length} ordenanzas específicas** sobre humedales en el catastro nacional.

**Ejemplos destacados:**
${ejemplos}

*Puedes escribir "humedal" en el buscador central para explorar todos los decretos comunales.*
        `;
      }
    }

    // 6. Pregunta sobre Ruidos Molestos o Seguridad
    if (norm.includes('ruido') || norm.includes('ruidos') || norm.includes('seguridad')) {
      return `
🔊 **Regulación de Ruidos Molestos y Convivencia Vecinal:**

El catastro consolida más de **120 normas** en la materia *Seguridad y Convivencia*. Las ordenanzas de ruidos fijan decibeles máximos por zonificación (residencial vs comercial), horarios permitidos y multas de hasta 5 UTM tramitadas en el Juzgado de Policía Local.

*Escribe el nombre de tu comuna (ej. "Ruidos en Providencia" o "Ruidos en Concepción") para ver la ordenanza específica.*
      `;
    }

    // 7. Pregunta general / Búsqueda por palabras clave
    if (window.CATASTRO_DATA && window.CATASTRO_DATA.comunas) {
      const resultados = [];
      for (const c of window.CATASTRO_DATA.comunas) {
        for (const o of (c.ordenanzas || [])) {
          if (normalize(o.titulo).includes(norm)) {
            resultados.push({ comuna: c.comuna, titulo: o.titulo, fecha: o.fecha, url: o.target_url });
            if (resultados.length >= 4) break;
          }
        }
        if (resultados.length >= 4) break;
      }

      if (resultados.length > 0) {
        return `
🔎 Encontré normas relacionadas con **"${escapeHtml(pregunta)}"**:

${resultados.map(r => `• **${escapeHtml(r.comuna)}** (${r.fecha ? r.fecha.substring(0,4) : 'S/F'}): ${escapeHtml(r.titulo)}${r.url ? ` [Fuente ↗](${r.url})` : ''}`).join('\n')}

*Para ver todas las coincidencias, utiliza el Buscador Principal en la parte superior.*
        `;
      }
    }

    // Fallback sobrio y verídico
    const totalCanonic = (window.CATASTRO_DATA && window.CATASTRO_DATA.metrics && window.CATASTRO_DATA.metrics.total_ordenanzas) || 7462;
    return `
No encontré un registro exacto para tu consulta en las ${totalCanonic.toLocaleString('es-CL')} ordenanzas catalogadas.

Puedes:
1. Preguntar por una **comuna específica** (ej: "¿Qué ordenanzas tiene Arica?").
2. Consultar por una materia (ej: "humedales", "ruidos", "derechos").
3. Preguntar por temas legales (ej: "¿Cuáles son las 6 ordenanzas obligatorias?", "¿El PLACMA es una ordenanza?").
4. Si buscas un documento que no figura, puedes informarlo en el **Buzón Colaborativo** para su rescate oficial.
    `;
  }

  // Renderizar markdown simple en el chat
  function formatMarkdown(text) {
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/• /g, '• ')
      .replace(/\[(.*?)\]\((.*?)\)/g, (_, label, url) => {
        try {
          const parsed = new URL(url);
          if (!['https:', 'http:'].includes(parsed.protocol)) return label;
          return `<a href="${escapeHtml(parsed.href)}" target="_blank" rel="noopener noreferrer" class="text-sky-400 underline font-semibold hover:text-sky-300">${label}</a>`;
        } catch { return label; }
      });
    
    // Convertir saltos de línea
    html = html.replace(/\n\n/g, '</p><p class="mt-2">').replace(/\n/g, '<br/>');
    return `<p>${html}</p>`;
  }

  function agregarMensaje(remitente, texto) {
    const log = document.getElementById('chat-messages-log');
    if (!log) return;

    const msgDiv = document.createElement('div');
    if (remitente === 'usuario') {
      msgDiv.className = 'flex justify-end';
      msgDiv.innerHTML = `
        <div class="bg-sky-600 text-white rounded-2xl rounded-tr-none px-3.5 py-2 text-xs max-w-[85%] shadow-md">
          ${escapeHtml(texto)}
        </div>
      `;
    } else {
      msgDiv.className = 'flex justify-start';
      msgDiv.innerHTML = `
        <div class="bg-[#04142b] text-zinc-200 border border-[#153b70] rounded-2xl rounded-tl-none p-3 text-xs max-w-[92%] shadow-md leading-relaxed space-y-1">
          ${formatMarkdown(texto)}
        </div>
      `;
    }
    log.appendChild(msgDiv);
    log.scrollTop = log.scrollHeight;
  }

  window.enviarConsultaChat = function(preguntaTexto) {
    const input = document.getElementById('chat-input-text');
    const q = (preguntaTexto || (input ? input.value : '')).trim();
    if (!q) return;

    if (input && !preguntaTexto) input.value = '';

    agregarMensaje('usuario', q);

    if (window.umami) {
      window.umami.track('asistente_chat_consulta');
    }

    // Simular procesamiento rápido y responder
    setTimeout(() => {
      const resp = responderPregunta(q);
      agregarMensaje('asistente', resp);
    }, 120);
  };

  window.toggleChatModal = function() {
    chatIsOpen = !chatIsOpen;
    const windowEl = document.getElementById('chat-window-panel');
    const badgeEl = document.getElementById('chat-toggle-badge');
    if (windowEl) {
      if (chatIsOpen) {
        windowEl.classList.remove('hidden');
        if (badgeEl) badgeEl.classList.add('hidden');
        const input = document.getElementById('chat-input-text');
        if (input) setTimeout(() => input.focus(), 100);
        if (window.umami) window.umami.track('asistente_chat_abrir');
      } else {
        windowEl.classList.add('hidden');
      }
    }
    lucide.createIcons();
  };

  window.limpiarChat = function() {
    const log = document.getElementById('chat-messages-log');
    const totalCanonic = (window.CATASTRO_DATA && window.CATASTRO_DATA.metrics && window.CATASTRO_DATA.metrics.total_ordenanzas) || 7462;
    if (log) {
      log.innerHTML = `
        <div class="bg-[#04142b] border border-[#153b70] rounded-2xl p-3.5 text-xs text-zinc-300 space-y-2">
          <div class="flex items-center gap-2 text-sky-400 font-bold">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
            <span>Asistente Jurídico Municipal P090</span>
          </div>
          <p class="text-[11px] leading-relaxed text-zinc-300">
            ¡Hola! Soy tu asistente de consulta normativa sobre las <strong>${totalCanonic.toLocaleString('es-CL')} ordenanzas oficiales de Chile</strong> (registros en 346 comunas; exhaustividad no acreditada; la presencia de materias registradas no certifica vigencia ni cumplimiento legal formal).
          </p>
          <p class="text-[11px] text-zinc-400">
            Pregúntame por las ordenanzas obligatorias por ley, la validez del PLACMA, o escribe el nombre de cualquier comuna del país.
          </p>
          <div class="pt-1 flex flex-wrap gap-1.5">
            <button onclick="enviarConsultaChat('¿Cuáles son las 6 ordenanzas obligatorias?')" class="px-2 py-1 rounded bg-[#071f43] hover:bg-sky-600 border border-[#153b70] text-[10px] text-sky-300 hover:text-white transition-colors">⚖️ 6 Ordenanzas Obligatorias</button>
            <button onclick="enviarConsultaChat('¿El PLACMA es una ordenanza?')" class="px-2 py-1 rounded bg-[#071f43] hover:bg-sky-600 border border-[#153b70] text-[10px] text-sky-300 hover:text-white transition-colors">🌳 ¿PLACMA es ordenanza?</button>
            <button onclick="enviarConsultaChat('Ordenanzas de Maipú')" class="px-2 py-1 rounded bg-[#071f43] hover:bg-sky-600 border border-[#153b70] text-[10px] text-sky-300 hover:text-white transition-colors">🏛️ Ordenanzas de Maipú</button>
            <button onclick="enviarConsultaChat('¿Qué comunas tienen ordenanza de humedales?')" class="px-2 py-1 rounded bg-[#071f43] hover:bg-sky-600 border border-[#153b70] text-[10px] text-sky-300 hover:text-white transition-colors">🌿 Humedales Urbanos</button>
          </div>
        </div>
      `;
      lucide.createIcons();
    }
  };

})();
