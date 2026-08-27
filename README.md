# Catastro y Pipeline de Ordenanzas Municipales de Chile

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Herramienta de extracción automatizada, estructuración y catálogo nacional de **ordenanzas municipales de Chile** a partir del endpoint SPARQL y datos abiertos de la **Biblioteca del Congreso Nacional (BCN)** y portales de Transparencia Activa (CPLT).

---

## 🎯 Propósito del Proyecto

Las ordenanzas municipales constituyen el marco regulatorio local fundamental para la convivencia, comercio, urbanismo y gobernanza territorial en las 346 comunas de Chile. Sin embargo, su acceso suele estar fragmentado entre distintos repositorios institucionales.

Este proyecto tiene como objetivos:
1. **Consolidar y estructurar** un catastro unificado de recursos normativos municipales.
2. **Proveer pipelines reproducibles en Python** para consultar el endpoint SPARQL de la BCN y fuentes complementarias.
3. **Ofrecer un catálogo descargable y visualizador interactivo** para análisis de políticas públicas locales y derecho municipal.

---

## 📁 Estructura del Repositorio

```text
├── data/
│   └── maestro_comunas_chile.csv      # Catálogo maestro de comunas y códigos territoriales
├── src/
│   ├── bcn_full_fetcher.py            # Extracción desde el endpoint SPARQL de la BCN
│   ├── enrich_all_bcn.py              # Limpieza, enriquecimiento y normalización de metadatos
│   ├── cplt_transparencia_crawler.py  # Vía complementaria sobre Transparencia Activa CPLT
│   ├── maestro_generator.py           # Generador de estructura consolidada
│   └── export_excel_and_zip.py        # Exportación en formatos abiertos (XLSX, CSV, JSON)
├── dashboard/                         # Visualizador web interactivo (GitHub Pages)
│   ├── index.html
│   └── descargas/                     # Datasets compilados listos para análisis
├── requirements.txt                   # Dependencias de Python reproducibles
├── LICENSE                            # Licencia MIT
└── README.md
```

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Bibliotecas:** `requests`, `pandas`, `openpyxl`
- **Protocolos & Datos:** SPARQL (RDF/XML, JSON), REST APIs, Open Data
- **Frontend / Dashboard:** HTML5, JavaScript moderno, Tailwind CSS

---

## 🚀 Uso y Reproducción

### 1. Requisitos e Instalación
```bash
git clone https://github.com/evegat/catastro-ordenanzas-municipales.git
cd catastro-ordenanzas-municipales

python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ejecutar extracción y procesamiento
```bash
# Ejecutar pipeline de extracción SPARQL BCN
python src/bcn_full_fetcher.py

# Enriquecer y exportar resultados consolidados
python src/export_excel_and_zip.py
```

---

## 📊 Alcance y Cobertura de Datos

Corte del dataset publicado: **27 de agosto de 2026**.

- **Recursos catastrados:** 1.632 registros normativos.
- **Fuentes:** 1.572 registros BCN y 60 registros complementarios de Transparencia Activa CPLT (2022–2026).
- **Cobertura territorial observada:** 217 de 346 comunas presentan al menos un registro en las fuentes consolidadas.
- **Rango temporal registrado:** 1980–2026.
- **Clasificación temática:** 9 materias.

### Nota metodológica y limitaciones

El catastro consolida documentos identificados en las fuentes consultadas y no constituye, por sí solo, una certificación de completitud normativa de cada municipalidad. **La ausencia de registros para una comuna no implica necesariamente que esa municipalidad no tenga ordenanzas vigentes**; puede reflejar ausencia, rezago, diferencias de publicación o dificultades de identificación en las fuentes disponibles.

La cobertura comunal se calcula sobre las **346 comunas de Chile** y considera como “comuna con datos” aquella para la cual el dataset publicado contiene al menos un registro asociado. Las cifras pueden variar entre versiones a medida que se incorporan nuevas fuentes, se corrigen identificadores o se depuran duplicados.

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.
