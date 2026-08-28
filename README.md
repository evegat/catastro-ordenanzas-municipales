# Catastro y Pipeline de Ordenanzas Municipales de Chile

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Herramienta de extracción, estructuración y catálogo nacional de **ordenanzas municipales de Chile**. La fuente estructurada principal y actualmente publicable es la **Biblioteca del Congreso Nacional (BCN/LeyChile)**. Las referencias complementarias identificadas en portales municipales/Transparencia Activa se preservan en cuarentena hasta contar con evidencia documental reproducible.

---

## 🎯 Propósito del Proyecto

Las ordenanzas municipales constituyen el marco regulatorio local fundamental para la convivencia, comercio, urbanismo y gobernanza territorial en las 346 comunas de Chile. Sin embargo, su acceso suele estar fragmentado entre distintos repositorios institucionales.

Este proyecto tiene como objetivos:
1. **Consolidar y estructurar** un catastro unificado de recursos normativos municipales.
2. **Proveer pipelines reproducibles en Python** para consultar el endpoint SPARQL de la BCN y procesar fuentes complementarias.
3. **Ofrecer un catálogo descargable y visualizador interactivo** para análisis de políticas públicas locales y derecho municipal.
4. **Mantener trazabilidad de las fuentes**, distinguiendo entre corpus público verificable y referencias en cuarentena.

---

## 📁 Estructura del Repositorio

```text
├── data/
│   └── maestro_comunas_chile.csv      # Catálogo maestro de comunas y códigos territoriales
├── src/
│   ├── bcn_full_fetcher.py            # Extracción desde el endpoint SPARQL de la BCN
│   ├── enrich_all_bcn.py              # Limpieza, enriquecimiento y normalización de metadatos
│   ├── cplt_transparencia_crawler.py  # Esqueleto de integración con Transparencia Activa
│   ├── verify_cplt_links.py           # Verificación reproducible de URLs CPLT/municipales
│   ├── build_public_snapshot.py       # Construye publicación verified-only y descargas
│   ├── maestro_generator.py           # Generador de estructura consolidada
│   └── export_excel_and_zip.py        # Exportación de fuentes de trabajo
├── dashboard/                         # Fuente del visualizador web
│   ├── index.html
│   ├── status_data.json
│   └── descargas/
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Bibliotecas:** `requests`, `pandas`, `openpyxl`
- **Protocolos & Datos:** SPARQL (RDF/XML, JSON), HTTP, Open Data
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
python src/bcn_full_fetcher.py
python src/export_excel_and_zip.py
```

### 3. Verificar referencias CPLT/municipales
```bash
python src/verify_cplt_links.py
```

El verificador registra código HTTP, redirecciones, tipo de recurso y si la URL parece apuntar directamente a un documento. **Una respuesta HTTP correcta no certifica vigencia ni autenticidad normativa.**

### 4. Construir snapshot público verified-only
```bash
python src/build_public_snapshot.py dashboard
```

En producción este paso se ejecuta sobre una copia de `dashboard/` y excluye toda referencia CPLT no verificada antes de publicar GitHub Pages y regenerar las descargas.

---

## 📊 Alcance y Cobertura de Datos

Corte de referencia: **27 de agosto de 2026**.

### Corpus público
- **1.572 registros BCN/LeyChile** con resolución mediante la fuente estructurada utilizada por el proyecto.
- El número de comunas con registros públicos se calcula nuevamente durante cada build, una vez retirada la cuarentena.
- Rango temporal observado: 1980–2026.
- Clasificación temática: 9 materias.

### Cuarentena
- **60 referencias municipales/Transparencia Activa (2022–2026)** permanecen preservadas en el repositorio de trabajo, pero **no forman parte del dataset ni del dashboard público**.
- Estas referencias fueron incorporadas desde una lista manual de URLs externas y no cuentan todavía, registro por registro, con documento preservado y evidencia reproducible suficiente.

### Criterio de reincorporación

Una referencia complementaria solo vuelve al corpus público cuando disponga de:
1. URL oficial resoluble o copia documental preservada.
2. Correspondencia comprobable entre documento y metadatos del registro.
3. Fecha de verificación y estado de acceso.
4. Trazabilidad suficiente para reproducir la incorporación.

### Nota metodológica

El catastro no certifica completitud normativa por municipalidad. **La ausencia de registros para una comuna no implica que esa municipalidad no tenga ordenanzas vigentes**; puede reflejar diferencias de publicación, cobertura de las fuentes o dificultades de identificación.

`src/cplt_transparencia_crawler.py` sigue siendo una base de implementación y **no constituye todavía un crawler productivo**. Hasta completar ese componente y validar las referencias, GitHub Pages se construye bajo política `verified-only` y publica exclusivamente el corpus BCN/LeyChile.

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.
