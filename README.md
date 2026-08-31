# Catastro y Pipeline de Ordenanzas Municipales de Chile

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
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
- [x] **Fase 3: Expansión Territorial Directa:** Pipeline de descubrimiento y extracción directa con verificación criptográfica (SHA-256), alcanzando el **100% de cobertura territorial (346 de 346 comunas)** con **3.015 ordenanzas oficiales consolidadas**.
- [ ] **Fase 4: Asistente RAG Jurídico-Municipal ($0 API Cost):** Indexación vectorial de texto completo (Embeddings BGE-M3 / e5-small) y conexión con modelos locales (Ollama RTX 4080) y OpenRouter Free Tier para análisis comparado y redacción asistida.
- [x] **Fase 5: Módulo Docente & Guías Metodológicas:** Publicación de 3 casos de estudio interactivos en el visualizador y Jupyter Notebook oficial (`analisis_ordenanzas_chile_estudiantes.ipynb`) descargable para cátedras universitarias.

---

## 📁 Estructura del Repositorio

```text
catastro-ordenanzas-municipales/
├── .github/workflows/          # CI/CD: build snapshot & GitHub Pages deploy
├── data/                       # Registries y datasets oficiales consolidados
│   ├── maestro_comunas_chile.csv        # Catálogo territorial oficial (346 comunas)
│   ├── municipal_source_registry.json   # Registro y estrategia de fuentes oficiales
│   ├── municipal_verified_records.json  # 1.305 actos municipales promovidos con SHA-256
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

## 🚀 Uso y Reproducción

### 1. Requisitos e instalación
```bash
git clone https://github.com/evegat/catastro-ordenanzas-municipales.git
cd catastro-ordenanzas-municipales

python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Extracción BCN y procesamiento
```bash
python src/bcn_full_fetcher.py
python src/export_excel_and_zip.py
```

### 3. Extracción municipal con verificación SHA-256
```bash
python src/exhaustive_municipal_recovery.py \
  --registry data/municipal_source_registry.json \
  --out data/municipal_exhaustive_coverage.json
```

### 4. Construir snapshot público verified-only
```bash
python src/build_public_snapshot.py dashboard
```

Este paso consolida los 3.015 registros oficiales, valida la integridad de cada URL y hash SHA-256, regenera los archivos `catastro_ordenanzas_nacional_2026.csv`, `.xlsx`, `.zip` y prepara los metadatos para GitHub Pages.

---

## 📊 Alcance, cobertura y estados de evidencia

Los conteos públicos **no se mantienen manualmente en este README**. Se recalculan en cada build desde las filas efectivamente publicables y quedan expuestos en `dashboard/status_data.json`, en el dashboard y en el manifiesto de descargas.

- **Total normas consolidadas:** 7.186 registros normativos.
- **BCN / LeyChile:** 5.881 registros.
- **Fuentes Municipales Verificadas:** 1.305 registros oficiales con SHA-256.
- **Cobertura comunal:** 346 de 346 comunas (100.0% de presencia territorial observada; solo 5 comunas con 1 sola norma, 98.6% con acervo normativo denso).
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

