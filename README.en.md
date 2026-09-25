# Chilean Municipal Regulations & By-Laws Open Data Pipeline

> **Version 3.0 (September 2026 release).** Independent open research initiative: **7,321 cataloged normative records** across all 346 communes of Chile (5,881 BCN/LeyChile + 1,440 verified municipal records with SHA-256). Includes legal framework analysis, national territorial visualizer, and local traceable assistant.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success.svg)](https://ordenanzas.evegat.cl)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Open Data](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Open Live Interactive Dashboard** ](https://ordenanzas.evegat.cl)  
[ 🇪🇸 Versión en Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Independent automated ETL pipeline, structured dataset, and exploratory visualizer for **Chilean Municipal Regulations and By-Laws (*Ordenanzas Municipales*)**, querying open data from the **Library of the National Congress of Chile (BCN/LeyChile)** SPARQL endpoint and complementary verified municipal sources with SHA-256 cryptographic hashes.

> **Coverage & Scope:** National territorial presence across all 346 communes of Chile (100%). Document exhaustiveness not certified (subject to digital publishing availability per municipality).

---

## 🎯 Purpose & Educational Focus

Municipal ordinances are the primary legal mechanism through which Chilean local governments exercise regulatory autonomy across everyday life (local fees, environmental sanitation, municipal permits, urban planning, and coexistence) in all 346 municipalities.

### Research and Teaching Tool for Local Governance
This project is built primarily as an educational and empirical research resource:
1. **Undergraduate & Graduate Tool:** Enables students of Public Administration, Political Science, Law, Urban Studies, and Public Policy to explore how local governments formulate and enforce regulations.
2. **Empirical Policy Research:** Facilitates microdata downloads (CSV, SQLite, XLSX) to cross-reference municipal regulatory activity with sociodemographic indicators, municipal budgets (SINIM), and territorial typologies.
3. **Local Transparency Diagnostics:** Helps identify active disclosure gaps and institutional capacity asymmetries across urban, rural, and under-resourced municipalities.
4. **Methodological Traceability:** Teaches public data collection standards, distinguishing verified corpus, territorial presence, and documents with cryptographic verification.

---

## 🗺️ Project Roadmap

- [x] **Phase 1: Base Registry & Reproducible Pipeline:** BCN SPARQL extraction (1,710 records) + initial multi-agent crawler + 9-domain classification.
- [x] **Phase 2: Public Visualizer & Open Access:** Interactive dashboard hosted on GitHub Pages with multi-filter matrix, detailed commune drawer, interactive Leaflet map, smart autocomplete, and open data downloads.
- [x] **Phase 3: Direct Territorial Expansion:** Pipeline discovering and validating municipal documents with SHA-256 hashes, reaching **coverage across all 346 communes** with **7,321 consolidated normative records** (5,881 BCN + 1,440 verified municipal records).
- [x] **Phase 4: Traceable Municipal Legal Assistant ("Chatcito"):** Client-side floating assistant (`asistente_chat.js`) querying all 7,321 records in real-time with direct source links and zero token inference cost.
- [x] **Phase 5: Educational Module & Legal Framework:** Interactive live auditor for regulations with specific legal mandate (Fees, Citizen Participation, Waste, Pet Ownership, Master Urban Plan, Municipal Subsidies), doctrinal clarification on PLACMA vs. Environmental By-law, 3 case studies, and downloadable Jupyter Notebook.

---

## 📁 Repository Structure

```text
catastro-ordenanzas-municipales/
├── .github/workflows/          # CI/CD: build snapshot & GitHub Pages deploy
├── data/                       # Official registries and verified datasets
│   ├── maestro_comunas_chile.csv        # Master territorial reference (346 communes)
│   ├── municipal_source_registry.json   # Registry of official municipal endpoints
│   ├── municipal_verified_records.json  # 1,440 municipal acts verified with SHA-256
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

## Local preview

Serve the existing dashboard with Python:

```bash
python -m http.server 8000 --directory dashboard
```

Open http://localhost:8000. This does not rebuild data. Extraction scripts depend on missing local modules; consult the [restart guide](docs/ESTADO-Y-REENTRADA-P090.md). `src/build_public_snapshot.py` overwrites the selected dashboard directory; verify using a separate copy.

## 📊 Dataset Scope

- **Consolidated Normative Records:** 7,321.
- **BCN / LeyChile:** 5,881 records.
- **Verified Municipal Sources (SHA-256):** 1,440 official records.
- **Territorial presence:** 346/346 communes; 4 have one record and 19 have 1–3. Completeness remains unproven.
- **Observed Time Span:** 1980–2026.
- **Thematic Domains:** 9 municipal regulatory axes.

---

## 👤 Author

**Eduardo Vega Toledo**  
*Public Administrator · Master in Government & Public Management · Computer Engineering Student*  
Former Head of Municipal Investment Dept. (SUBDERE) · Lecturer at FAGOB Universidad de Chile.

