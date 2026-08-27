# Chilean Municipal By-Laws (Ordenanzas) Open Data Pipeline

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Open Data](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🇪🇸 Versión en Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Automated ETL pipeline, structured dataset, and exploratory dashboard for **Chilean Municipal By-Laws (*Ordenanzas Municipales*)**, querying open data from the **Library of the National Congress of Chile (BCN)** SPARQL endpoint and Active Transparency portals.

---

## 🎯 Overview & Objectives

Municipal ordinances are the core local regulatory framework across all 346 Chilean municipalities. However, access is traditionally fragmented.

This project delivers:
1. A **consolidated open dataset** indexing 1,570+ municipal regulatory acts.
2. **Reproducible Python pipelines** leveraging SPARQL semantic queries and web scrapers.
3. An **offline-first interactive dashboard** for researchers, public policy analysts, and municipal legal teams.

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
├── dashboard/                         # Local HTML5/JS dashboard
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

## 👤 Author

**Eduardo Vega Toledo**  
*Public Administrator · Master in Government & Public Management · Computer Engineering Student*  
Former Head of Municipal Investment Dept. (SUBDERE) · Lecturer at FAGOB Universidad de Chile.
