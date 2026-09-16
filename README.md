# Catastro y Pipeline de Ordenanzas Municipales de Chile

> **Work in progress / En evolución (2026-09-15).** Proyecto no terminado. Presencia territorial no acredita exhaustividad. [Estado y reentrada / Current status](docs/ESTADO-Y-REENTRADA-P090.md). Revisión local; despliegue público no verificado.

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://ordenanzas.evegat.cl)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://ordenanzas.evegat.cl)  
[ 🇪🇸 Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Herramienta de extracción, estructuración y catálogo nacional de **ordenanzas municipales de Chile**. La fuente estructurada principal es la **Biblioteca del Congreso Nacional (BCN/LeyChile)** y el corpus se complementa con documentos recuperados desde repositorios municipales oficiales y Transparencia Activa cuando existe evidencia reproducible con hash SHA-256.

> **Meta de cobertura:** exhaustiva, no muestral. El objetivo es identificar **todas las ordenanzas publicadas oficialmente por las 345 municipalidades de Chile**, que administran las 346 comunas del país, incluyendo su historia oficial disponible y sus actos modificatorios cuando corresponda.

---

## 🎯 Propósito del Proyecto & Enfoque Pedagógico

Las ordenanzas municipales constituyen la expresión jurídica primaria de la autonomía comunal y el marco regulatorio directo sobre la vida cotidiana en las 346 comunas de Chile (derechos municipales, medio ambiente, patentes, aseo y ornato, urbanismo y convivencia). Sin embargo, su acceso histórico ha estado profundamente fragmentado entre BCN/LeyChile, Transparencia Activa y repositorios documentales propios de cada municipio.

### Foco Docente y de Investigación del Mundo Local
Este proyecto nace con un objetivo fundamentalmente formativo y de investigación aplicada:
1. **Herramienta para estudiantes universitarios:** Proveer a estudiantes de Administración Pública, Ciencia Política, Derecho, Urbanismo y Políticas Públicas una base empírica estructurada para estudiar la gobernanza local y el ejercicio real de las facultades normativas de los municipios chilenos.
2. **Investigación empírica y comparada:** Facilitar la descarga de microdatos (CSV, SQLite, XLSX) para cruzar la densidad normativa municipal con variables sociodemográficas, presupuesto comunal (SINIM) y tipologías territoriales.
3. **Diagnóstico de transparencia local:** Visibilizar las brechas de publicidad activa y asimetrías de información entre municipios metropolitanos y comunas rurales o de menores recursos.
4. **Trazabilidad y rigor metodológico:** Enseñar estándares de recolección de datos públicos, distinguiendo corpus verificado, cobertura exhaustiva demostrada y referencias en cuarentena.

---

## 🗺️ Hoja de Ruta (Roadmap)

- [x] **Fase 1: Catastro Base & Pipeline Reproducible:** Extracción SPARQL BCN (1.710 normas), captura complementaria CPLT y categorización en 9 ejes temáticos.
- [x] **Fase 2: Visualizador Público & Acceso Abierto:** Dashboard interactivo publicado en GitHub Pages, filtros combinados por materia, región y año, drawer comunal, mapa interactivo con Leaflet, autocompletar inteligente y descargas abiertas.
- [ ] **Fase 3: Expansión Territorial Directa:** Pipeline de descubrimiento y extracción directa con verificación criptográfica (SHA-256), alcanzando el **100% de cobertura territorial (346 de 346 comunas)** con **7.287 ordenanzas oficiales consolidadas** (5.881 BCN/LeyChile + 1.406 municipales verificadas con SHA-256). Exhaustividad pendiente / Exhaustiveness unproven: `coverage_complete=false`.
- [ ] **Fase 4: Asistente RAG Jurídico-Municipal (costos por validar / costs to validate):** Indexación vectorial de texto completo (Embeddings BGE-M3 / e5-small) y conexión con modelos locales (inferencia por definir) y proveedor por evaluar para análisis comparado y redacción asistida.
- [x] **Fase 5: Módulo Docente & Guías Metodológicas:** Publicación de 3 casos de estudio interactivos en el visualizador y Jupyter Notebook oficial (`analisis_ordenanzas_chile_estudiantes.ipynb`) descargable para cátedras universitarias.

---

## 📁 Estructura del Repositorio

```text
catastro-ordenanzas-municipales/
├── .github/workflows/          # CI/CD: build snapshot & GitHub Pages deploy
├── data/                       # Registries y datasets oficiales consolidados
│   ├── maestro_comunas_chile.csv        # Catálogo territorial oficial (346 comunas)
│   ├── municipal_source_registry.json   # Registro y estrategia de fuentes oficiales
│   ├── municipal_verified_records.json  # 1.406 actos municipales promovidos con SHA-256
│   ├── cplt_municipal_directory.json    # Directorio de portales Transparencia CPLT
│   └── national_coverage_ledger.json    # Ledger nacional de cobertura territorial
├── dashboard/                  # Visualizador interactivo en GitHub Pages
│   ├── descargas/              # XLSX, CSV, ZIP, Notebook oficial para estudiantes
│   ├── index.html              # Frontend responsivo
│   ├── mapa_chile.js           # Visualizador de mapa interactivo (Leaflet.js)
│   └── status_data.json        # Snapshot JSON oficial con métricas en vivo
├── src/                        # Pipeline ETL reproducible y verificador de evidencia
│   ├── bcn_full_fetcher.py              # Extracción BCN/SPARQL
│   ├── cplt_transparencia_crawler.py    # Crawler y extractor CPLT
│   ├── exhaustive_municipal_recovery.py # Extractor municipal con contrato de evidencia
│   ├── build_public_snapshot.py         # Compilador maestro de snapshot y descargas
│   ├── build_accurate_map_data.py       # Georreferenciación comunal exacta
│   ├── export_excel_and_zip.py          # Exportador de paquetes abiertos
│   └── generate_docent_notebook.py      # Generador del Jupyter Notebook didáctico
├── LICENSE                     # Licencia MIT
├── README.md                   # Documentación en español
├── README.en.md                # English documentation
└── requirements.txt            # Dependencias reproducibles
```

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Bibliotecas:** `requests`, `pandas`, `openpyxl`, `beautifulsoup4`, `pypdf`
- **Protocolos & Datos:** SPARQL, HTTP, HTML, PDF, Open Data
- **Frontend / Dashboard:** HTML5, JavaScript moderno, Tailwind CSS, Leaflet.js
- **Control de evidencia:** descarga real, firma PDF (`%PDF-`), código HTTP 200, tamaño en bytes y hash SHA-256 inmutable.

---

## Uso local y reproducción

Para revisar el dashboard existente con Python:

```bash
python -m http.server 8000 --directory dashboard
```

Abrir http://localhost:8000. Sirve archivos existentes; no reconstruye datos. Los extractores dependen de módulos locales ausentes: consultar [pendientes y reentrada](docs/ESTADO-Y-REENTRADA-P090.md) antes de ejecutarlos.

`src/build_public_snapshot.py` sobrescribe JSON, JS, HTML y descargas del directorio recibido. Probar sobre una copia separada. La compilación no demuestra que los imports, las fuentes remotas ni el pipeline funcionen.

## 📊 Alcance, cobertura y estados de evidencia

Corte documental local del 2026-09-15, contado desde `dashboard/status_data.json` y contrastado con el CSV. Estas cifras requieren actualización cuando cambien los datos; no hay sincronización automática de este README. No se revalidaron documentos remotos ni todas las exportaciones.

- **Total normas consolidadas:** 7.287 registros normativos.
- **BCN / LeyChile:** 5.881 registros.
- **Fuentes Municipales Verificadas:** 1.406 registros oficiales con SHA-256.
- **Presencia territorial:** 346/346 comunas; 4 tienen un registro y 19 tienen entre 1 y 3. Exhaustividad pendiente.
- **Rango temporal observado:** 1980–2026.
- **Clasificación temática:** 9 materias normativas.

### 1. Corpus público verificado
Incluye:
- registros **BCN/LeyChile**;
- documentos municipales oficiales cuya descarga y metadatos han sido validados;
- SHA-256, tamaño y fecha de verificación para los documentos municipales promovidos.

### 2. Evidencia mínima de un documento municipal
1. Fuente/listado oficial identificable;
2. URL documental resoluble (`https://`);
3. Descarga real del recurso;
4. Contenido compatible con PDF (`%PDF-`);
5. Tamaño > 0 bytes;
6. Hash criptográfico SHA-256 inmutable;
7. Fecha de verificación registrada;
8. Relación jurídica con la ordenanza correctamente tipificada.

### 3. Cuarentena
Las referencias históricas CPLT/Transparencia Activa cuyo documento no puede demostrarse permanecen preservadas en auditoría, pero **no se publican como ordenanzas verificadas**.

---

## 🔬 Política metodológica: NO SAMPLING

Encontrar una norma, cinco normas o cincuenta normas de un municipio **no autoriza a declararlo cubierto exhaustivamente**. El objetivo final del proyecto es reconstruir el universo normativo oficial disponible en Chile mediante métodos auditables y reproducibles.

Chile tiene **346 comunas y 345 municipalidades** (la Municipalidad de Cabo de Hornos administra las comunas de Cabo de Hornos y Antártica).

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.

