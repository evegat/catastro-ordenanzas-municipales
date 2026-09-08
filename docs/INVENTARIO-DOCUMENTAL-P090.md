# Inventario Documental y Conciliación de Cifras — P090

- **Task ID:** `P090-20260908-plan-publico-02`
- **Fecha de corte:** 2026-09-08
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

- **1 norma (5 comunas):** Pencahue, Hualpén, Cholchol, O Higgins, Antártica
- **2 normas (10 comunas):** Camiña, Paiguano, Tiltil, Pumanque, Chillán Viejo, Alto Biobío, Nueva Imperial, Lanco, Chaitén, Timaukel
- **3 normas (6 comunas):** Freirina, Punitaqui, San Rafael, Ñiquén, Máfil, Mariquina

---

## 4. Diagnóstico de Brecha para la Fase 4 (Asistente RAG)

1. **Distinción entre Catastro y Corpus Textual RAG:**
   El catastro actual es un **catálogo referencial validado** (sabe dónde está cada ordenanza, su fecha, materia, número, URL y huella digital SHA-256). No es un almacén de texto completo descargado localmente.
2. **Requisito para RAG:**
   No se deben descargar las 7.226 normas masivamente de forma indiscriminada. El plan estipula iniciar con el **Paquete 05 (Lote piloto de 50 a 100 documentos)** para validar el pipeline de extracción por página, OCR selectivo, chunking y evaluación de respuestas antes de cualquier escalamiento.

---

## 5. Manifiesto de Archivos Físicos Locales en `data/official_pdfs/`

```text
- `bulnes_norma_oficial.pdf` (123.569 bytes)
- `canela_norma_oficial.pdf` (165.227 bytes)
- `cholchol_norma_oficial.pdf` (122.613 bytes)
- `diego de almagro_norma_oficial.pdf` (144.075 bytes)
- `donihue_norma_oficial.pdf` (61.937 bytes)
- `negrete_norma_oficial.pdf` (61.648 bytes)
- `palena_norma_oficial.pdf` (153.629 bytes)
- `puerto octay_norma_oficial.pdf` (122.273 bytes)
- `rio negro_norma_oficial.pdf` (140.063 bytes)
- `santa juana_norma_oficial.pdf` (127.693 bytes)
```
