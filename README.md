# Catastro y Pipeline de Ordenanzas Municipales de Chile

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Herramienta de extracción, estructuración y catálogo nacional de **ordenanzas municipales de Chile**. La fuente estructurada principal es la **Biblioteca del Congreso Nacional (BCN/LeyChile)**; el proyecto incorpora además referencias complementarias identificadas en portales municipales y de Transparencia Activa.

---

## 🎯 Propósito del Proyecto

Las ordenanzas municipales constituyen el marco regulatorio local fundamental para la convivencia, comercio, urbanismo y gobernanza territorial en las 346 comunas de Chile. Sin embargo, su acceso suele estar fragmentado entre distintos repositorios institucionales.

Este proyecto tiene como objetivos:
1. **Consolidar y estructurar** un catastro unificado de recursos normativos municipales.
2. **Proveer pipelines reproducibles en Python** para consultar el endpoint SPARQL de la BCN y procesar fuentes complementarias.
3. **Ofrecer un catálogo descargable y visualizador interactivo** para análisis de políticas públicas locales y derecho municipal.
4. **Mantener trazabilidad de las fuentes**, distinguiendo entre enlaces persistentes/verificables y referencias históricas que requieren revalidación.

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
│   ├── maestro_generator.py           # Generador de estructura consolidada
│   └── export_excel_and_zip.py        # Exportación en formatos abiertos (XLSX, CSV, JSON)
├── dashboard/                         # Visualizador web interactivo (GitHub Pages)
│   ├── index.html
│   ├── cplt-safety.js                 # Capa de seguridad para enlaces CPLT no verificados
│   └── descargas/                     # Datasets compilados listos para análisis
├── requirements.txt                   # Dependencias de Python reproducibles
├── LICENSE                            # Licencia MIT
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
# Ejecutar pipeline de extracción SPARQL BCN
python src/bcn_full_fetcher.py

# Enriquecer y exportar resultados consolidados
python src/export_excel_and_zip.py
```

### 3. Verificar referencias CPLT/municipales
```bash
python src/verify_cplt_links.py
```

El verificador registra código HTTP, redirecciones, tipo de recurso y si la URL parece apuntar directamente a un documento. **Una respuesta HTTP correcta no certifica vigencia ni autenticidad normativa.**

---

## 📊 Alcance y Cobertura de Datos

Corte del dataset publicado: **27 de agosto de 2026**.

- **Recursos catastrados:** 1.632 registros normativos.
- **Fuentes:** 1.572 registros BCN y 60 referencias complementarias municipales/Transparencia Activa (2022–2026).
- **Cobertura territorial observada:** 217 de 346 comunas presentan al menos un registro en las fuentes consolidadas.
- **Rango temporal registrado:** 1980–2026.
- **Clasificación temática:** 9 materias.

### Nota metodológica y limitaciones

El catastro consolida documentos y referencias identificados en las fuentes consultadas y no constituye, por sí solo, una certificación de completitud normativa de cada municipalidad. **La ausencia de registros para una comuna no implica necesariamente que esa municipalidad no tenga ordenanzas vigentes**; puede reflejar ausencia, rezago, diferencias de publicación o dificultades de identificación en las fuentes disponibles.

Los **60 registros complementarios asociados a Transparencia Activa/portales municipales no deben interpretarse como 60 documentos preservados por el CPLT**. Fueron consolidados como referencias con URLs externas municipales. Esas URLs pueden cambiar, redirigir a la portada del organismo o devolver 404. Desde la corrección `MW-P090-0002`, el dashboard deja de presentarlas como “documentos CPLT vigentes”: se muestran como **referencias no verificadas** y se deriva la consulta al Portal de Transparencia oficial hasta que exista validación documental reproducible.

El archivo `src/cplt_transparencia_crawler.py` corresponde actualmente a una base de implementación y **no constituye todavía un crawler productivo**. Para auditar la accesibilidad de las URLs registradas se debe ejecutar `src/verify_cplt_links.py`.

La cobertura comunal se calcula sobre las **346 comunas de Chile** y considera como “comuna con datos” aquella para la cual el dataset publicado contiene al menos un registro asociado. Las cifras pueden variar entre versiones a medida que se incorporan nuevas fuentes, se corrigen identificadores o se depuran duplicados.

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.
