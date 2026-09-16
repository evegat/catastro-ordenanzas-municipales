# Inventario Documental y Conciliación de Cifras — P090

- **Task ID:** `P090-20260908-plan-publico-02`
- **Fecha de corte:** 2026-09-16
- **Estado:** Completado sin LLM mediante inspección física y sintáctica determinista.

---

## 1. Resumen Ejecutivo de Cifras Canónicas

| Dimensión | Cifra Canónica Observada | Estado de Evidencia |
| :--- | :--- | :--- |
| **Total registros normativos públicos** | **7.226** | Publicados en `dashboard/status_data.json` y descargas CSV/XLSX/ZIP. |
| **Registros BCN / LeyChile** | **5.881** | Extracción SPARQL / LeyChile disponible en catálogo. |
| **Registros Municipales Verificados** | **1.345** | Validados con SHA-256, HTTP 200 y HTTPS oficial. |
| **Cobertura territorial comunal** | **346 de 346 (100%)** | Todas las comunas tienen $\ge 1$ registro normativo. |
| **Comunas con 1 sola norma** | **5 comunas** | Pencahue, Hualpén, Cholchol, O'Higgins y Antártica. |
| **Comunas de baja densidad (1 a 3 normas)**| **21 comunas** | 5 con 1 norma, 10 con 2 normas y 6 con 3 normas. |
| **Comunas con acervo denso (> 3 normas)** | **325 comunas (93,9%)** | Densidad normativa promedio de ~21 ordenanzas por comuna. |

> [!NOTE]
> **Nota de conciliación con el README y Bitácora:**
> En versiones previas de la documentación figuraba la cifra de **7.186** registros (5.881 BCN + 1.305 municipales). Tras la incorporación final de 40 ordenanzas municipales adicionales validadas en `municipal_verified_records.json`, la cifra canónica real y efectiva del snapshot público es **7.226 registros** (5.881 BCN + 1.345 municipales).

---

## 2. Inventario de Binarios y Almacenamiento Local vs Remoto

| Activo | Ubicación | Cantidad | Tipo de Contenido |
| :--- | :--- | :--- | :--- |
| **PDFs Físicos en Repositorio** | `data/official_pdfs/` | **10 archivos** | Binarios PDF descargados localmente. |
| **Textos JSON de BCN** | `D:\Datasets\P090 - BCN Ordenanzas municipales\bcn_textos\` | **19 archivos** | Extracciones de texto estructurado de normas BCN históricas. |
| **Base SQLite Histórica** | `D:\Datasets\P090 - BCN Ordenanzas municipales\catastro_ordenanzas.db` | **1.632 filas** | Base relacional histórica de la Fase 1 (ordenanzas BCN iniciales). |
| **Referencias con Hash Remoto** | `data/municipal_verified_records.json` | **1.345 registros** | 1.345 URLs HTTPS oficiales con SHA-256 en origen (215 comunas). |
| **Referencias BCN Remotas** | `dashboard/status_data.json` | **5.881 registros** | Enlaces canónicos a LeyChile / BCN. |

---

## 3. Detalle Territorial de Comunas con Brecha Normativa (1–3 normas)

- **1 norma (5 comunas):** Pencahue, Cholchol, Antártica
- **2 normas (10 comunas):** Camiña, Paiguano, Pumanque, Timaukel
- **3 normas (6 comunas):** San Rafael, Ñiquén, Nueva Imperial, Máfil, Chaitén

---

## 4. Diagnóstico de Brecha para la Fase 4 (Asistente RAG)

1. **Distinción entre Catastro y Corpus Textual RAG:**
   El catastro actual es un **catálogo referencial validado** (sabe dónde está cada ordenanza, su fecha, materia, número, URL y huella digital SHA-256). No es un almacén de texto completo descargado localmente.
2. **Requisito para RAG:**
   No se deben descargar las 7.226 normas masivamente de forma indiscriminada. El plan estipula iniciar con el **Paquete 05 (Lote piloto de 50 a 100 documentos)** para validar el pipeline de extracción por página, OCR selectivo, chunking y evaluación de respuestas antes de cualquier escalamiento.

---

## 5. Manifiesto de Archivos Físicos Locales en `data/official_pdfs/`

```text
- `_iqu_n_COBROS-2021_2021-01-01.pdf` (1.207.463 bytes)
- `_iqu_n_PRC-2024_2024-01-01.pdf` (306.510 bytes)
- `bulnes_norma_oficial.pdf` (123.569 bytes)
- `cabo_de_hornos_194_1988-02-08.pdf` (23.791 bytes)
- `cabo_de_hornos_473_2024-08-23.pdf` (7.227.399 bytes)
- `canela_norma_oficial.pdf` (165.227 bytes)
- `chait_n_490_1990-10-18.pdf` (23.929 bytes)
- `chill_n_viejo_1838_2009-11-14.pdf` (23.998 bytes)
- `chill_n_viejo_1_1995-01-26.pdf` (23.749 bytes)
- `cholchol_norma_oficial.pdf` (122.613 bytes)
- `diego de almagro_norma_oficial.pdf` (144.075 bytes)
- `donihue_norma_oficial.pdf` (61.937 bytes)
- `freirina_3095_2019-11-04.pdf` (23.995 bytes)
- `freirina_4_2017-10-18.pdf` (23.860 bytes)
- `negrete_norma_oficial.pdf` (61.648 bytes)
- `nueva_imperial_401_1992-01-28.pdf` (54.767 bytes)
- `o_higgins_330_2024-07-19.pdf` (23.974 bytes)
- `o_higgins_877_2024-10-30.pdf` (47.819 bytes)
- `o_higgins_894_2024-12-21.pdf` (46.884 bytes)
- `palena_norma_oficial.pdf` (153.629 bytes)
- `puerto octay_norma_oficial.pdf` (122.273 bytes)
- `pumanque_290_2020-02-18.pdf` (26.176 bytes)
- `punitaqui_2369_2010-12-15.pdf` (46.540 bytes)
- `punitaqui_617_2004-08-26.pdf` (25.403 bytes)
- `rio negro_norma_oficial.pdf` (140.063 bytes)
- `santa juana_norma_oficial.pdf` (127.693 bytes)
```
