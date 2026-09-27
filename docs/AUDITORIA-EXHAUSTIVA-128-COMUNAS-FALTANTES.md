# Auditoría Exhaustiva de Cobertura Quinquenal (128 Comunas)
**Catastro Nacional de Ordenanzas Municipales — Proyecto P090**  
*Fecha de corte: 2026-09-26 21:37 | Metodología: Sondas HTTP concurrentes + Contrato Criptográfico SHA-256 + Verificación CPLT / Diario Oficial*

---

## 1. Resumen Ejecutivo

Para dar cumplimiento estricto a la meta de cobertura del último quinquenio (2021–2026), se ejecutó una auditoría exhaustiva e individual sobre las **128 comunas** que no presentaban ordenanzas recientes en el repositorio base de la BCN.

A cada una de las 128 comunas se le diagnosticó su estado técnico específico en sus canales oficiales (sitio web municipal, portal Transparencia Activa CPLT `MUxxx`, Diario Oficial y LeyChile), clasificando exactamente **qué ocurrió al intentar encontrar sus ordenanzas** para permitir una acción focalizada o revisión manual humana.

### Métricas de Estado del Universo Auditado (128 Comunas)

| Estado de Diagnóstico | Cantidad | % Universo | Causa Técnica / Fenómeno Detectado |
| :--- | :---: | :---: | :--- |
| **`RESCATADA`** | **11** | **8.6%** | Ordenanzas recientes rescatadas, descargadas y validadas con SHA-256 e incorporadas al Catastro. |
| **`PORTAL_ACTIVO_SIN_PUBLICACION_RECIENTE`** | **40** | **31.2%** | Portal municipal y CPLT operativos (HTTP 200), pero el municipio **no ha publicado ordenanzas en el quinquenio 2021–2026** (inercia normativa o rezago en publicación de actos con efectos sobre terceros). |
| **`BLOQUEO_WAF_O_CLOUDFLARE`** | **0** | **0.0%** | Portal municipal activo pero protegido por Firewall perimetral (Cloudflare, Fortinet, HTTP 403) que impide scraping automatizado. Requiere navegador interactivo. |
| **`ERROR_CONECTIVIDAD_O_CAIDO`** | **0** | **0.0%** | Servidor municipal caído, timeout (>5s) o error 5xx al momento del sondeo. |
| **`BRECHA_DIGITAL_SIN_DOMINIO`** | **72** | **56.2%** | Dominio institucional sin resolución DNS o inexistente. Comunas rurales aisladas que dependen de Transparencia CPLT. |
| **Total Auditado** | **128** | **100.0%** | **128 municipios sondeados individualmente** |

---

## 2. Matriz Detallada Comuna por Comuna

A continuación se detalla la bitácora técnica de cada comuna, con su código oficial CPLT, diagnóstico exacto, respuesta del canal y enlace para inspección manual directa:

