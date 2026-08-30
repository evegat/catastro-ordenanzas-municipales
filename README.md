# Catastro y Pipeline de Ordenanzas Municipales de Chile

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-Online-success.svg)](https://evegat.github.io/catastro-ordenanzas-municipales/)
[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Datos Abiertos](https://img.shields.io/badge/Open%20Data-Chile-green.svg)](#)

[ 🌐 **Abrir Dashboard Interactivo en Vivo** ](https://evegat.github.io/catastro-ordenanzas-municipales/)  
[ 🇪🇸 Español ](README.md) · [ 🇬🇧 English version ](README.en.md)

Herramienta de extracción, estructuración y catálogo nacional de **ordenanzas municipales de Chile**. La fuente estructurada principal es la **Biblioteca del Congreso Nacional (BCN/LeyChile)** y el corpus se complementa con documentos recuperados desde repositorios municipales oficiales y Transparencia Activa cuando existe evidencia reproducible.

> **Meta de cobertura:** exhaustiva, no muestral. El objetivo es identificar **todas las ordenanzas publicadas oficialmente por las 345 municipalidades de Chile**, que administran las 346 comunas del país, incluyendo su historia oficial disponible y sus actos modificatorios cuando corresponda. Un municipio no se considera cubierto por haber encontrado una o varias normas.

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

- [x] **Fase 1: Catastro Base & Pipeline Reproducible:** Extracción SPARQL BCN (1.572 normas), captura complementaria CPLT (60 normas) y categorización en 9 ejes temáticos.
- [x] **Fase 2: Visualizador Público & Acceso Abierto:** Dashboard interactivo publicado en GitHub Pages, filtros combinados por materia, región y año, drawer comunal y descargas multiformato (XLSX, CSV, SQLite, ZIP).
- [ ] **Fase 3: Expansión Territorial Directa:** Desarrollo de scrapers específicos sobre portales municipales para cerrar la brecha de las 129 comunas sin presencia en BCN.
- [ ] **Fase 4: Análisis Textual & Comparador Normativo por IA:** Indexación de texto completo (PDF/HTML), búsqueda semántica y detección de patrones de "ordenanzas tipo" y variaciones comunales.
- [ ] **Fase 5: Módulo Docente & Guías Metodológicas:** Publicación de guías didácticas, ejercicios prácticos y notebooks (Python/R) para uso directo en cátedras universitarias sobre gestión local.

---

## 📁 Estructura del Repositorio

```text
├── data/
│   ├── maestro_comunas_chile.csv              # Catálogo maestro territorial
│   ├── municipal_source_registry.json         # Registro y estrategia de fuentes oficiales
│   └── municipal_verified_records.json        # Actos municipales promovidos con evidencia
├── src/
│   ├── bcn_full_fetcher.py                    # Extracción BCN/SPARQL
│   ├── enrich_all_bcn.py                      # Limpieza y normalización
│   ├── cplt_transparencia_crawler.py          # Directorio CPLT + recovery documental
│   ├── exhaustive_municipal_recovery.py       # Auditor de exhaustividad por fuente/municipio
│   ├── verify_cplt_links.py                   # Verificación reproducible de URLs heredadas
│   ├── build_public_snapshot.py               # Publicación verified-only
│   ├── maestro_generator.py                   # Generador de estructura consolidada
│   └── export_excel_and_zip.py                # Exportaciones
├── dashboard/                                 # Visualizador web
├── .github/workflows/municipal-recovery-audit.yml
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🛠️ Stack Tecnológico

- **Lenguaje:** Python 3.10+
- **Bibliotecas:** `requests`, `pandas`, `openpyxl`, `beautifulsoup4`, `pypdf`
- **Protocolos & Datos:** SPARQL, HTTP, HTML, PDF, Open Data
- **Frontend / Dashboard:** HTML5, JavaScript moderno, Tailwind CSS
- **Control de evidencia:** descarga real, firma PDF, código HTTP, tamaño, URL resuelta y SHA-256

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

### 3. Recovery municipal conocido
```bash
python src/cplt_transparencia_crawler.py recover \
  --registry data/municipal_source_registry.json \
  --out data/municipal_recovery_report.json \
  --verified-out data/municipal_recovery_verified.json
```

### 4. Auditoría exhaustiva
```bash
python src/exhaustive_municipal_recovery.py \
  --registry data/municipal_source_registry.json \
  --out data/municipal_exhaustive_coverage.json
```

El auditor recorre las fuentes oficiales según su estrategia, agota la paginación cuando corresponde, separa ordenanzas de modificaciones y actos relacionados, verifica los documentos y produce un ledger nacional de estados `complete`, `partial` y `unregistered`.

### 5. Verificar referencias heredadas CPLT/municipales
```bash
python src/verify_cplt_links.py
```

Una respuesta HTTP correcta **no certifica** vigencia, autenticidad normativa ni exhaustividad.

### 6. Construir snapshot público verified-only
```bash
python src/build_public_snapshot.py dashboard
```

En producción este paso se ejecuta sobre una copia de `dashboard/`, excluye referencias CPLT no verificadas y regenera las descargas antes de desplegar GitHub Pages.

---

<<<<<<< HEAD
## 📊 Alcance, cobertura y estados de evidencia

Los conteos públicos **no se mantienen manualmente en este README**. Se recalculan en cada build desde las filas efectivamente publicables y quedan expuestos en `dashboard/status_data.json`, en el dashboard y en el manifiesto de descargas.

### 1. Corpus público verificado
Puede incluir:
- registros **BCN/LeyChile**;
- documentos municipales oficiales cuya descarga y metadatos han sido validados;
- SHA-256, tamaño y fecha de verificación para los documentos municipales promovidos.

**Importante:** que un registro esté verificado significa que ese documento particular tiene evidencia reproducible. No significa que la municipalidad esté exhaustivamente cubierta.

### 2. Cobertura municipal exhaustiva
Una municipalidad solo obtiene estado `complete` cuando:
1. existe una fuente oficial considerada autoritativa para el universo correspondiente;
2. toda su paginación/listado fue recorrida;
3. se enumeraron todos los candidatos pertinentes;
4. no quedan candidatos sin resolver;
5. cada documento incorporado supera el contrato de evidencia;
6. la fuente utilizada es suficiente para sostener cobertura actual, o se ha reconciliado con las demás fuentes oficiales necesarias.

Las fuentes históricas que no prueban actualidad pueden aportar documentos sin cerrar la cobertura municipal.

### 3. Cuarentena
Las referencias históricas CPLT/Transparencia Activa cuyo documento no puede demostrarse permanecen preservadas, pero **no se publican como ordenanzas verificadas**.

### 4. Tipos de acto
El recovery conserva el universo documental, pero evita llamar “ordenanza” a cualquier PDF que meramente la mencione. Los hallazgos se tipifican, entre otros, como:
- `ordenanza`
- `modificacion`
- `acto_relacionado`
- `documento_indice`

Esto permite mantener exhaustividad de evidencia sin inflar artificialmente el número de ordenanzas.

### 5. Universo territorial
Chile tiene **346 comunas y 345 municipalidades**. La Municipalidad de Cabo de Hornos administra las comunas de Cabo de Hornos y Antártica. Por lo tanto, el ledger de completitud institucional usa 345 municipalidades, manteniendo la correspondencia territorial con 346 comunas.

---

## 🔬 Política metodológica

### NO SAMPLING
Encontrar una norma, cinco normas o cincuenta normas de un municipio **no autoriza a declararlo cubierto**. El objetivo final es el universo oficial disponible.

### Evidencia mínima de un documento municipal
1. fuente/listado oficial identificable;
2. URL documental resoluble;
3. descarga real del recurso;
4. contenido compatible con PDF;
5. bytes > 0;
6. SHA-256;
7. fecha de verificación;
8. relación jurídica con la ordenanza correctamente tipificada.

### Deduplificación
La consolidación debe distinguir entre:
- duplicados exactos del mismo archivo;
- textos refundidos o versiones actualizadas;
- modificaciones normativas distintas;
- documentos relacionados que no constituyen por sí mismos una ordenanza.

La trazabilidad original se conserva aun cuando dos fuentes terminen refiriéndose al mismo acto jurídico.

---

## ⚠️ Estado del proyecto

El dashboard público es un **corpus verificado en expansión**. No debe interpretarse todavía como prueba de exhaustividad nacional hasta que el ledger de cobertura alcance las 345 municipalidades y se resuelvan las discrepancias entre fuentes oficiales.

La automatización de recovery se encuentra en desarrollo activo precisamente para cerrar esa brecha de cobertura de manera reproducible, en vez de completar el catastro mediante muestras manuales.

---

## 👤 Autor

**Eduardo Vega Toledo**  
*Administrador Público · Magíster en Gobierno y Gerencia Pública · Est. Ing. Civil Informática*  
Ex Jefe de Departamento de Inversión Municipal e Infraestructura (SUBDERE) · Docente en FAGOB Universidad de Chile.
