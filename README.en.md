# Chilean Municipal By-Laws (Ordenanzas) Open Data Pipeline

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Open Data](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Launch Interactive Dashboard Online** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Versión en Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Automated ETL pipeline, structured dataset, and exploratory dashboard for **Chilean Municipal By-Laws (*Ordenanzas Municipales*)**, querying open data from the **Library of the National Congress of Chile (BCN)** SPARQL endpoint and complementary **Active Transparency (CPLT)** records.

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

- [x] **Phase 1: Base Registry & Reproducible Pipeline:** BCN SPARQL extraction (1,572 records) + CPLT multi-agent crawler (60 records) + 9-domain classification.
- [x] **Phase 2: Public Visualizer & Open Access:** Interactive dashboard hosted on GitHub Pages with multi-filter matrix, detailed commune drawer, and multi-format downloads (XLSX, CSV, SQLite, ZIP).
- [ ] **Phase 3: Direct Municipal Crawling:** Automated ingestion pipelines directly targeting municipal websites to bridge the gap for the remaining 129 municipalities.
- [ ] **Phase 4: AI-Assisted Text Analysis & Normative Comparison:** Full-text indexing (PDF/HTML), semantic search, and detection of standard/template ordinance patterns.
- [ ] **Phase 5: Teaching Modules & Academic Workbooks:** Downloadable research guides, case studies, and Jupyter/R notebooks for university courses on local governance.

---

## 📁 Repository Structure

```text
├── data/
│   └── maestro_comunas_chile.csv      # Master territorial and municipal reference catalogue
├── src/
│   ├── bcn_full_fetcher.py            # BCN SPARQL endpoint query worker
│   ├── enrich_all_bcn.py              # Metadata enrichment and normalization
│   ├── cplt_transparencia_crawler.py  # CPLT Active Transparency crawler module
│   ├── maestro_generator.py           # Core dataset compiler
│   └── export_excel_and_zip.py        # Export multi-format open packages (XLSX, CSV, JSON)
├── dashboard/                         # HTML5/JS dashboard (GitHub Pages)
│   └── descargas/                     # Precompiled data packages
├── requirements.txt                   # Reproducible Python dependencies
├── LICENSE                            # MIT License
└── README.md
```

---

## 🚀 Quickstart

```bash
git clone https://github.com/evegat/catastro-ordenanzas-municipales.git
cd catastro-ordenanzas-municipales

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run SPARQL ingestion
python src/bcn_full_fetcher.py

# Export clean datasets
python src/export_excel_and_zip.py
```

---

## 📊 Dataset Scope

Published dataset snapshot: **August 27, 2026**.

- **Indexed records:** 1,632.
- **Sources:** 1,572 BCN records plus 60 complementary CPLT Active Transparency records (2022–2026).
- **Observed territorial coverage:** 217 of Chile's 346 communes have at least one record in the consolidated dataset.
- **Observed time span:** 1980–2026.
- **Thematic classification:** 9 categories.

### Methodological note and limitations

This catalogue consolidates documents identified in the consulted sources and should not be interpreted as a certification that each municipality's regulatory corpus is complete. **No records for a commune does not necessarily mean that the municipality has no ordinances in force**; it may reflect publication gaps, source lag, identifier differences, or limitations in document discovery.

Territorial coverage is calculated over Chile's **346 communes**. A commune is counted as “covered” when the published dataset contains at least one associated record. Figures may change between versions as new sources are incorporated, identifiers are corrected, and duplicates are reviewed.

---

## 👤 Author

**Eduardo Vega Toledo**  
*Public Administrator · Master in Government & Public Management · Computer Engineering Student*  
Former Head of Municipal Investment Dept. (SUBDERE) · Lecturer at FAGOB Universidad de Chile.
