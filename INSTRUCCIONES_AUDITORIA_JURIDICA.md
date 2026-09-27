# Directiva de Auditoría Técnica y Jurídica — P090 / ordenanzas.evegat.cl

**Fecha:** 2026-09-25  
**Fuente:** Correos de auditoría de Eduardo Vega Toledo (`1a0d5ee0a9022061` y `1a0d5ecf1de72661`)  
**Prioridad:** P0 (Resolver antes de difusión masiva)  
**Archivos objetivo:** `dashboard/index.html`, `README.md`, `README.en.md`

---

## 1. Tareas P0 Inmediatas

### A. Eliminar expresión "Repositorio Oficial" / "Catastro Oficial"
- **Motivo:** El sitio es una iniciativa independiente sobre fuentes oficiales y documentos verificables. No es una plataforma oficial del Estado, SUBDERE o municipalidad alguna.
- **Cambio en `dashboard/index.html`:**
  - `<title>`: Cambiar a `Catastro Nacional de Ordenanzas Municipales de Chile | Iniciativa Independiente`
  - Encabezados: Reemplazar cualquier uso de "Repositorio Oficial" por:
    - *"Catastro Nacional de Ordenanzas Municipales de Chile"*
    - Bajada: *"Iniciativa independiente construida a partir de fuentes oficiales y documentos municipales verificables."*

### B. Corregir Sección "Las 6 Ordenanzas Obligatorias"
- **Renombrar encabezado:** *"Ordenanzas y regulaciones comunales con mandato o fundamento legal específico"*.
- **Punto 5 (Notificaciones):**
  - El Art. 12 inc. final de la LOCM **NO mandata dictar una ordenanza de notificaciones** (eso opera por Ley N° 19.880 y Ley N° 18.287).
  - Eliminar esta tarjeta de obligatorias o sustituirla por la **Ordenanza Local del Plan Regulador Comunal** (mandatada por la Ley General de Urbanismo y Construcciones / OGUC).
- **Punto 6 (Subvenciones Municipales):**
  - La Ley N° 19.862 exige llevar un registro, no una ordenanza. El instrumento formal municipal es la **"Ordenanza sobre Otorgamiento de Subvenciones Municipales"** (Art. 5° letra g y Art. 65 letra g de la Ley N° 18.695).
  - Renombrar y fundamentar conforme a los artículos 5 y 65 de la LOCM.
- **Mantener confirmadas:**
  - *Derechos Municipales y Tarifas:* Art. 42 DL 3.063 y Art. 12 LOCM.
  - *Participación Ciudadana:* Art. 93 LOCM / Ley N° 20.500.
  - *Tarifas y Exenciones de Aseo:* Arts. 7, 8 y 9 DL 3.063.
  - *Tenencia Responsable de Mascotas:* Art. 7 Ley N° 21.020.

### C. Corrección Errata de Autoría
- En `dashboard/index.html` línea 17 (`<meta name="author">`), OpenGraph y footer:
  - Cambiar `Eduardo Vega Toro` por **`Eduardo Vega Toledo`**.

### D. Disclaimer de Vigencia en Modal Comunal
- En el modal donde se despliegan los textos de ordenanzas, agregar el micro-copy:
  > *"Texto sistematizado con fines analíticos y de referencia. Para efectos jurídicos o litigiosos, verificar eventuales modificaciones o derogaciones no publicadas en la Secretaría Municipal respectiva."*

### E. Optimización de Render
- Virtualizar o paginar la tabla nacional a 50 registros por página para conexiones municipales lentas.
- Reforzar el badge visual que distingue norma BCN LeyChile de norma respaldada directamente desde portal municipal con hash SHA-256.

---

## 2. Validación y Despliegue
Al completar los cambios:
1. `python -m compileall -q src`
2. Validar sintaxis HTML/JS de `dashboard/index.html`.
3. Ejecutar gates del arnés MyWorld: `.myworld-harness/harness.ps1 preflight` y `quality`.
4. Git commit y push a `main`.
5. Re-desplegar en Coolify VPS Hostinger o GitHub Pages.
