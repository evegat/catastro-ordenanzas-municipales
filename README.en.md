# Chilean Municipal By-Laws (Ordenanzas) Open Data Pipeline

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Open Data](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Launch Interactive Dashboard Online** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Versión en Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Automated ETL pipeline, structured dataset, and exploratory dashboard for **Chilean Municipal By-Laws (*Ordenanzas Municipales*)**, querying open data from the **Library of the National Congress of Chile (BCN)** SPARQL endpoint and Active Transparency portals.

---

## 🎯 Overview & Objectives

Municipal ordinances are the core local regulatory framework across all 346 Chilean municipalities. However, access is traditionally fragmented.

This project delivers:
1. A **consolidated open dataset** of municipal regulatory records.
2. **Reproducible Python pipelines** leveraging SPARQL semantic queries and complementary sources.
3. An **interactive dashboard** for researchers, public policy analysts, and municipal legal teams.

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
