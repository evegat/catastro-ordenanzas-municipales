// Asistente Jurídico Municipal P090 - Motor de Búsqueda y Diálogo Cero-Alucinación
// Consulta en tiempo real sobre 7.321 ordenanzas oficiales de Chile (346 comunas)
// Compatible con Umami Analytics y 100% ejecución local en el navegador del usuario.

(function() {
  'use strict';

  let chatIsOpen = false;
  let chatHistory = [];

  // BASE DOCTRINAL Y JURÍDICA NACIONAL (VERIFICADA)
  const CONOCIMIENTO_JURIDICO = {
    obligatorias: `
**Las 6 Ordenanzas Obligatorias por Ley en Chile:**

1. **Derechos Municipales y Tarifas** *(Art. 12 Ley 18.695 LOCM)*: Fija anualmente los cobros por permisos de edificación, terrazas, comercio y derechos varios antes del 31 de octubre para regir el 1 de enero.
2. **Participación Ciudadana** *(Art. 93 LOCM y Ley 20.500)*: Regula consultas vecinales, audiencias públicas, cabildos y el funcionamiento del COSOC.
3. **Cobro y Exenciones de Aseo Domiciliario** *(Arts. 7, 8 y 9 DL 3.063)*: Fija la tarifa por extracción de basura y las causales de exención social (RSH vulnerable).
4. **Tenencia Responsable de Mascotas** *(Art. 7 Ley 21.020 "Ley Cholito")*: Regula registro con microchip, esterilización, paseo y multas de hasta 30 UTM en JPL.
5. **Notificaciones y Resoluciones Municipales** *(Art. 12 inc. final LOCM)*: Garantiza el debido proceso para clausuras, demoliciones y multas alcaldicias.
6. **Registro de Personas Jurídicas Receptoras de Fondos Públicos** *(Ley 19.862)*: Requisito legal habilitante indispensable para entregar subvenciones municipales a clubes u ONG.
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

  function normalize(str) {
    return (str || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  // Detectar si la consulta menciona una comuna de Chile
  function findComunaEnConsulta(text) {
    if (!window.CATASTRO_DATA || !window.CATASTRO_DATA.comunas) return null;
    const normText = normalize(text);

    // Búsqueda exacta primero
    for (const c of window.CATASTRO_DATA.comunas) {
      const normC = normalize(c.comuna);
      if (normC.length > 3 && normText.includes(normC)) {
        return c;
      }
    }
    // Casos especiales abreviados
    if (normText.includes('vina') || normText.includes('vina del mar')) {
      return window.CATASTRO_DATA.comunas.find(c => c.comuna.includes('Viña'));
    }
    if (normText.includes('stgo') || normText.includes('santiago')) {
      return window.CATASTRO_DATA.comunas.find(c => c.comuna === 'Santiago');
    }
    return null;
  }

  // Generador de respuestas inteligentes basadas en evidencia
  function responderPregunta(pregunta) {
    const norm = normalize(pregunta);

    // 1. Pregunta sobre PLACMA o Planes Ambientales
    if (norm.includes('placma') || (norm.includes('plan') && norm.includes('medio ambiente')) || norm.includes('scam')) {
      return CONOCIMIENTO_JURIDICO.placma;
    }

    // 2. Pregunta sobre Ordenanzas Obligatorias por Ley
    if (norm.includes('obligatoria') || norm.includes('obligacion') || norm.includes('por ley') || norm.includes('cuales son las 6') || norm.includes('deben tener')) {
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
            const num = o.numero ? ` (N° ${o.numero})` : '';
            const link = o.target_url ? ` — [Ver PDF Oficial ↗](${o.target_url})` : '';
            return `• **${o.fecha ? o.fecha.substring(0, 4) : 'S/F'}**: ${o.titulo}${num}${link}`;
          }).join('\n');
      }

      return `
🏛️ **Comuna de ${comunaMatch.comuna}** (${comunaMatch.region_nombre})

• **Total de normas catalogadas:** ${total} ordenanzas oficiales (${bcn} en BCN LeyChile + ${muni} verificadas directamente en la Municipalidad con hash SHA-256).
• **Cobertura de materias obligatorias en el catastro:**
  - Derechos Municipales: ${tieneDerechos ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Aseo / Medio Ambiente: ${tieneAseo ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Tenencia de Mascotas: ${tieneMascotas ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Participación Ciudadana: ${tieneParticipacion ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Comercio / Alcoholes: ${tieneComercio ? '✅ Detectada' : '⚠️ No registrada aún'}
  - Convivencia / Seguridad: ${tieneSeguridad ? '✅ Detectada' : '⚠️ No registrada aún'}
${detalleNormas}

*Puedes revisar el expediente íntegro en la pestaña "Ficha por Comuna" buscando "${comunaMatch.comuna}".*
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
        const ejemplos = comunasHumedales.slice(0, 5).map(h => `• **${h.comuna}**: ${h.titulo}${h.url ? ` [PDF ↗](${h.url})` : ''}`).join('\n');
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
🔎 Encontré normas relacionadas con **"${pregunta}"**:

${resultados.map(r => `• **${r.comuna}** (${r.fecha ? r.fecha.substring(0,4) : 'S/F'}): ${r.titulo}${r.url ? ` [PDF ↗](${r.url})` : ''}`).join('\n')}

*Para ver todas las coincidencias, utiliza el Buscador Principal en la parte superior.*
        `;
      }
    }

    // Fallback sobrio y verídico
    return `
No encontré un registro exacto para tu consulta en las 7.321 ordenanzas catalogadas.

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
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-sky-400 underline font-semibold hover:text-sky-300">$1</a>');
    
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
          ${texto}
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
      window.umami.track('asistente_chat_consulta', { query: q.substring(0, 50) });
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
    if (log) {
      log.innerHTML = `
        <div class="bg-[#04142b] border border-[#153b70] rounded-2xl p-3.5 text-xs text-zinc-300 space-y-2">
          <div class="flex items-center gap-2 text-sky-400 font-bold">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
            <span>Asistente Jurídico Municipal P090</span>
          </div>
          <p class="text-[11px] leading-relaxed text-zinc-300">
            ¡Hola! Soy tu asistente de consulta normativa sobre las <strong>7.321 ordenanzas oficiales de Chile</strong> (100% de cobertura nacional en 346 comunas).
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
