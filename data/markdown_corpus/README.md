# Corpus Markdown de Ordenanzas Municipales de Chile (P090)

Repositorio estructurado en texto plano Markdown (`.md`) para investigación empírica, análisis de políticas públicas y asistentes RAG jurídicos a costo $0.

## Métricas del Corpus

- **Total de Documentos:** 7321
- **Documentos con Texto Completo Extraído (MarkItDown):** 359
- **Cobertura Territorial:** 346 / 346 comunas de Chile (100%)
- **Estandarización:** Frontmatter YAML compatible con Schema.org / Dublin Core en el 100% de los archivos.

## Estructura de Directorios

```
data/markdown_corpus/
  ├── {region_id}_{region}/
  │     └── {comuna}/
  │           └── {fecha}_{numero}.md
  ├── corpus_manifest.json
  └── README.md
```

## Ejemplo de Documento

Cada archivo cuenta con encabezado YAML estructurado para consulta programática directa por agentes de IA:

```yaml
---
id: "p090_chillan_viejo_1838_2009_11_14"
comuna: "Chillán Viejo"
region: "Ñuble"
numero: "1838"
fecha: "2009-11-14"
titulo: "Dicta Ordenanza sobre Trabajos en Beneficio de la Comunidad..."
materia: "Seguridad y Convivencia"
fuente: "Diario Oficial / BCN"
target_url: "https://nuevo.leychile.cl/..."
sha256: "8701f5111bb765b..."
extraction_method: "markitdown_pdf_extract"
---
```
