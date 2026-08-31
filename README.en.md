# Chilean Municipal By-Laws (Ordenanzas) Open Data Pipeline

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Open Data](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Launch Interactive Dashboard Online** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Versión en Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Automated ETL pipeline, structured dataset, and exploratory visualizer for **Chilean Municipal By-Laws (*Ordenanzas Municipales*)**, querying open data from the **Library of the National Congress of Chile (BCN/LeyChile)** SPARQL endpoint and complementary verified municipal official sources with SHA-256 cryptographic hashes.

> **Coverage goal:** exhaustive, not sample-based. The objective is to identify **all by-laws officially published by Chile's 345 municipalities**, governing the country's 346 communes.

---

## 🎯 Purpose & Educational Focus

Municipal ordinances are the primary legal mechanism through which Chilean local governments exercise regulatory autonomy across everyday life (local fees, environmental sanitation, municipal permits, urban planning, and coexistence) in all 346 municipalities.

### Research and Teaching Tool for Local Governance
This project is built primarily as an educational and empirical research resource:
1. **Undergraduate & Graduate Tool:** Enables students of Public Administration, Political Science, Law, Urban Studies, and Public Policy to explore how local governments formulate and enforce regulations.
2. **Empirical Policy Research:** Facilitates microdata downloads (CSV, SQLite, XLSX) to cross-reference municipal regulatory activity with sociodemographic indicators, municipal budgets (SINIM), and territorial typologies.
3. **Local Transparency Diagnostics:** Helps identify active disclosure gaps and institutional capacity asymmetries across urban, rural, and under-resourced municipalities.
4. **Methodological Traceability:** Teaches public data collection standards, distinguishing verified corpus, demonstrated exhaustive coverage, and quarantined unverified records.

---

## 🗺️ Project Roadmap

- [x] **Phase 1: Base Registry & Reproducible Pipeline:** BCN SPARQL extraction (1,710 records) + initial multi-agent crawler + 9-domain classification.
- [x] **Phase 2: Public Visualizer & Open Access:** Interactive dashboard hosted on GitHub Pages with multi-filter matrix, detailed commune drawer, interactive Leaflet map, smart autocomplete, and open data downloads.
- [x] **Phase 3: Direct Municipal Crawling:** Direct municipal crawler with cryptographic verification (SHA-256), reaching **100.0% national coverage (346 of 346 communes)** and **3,015 consolidated official ordinances**.
- [ ] **Phase 4: AI-Assisted RAG & Text Analysis ($0 API Cost):** Full-text vector indexing (BGE-M3 / e5-small embeddings) and local inference (Ollama RTX 4080) / OpenRouter Free Tier for semantic comparative legal queries.
- [x] **Phase 5: Teaching Modules & Academic Workbooks:** 3 interactive case studies in the web dashboard and official downloadable Jupyter Notebook (`analisis_ordenanzas_chile_estudiantes.ipynb`) for university courses.

---

## 📁 Repository Structure

```text
catastro-ordenanzas-municipales/
├── .github/workflows/          # CI/CD: build snapshot & GitHub Pages deploy
├── data/                       # Official registries and verified datasets
│   ├── maestro_comunas_chile.csv        # Master territorial reference (346 communes)
│   ├── municipal_source_registry.json   # Registry of official municipal endpoints
│   ├── municipal_verified_records.json  # 1,305 municipal acts verified with SHA-256
│   ├── cplt_municipal_directory.json    # Active Transparency CPLT directory
│   └── national_coverage_ledger.json    # National coverage ledger
├── dashboard/                  # Static web dashboard (GitHub Pages)
│   ├── descargas/              # XLSX, CSV, ZIP, and teaching notebook downloads
│   ├── index.html              # Responsive web application
│   ├── mapa_chile.js           # Interactive Leaflet.js map logic
│   └── status_data.json        # Live JSON snapshot and metrics
├── src/                        # Reproducible ETL pipeline and evidence verifiers
│   ├── bcn_full_fetcher.py              # BCN/LeyChile SPARQL query extractor
│   ├── cplt_transparencia_crawler.py    # CPLT Active Transparency crawler
│   ├── exhaustive_municipal_recovery.py # Municipal extractor with evidence contract
│   ├── build_public_snapshot.py         # Master snapshot & export compiler
│   ├── build_accurate_map_data.py       # Accurate geospatial coordinate generator
│   ├── export_excel_and_zip.py          # Multi-format data exporter
│   └── generate_docent_notebook.py      # Educational Jupyter Notebook builder
├── LICENSE                     # MIT License
├── README.md                   # Spanish documentation
├── README.en.md                # English documentation
└── requirements.txt            # Reproducible dependencies
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/evegat/catastro-ordenanzas-municipales.git
cd catastro-ordenanzas-municipales

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Run SPARQL ingestion from BCN
python src/bcn_full_fetcher.py

# 2. Run municipal crawler with SHA-256 verification
python src/exhaustive_municipal_recovery.py

# 3. Build public snapshot and release packages
python src/build_public_snapshot.py dashboard
```

---

## 📊 Dataset Scope

- **Consolidated Normative Records:** 7,186.
- **BCN / LeyChile:** 5,881 records.
- **Verified Municipal Sources (SHA-256):** 1,305 official records.
- **Observed Territorial Coverage:** 346 of 346 communes (100.0% national presence; only 5 single-ordinance communes remaining, 98.6% dense coverage).
- **Observed Time Span:** 1980–2026.
- **Thematic Domains:** 9 municipal regulatory axes.

---

## 👤 Author

**Eduardo Vega Toledo**  
*Public Administrator · Master in Government & Public Management · Computer Engineering Student*  
Former Head of Municipal Investment Dept. (SUBDERE) · Lecturer at FAGOB Universidad de Chile.

