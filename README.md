# Catastro y Pipeline de Ordenanzas Municipales de Chile

Herramienta de extracción automatizada, estructuración y catálogo nacional de **ordenanzas municipales de Chile** a partir del endpoint SPARQL y datos abiertos de la **Biblioteca del Congreso Nacional (BCN)** y portales de Transparencia Activa (CPLT).

---

## 🎯 Propósito del Proyecto

Las ordenanzas municipales constituyen el marco regulatorio local fundamental para la convivencia, comercio, urbanismo y gobernanza territorial en las 346 comunas de Chile. Sin embargo, su acceso suele estar fragmentado entre distintos repositorios institucionales.

Este proyecto tiene como objetivos:
1. **Consolidar y estructurar** un catastro unificado de más de 1.570 recursos normativos municipales.
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
├── dashboard/                         # Visualizador web local interactivo
│   ├── index.html
│   └── descargas/                     # Datasets compilados listos para análisis
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
pip install requests pandas openpyxl
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

* **Recursos catastrados:** Más de 1.570 ordenanzas municipales.
* **Cobertura territorial:** 218 identificadores municipales indexados en BCN (con pipeline complementario para cobertura total vía Transparencia Activa Ley 20.285).
* **Rango temporal registrado:** 1980 a la fecha.

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.