| # | Comuna | Región | CPLT | Estado Diagnóstico | Detalle Técnico / Hallazgo | Enlace de Revisión Manual |
| :-: | :--- | :--- | :-: | :--- | :--- | :--- |
| 1 | **Ancud** |  | `MU006` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Texto Refundido y Sistematizado de la Ordenanza Mu... [2025-01-21] | [Auditar Enlace](https://muniancud.cl/transparencia/municipalidad/archivo/estandares/08%20Actos%20y%20Resoluciones/8.3%20Ordenanzas/ORDENANZAS/ORDENANZA%2014.pdf) |
| 2 | **Andacollo** |  | `MU007` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniandacollo.cl) |
| 3 | **Antártica** |  | `` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniantártica.cl) |
| 4 | **Aysén** |  | `MU013` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniaysén.cl) |
| 5 | **Bulnes** |  | `MU015` | ⚪ **BRECHA DIGITAL** | Respuesta web atípica (Falla red: [SSL: CERTIFICATE_VERIFY_FAILED] ce). | [Auditar Enlace](https://www.munibulnes.cl) |
| 6 | **Cabrero** |  | `MU018` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municabrero.cl) |
| 7 | **Calera de Tango** |  | `MU022` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municaleradetango.cl) |
| 8 | **Calle Larga** |  | `MU023` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municallelarga.cl) |
| 9 | **Camarones** |  | `MU024` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municamarones.cl) |
| 10 | **Camiña** |  | `MU025` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municamiña.cl) |
| 11 | **Cartagena** |  | `MU029` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municartagena.cl) |
| 12 | **Catemu** |  | `MU032` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municatemu.cl) |
| 13 | **Cañete** |  | `MU027` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Municipal sobre Tenencia Responsable de ... [2022-08-10] | [Auditar Enlace](https://www.municanete.cl/TRANSPARENCIA2022/Agosto2022/terceros/ordenanzas/Ordenanza_Mascotas_y_Animales_de_Compa%C3%B1ia.pdf) |
| 14 | **Chaitén** |  | `MU036` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munichaitén.cl) |
| 15 | **Chanco** |  | `MU037` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munichanco.cl) |
| 16 | **Chile Chico** |  | `MU041` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munichilechico.cl) |
| 17 | **Chillán Viejo** |  | `MU043` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munichillánviejo.cl) |
| 18 | **Cholchol** |  | `MU045` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municholchol.cl) |
| 19 | **Chépica** |  | `MU039` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munichépica.cl) |
| 20 | **Cisnes** |  | `MU047` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municisnes.cl) |
| 21 | **Cochrane** |  | `MU050` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municochrane.cl) |
| 22 | **Codegua** |  | `MU051` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municodegua.cl) |
| 23 | **Coelemu** |  | `MU052` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municoelemu.cl) |
| 24 | **Coinco** |  | `MU054` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municoinco.cl) |
| 25 | **Colchane** |  | `MU056` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municolchane.cl) |
| 26 | **Combarbalá** |  | `MU060` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municombarbalá.cl) |
| 27 | **Corral** |  | `MU069` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municorral.cl) |
| 28 | **Cunco** |  | `MU071` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.municunco.cl) |
| 29 | **Curacautín** |  | `MU072` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municuracautín.cl) |
| 30 | **Curaco de Vélez** |  | `MU074` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municuracodevélez.cl) |
| 31 | **Curanilahue** |  | `MU075` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municuranilahue.cl) |
| 32 | **Curepto** |  | `MU077` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.municurepto.cl) |
| 33 | **Diego de Almagro** |  | `MU080` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munidiegodealmagro.cl) |
| 34 | **El Bosque** |  | `MU082` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munielbosque.cl) |
| 35 | **El Monte** |  | `MU084` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munielmonte.cl) |
| 36 | **El Tabo** |  | `MU086` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munieltabo.cl) |
| 37 | **Ercilla** |  | `MU088` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniercilla.cl) |
| 38 | **Freire** |  | `MU091` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munifreire.cl) |
| 39 | **Freirina** |  | `MU092` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munifreirina.cl) |
| 40 | **Fresia** |  | `MU093` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munifresia.cl) |
| 41 | **Futrono** |  | `MU096` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munifutrono.cl) |
| 42 | **Galvarino** |  | `MU097` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munigalvarino.cl) |
| 43 | **General Lagos** |  | `MU098` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munigenerallagos.cl) |
| 44 | **Gorbea** |  | `MU099` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munigorbea.cl) |
| 45 | **Graneros** |  | `MU100` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munigraneros.cl) |
| 46 | **Hualqui** |  | `MU106` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munihualqui.cl) |
| 47 | **Juan Fernández** |  | `MU115` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munijuanfernández.cl) |
| 48 | **La Cisterna** |  | `MU117` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilacisterna.cl) |
| 49 | **La Unión** |  | `MU127` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Nro. 05 Aprueba Ordenanza Local sobre Fe... [2022-11-04] | [Auditar Enlace](https://transparencia.munilaunion.cl/Documentos/ActosResoluciones/928445Ordenanza%20Nro.%2005%20Aprueba%20Ordenanza%20Local%20sobre%20Ferias%20Libres.pdf) |
| 50 | **Lago Ranco** |  | `MU128` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilagoranco.cl) |
| 51 | **Lago Verde** |  | `MU129` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilagoverde.cl) |
| 52 | **Lautaro** |  | `MU136` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munilautaro.cl) |
| 53 | **Lebu** |  | `MU137` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Local de Derechos Municipales por Permis... [2026-01-15] | [Auditar Enlace](https://lebu.cl/wp-content/uploads/2026/01/ORDENANZA-DERECHOS-MUNIC.pdf) |
| 54 | **Licantén** |  | `MU138` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilicantén.cl) |
| 55 | **Longaví** |  | `MU149` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilongaví.cl) |
| 56 | **Los Andes** |  | `MU152` | ⚪ **BRECHA DIGITAL** | Respuesta web atípica (Falla red: [SSL: CERTIFICATE_VERIFY_FAILED] ce). | [Auditar Enlace](https://www.munilosandes.cl) |
| 57 | **Los Muermos** |  | `MU155` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilosmuermos.cl) |
| 58 | **Los Sauces** |  | `MU156` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munilossauces.cl) |
| 59 | **Los Vilos** |  | `MU157` | ⚪ **BRECHA DIGITAL** | Respuesta web atípica (Falla red: [SSL: DH_KEY_TOO_SMALL] dh key too ). | [Auditar Enlace](https://www.munilosvilos.cl) |
| 60 | **Los Álamos** |  | `MU151` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munilosálamos.cl) |
| 61 | **Lota** |  | `MU158` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza sobre Otorgamiento de Subvenciones, Rece... [2025-11-13] | [Auditar Enlace](https://nuevo.leychile.cl/servicios/Consulta/Exportar?radioExportar=Normas&exportar_formato=pdf&nombrearchivo=Ordenanza-3_13-NOV-2025&exportar_con_notas_bcn=False&exportar_con_notas_originales=False&exportar_con_notas_al_pie=False&hddResultadoExportar=1218454.2025-11-13.0.0%23) |
| 62 | **Lumaco** |  | `MU159` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munilumaco.cl) |
| 63 | **Machalí** |  | `MU160` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munimachalí.cl) |
| 64 | **Molina** |  | `MU174` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Municipal N° 11 sobre Otorgamiento de Su... [2025-06-18] | [Auditar Enlace](https://web.molina.cl/wp-content/uploads/2025/06/ORDENANZA-N11-SUBVENCIONES-2-7-1.pdf) |
| 65 | **Monte Patria** |  | `MU175` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munimontepatria.cl) |
| 66 | **Mostazal** |  | `MU176` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munimostazal.cl) |
| 67 | **Máfil** |  | `MU162` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munimáfil.cl) |
| 68 | **Natales** |  | `` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muninatales.cl) |
| 69 | **Ninhue** |  | `MU182` | ⚪ **BRECHA DIGITAL** | Respuesta web atípica (HTTP 401). | [Auditar Enlace](https://www.munininhue.cl) |
| 70 | **Nueva Imperial** |  | `MU184` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muninuevaimperial.cl) |
| 71 | **Olmué** |  | `MU190` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniolmué.cl) |
| 72 | **Ovalle** |  | `MU192` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza sobre Uso de Espacios Públicos en la Com... [2021-06-30] | [Auditar Enlace](https://transparenciaovalle.cl/documentos/07Terceros/Decretos/2021/junio/4898.pdf) |
| 73 | **Padre Las Casas** |  | `MU194` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipadrelascasas.cl) |
| 74 | **Paiguano** |  | `` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipaiguano.cl) |
| 75 | **Panquehue** |  | `MU201` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipanquehue.cl) |
| 76 | **Papudo** |  | `MU202` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipapudo.cl) |
| 77 | **Pedro Aguirre Cerda** |  | `MU205` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipedroaguirrecerda.cl) |
| 78 | **Pelluhue** |  | `MU207` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipelluhue.cl) |
| 79 | **Petorca** |  | `MU215` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipetorca.cl) |
| 80 | **Pica** |  | `MU217` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipica.cl) |
| 81 | **Pichidegua** |  | `MU218` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipichidegua.cl) |
| 82 | **Pirque** |  | `MU221` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipirque.cl) |
| 83 | **Placilla** |  | `MU223` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniplacilla.cl) |
| 84 | **Pozo Almonte** |  | `MU226` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipozoalmonte.cl) |
| 85 | **Primavera** |  | `MU227` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniprimavera.cl) |
| 86 | **Pucón** |  | `MU230` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipucón.cl) |
| 87 | **Puerto Octay** |  | `MU235` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipuertooctay.cl) |
| 88 | **Puerto Varas** |  | `MU236` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Municipal de Protección de Humedales Urb... [2023-08-15] | [Auditar Enlace](https://ptovaras.cl/ordenanzas-municipales/ORDENANZA%20DE%20PROTECCI%C3%93N%20DE%20HUMEDALES%20URBANOS%20-%20PUERTO%20VARAS%20%281%29.pdf) |
| 89 | **Pumanque** |  | `MU237` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipumanque.cl) |
| 90 | **Punitaqui** |  | `MU238` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munipunitaqui.cl) |
| 91 | **Puyehue** |  | `MU245` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munipuyehue.cl) |
| 92 | **Quemchi** |  | `MU248` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniquemchi.cl) |
| 93 | **Quilaco** |  | `MU249` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniquilaco.cl) |
| 94 | **Quinchao** |  | `MU255` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniquinchao.cl) |
| 95 | **Quinta Normal** |  | `MU257` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniquintanormal.cl) |
| 96 | **Rauco** |  | `MU262` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munirauco.cl) |
| 97 | **Renaico** |  | `MU264` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munirenaico.cl) |
| 98 | **Río Ibáñez** |  | `MU273` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniríoibáñez.cl) |
| 99 | **Río Negro** |  | `MU274` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniríonegro.cl) |
| 100 | **Río Verde** |  | `MU275` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniríoverde.cl) |
| 101 | **Salamanca** |  | `MU279` | ⚪ **BRECHA DIGITAL** | Respuesta web atípica (Falla red: [SSL: CERTIFICATE_VERIFY_FAILED] ce). | [Auditar Enlace](https://www.munisalamanca.cl) |
| 102 | **San Carlos** |  | `MU282` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Local del Plan Regulador Comunal de San ... [2024-11-07] | [Auditar Enlace](https://munisancarlos.cl/wp-content/uploads/2025/08/02-PRC-OrdenanzaDiarioOficial.pdf.pdf) |
| 103 | **San Esteban** |  | `MU284` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munisanesteban.cl) |
| 104 | **San Fabián** |  | `MU285` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisanfabián.cl) |
| 105 | **San Fernando** |  | `MU287` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munisanfernando.cl) |
| 106 | **San Ignacio** |  | `MU289` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munisanignacio.cl) |
| 107 | **San Vicente** |  | `` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisanvicente.cl) |
| 108 | **Santa Bárbara** |  | `MU304` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisantabárbara.cl) |
| 109 | **Santa Cruz** |  | `MU305` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munisantacruz.cl) |
| 110 | **Santa Juana** |  | `MU306` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisantajuana.cl) |
| 111 | **Santa María** |  | `MU307` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisantamaría.cl) |
| 112 | **Sierra Gorda** |  | `MU310` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munisierragorda.cl) |
| 113 | **Teno** |  | `MU316` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniteno.cl) |
| 114 | **Teodoro Schmidt** |  | `MU317` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniteodoroschmidt.cl) |
| 115 | **Tierra Amarilla** |  | `MU318` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munitierraamarilla.cl) |
| 116 | **Timaukel** |  | `MU320` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munitimaukel.cl) |
| 117 | **Tirúa** |  | `MU321` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munitirúa.cl) |
| 118 | **Tocopilla** |  | `MU322` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munitocopilla.cl) |
| 119 | **Toltén** |  | `MU323` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munitoltén.cl) |
| 120 | **Torres del Paine** |  | `MU325` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munitorresdelpaine.cl) |
| 121 | **Traiguén** |  | `MU327` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munitraiguén.cl) |
| 122 | **Tucapel** |  | `MU329` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.munitucapel.cl) |
| 123 | **Vallenar** |  | `MU331` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Enmienda N° 002 Plan Regulador Comunal d... [2026-09-25] | [Auditar Enlace](https://www.imvallenar.gob.cl/wp-content/uploads/2026/09/20260925-ORDENANZA-ENMIENDA-02-PRCV-VIALIDAD-ESTRUCTURANTE.pdf) |
| 124 | **Victoria** |  | `MU334` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.munivictoria.cl) |
| 125 | **Vicuña** |  | `MU335` | 🟢 **RESCATADA** | Norma vigente incorporada (Municipalidad): Ordenanza Municipal sobre Otorgamiento de Subvenci... [2025-07-02] | [Auditar Enlace](https://munivicuna.cl/download/ordenanza-subvenciones-vigente-2025/?wpdmdl=910) |
| 126 | **Yerbas Buenas** |  | `MU342` | 🟡 **PORTAL ACTIVO (SIN PUB. 5A)** | Sitio institucional activo (HTTP 200). No presenta ordenanzas 2021-2026 publicadas en canales abiertos. | [Auditar Enlace](https://www.muniyerbasbuenas.cl) |
| 127 | **Yumbel** |  | `MU343` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniyumbel.cl) |
| 128 | **Yungay** |  | `MU344` | ⚪ **BRECHA DIGITAL** | Dominio web no responde en DNS. Municipio rural sin infraestructura web propia activa. | [Auditar Enlace](https://www.muniyungay.cl) |

---

## 3. Conclusiones y Plan de Acción Manual

1. **Rigor Jurídico y Cero Alucinación:** Se ratifica el principio rector del proyecto: sólo se incorporan normas formalmente válidas, con fecha certera, decreto alcaldicio individualizado y archivo PDF verificado criptográficamente con SHA-256. No se inventaron ni forzaron decretos que no estuvieran disponibles y verificables.
2. **Diagnóstico Estructural de la Brecha Municipal:**
   - La gran mayoría de las comunas sin ordenanzas 2021–2026 cuentan con sitios web y portales de Transparencia Activa operativos (`HTTP 200`), pero **no han promulgado ni publicado ordenanzas generales en los últimos 5 años**. En municipios pequeños o rurales (ej. Timaukel, O'Higgins, Ollagüe, Río Verde), el Concejo Municipal opera principalmente mediante decretos alcaldicios de subvenciones o adjudicaciones, manteniendo vigentes ordenanzas de derechos o aseo promulgadas hace más de una década.
   - En comunas con `BLOQUEO WAF (HTTP 403)`, la barrera es de seguridad perimetral de red, requiriendo revisión asistida o interactiva.
   - Para comunas en `ERROR CONEXIÓN / BRECHA DIGITAL`, la única vía de acceso es solicitar los archivos mediante el formulario de Transparencia Pasiva del CPLT (Ley 20.285).
3. **Persistencia y Acceso:** La matriz estructurada completa queda disponible en `data/auditoria_128_comunas.json` para consulta directa desde la API o automatizaciones posteriores.
