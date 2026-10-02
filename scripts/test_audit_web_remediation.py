"""Suite de pruebas de verificación para la remediación de la auditoría web P090.
Task ID: P090-AUD-WEB-20261002
Cubre la verificación de los hallazgos H01 a H11.
"""
import os
import csv
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Proyectos/P090 - Catastro Ordenanzas Municipales BCN")
DATA_DIR = REPO_ROOT / "data"
DASHBOARD_DIR = REPO_ROOT / "dashboard"

CANONICAL_MATERIAS = {
    "Aseo, Ornato y Gestión de Residuos",
    "Comercio, Vía Pública y Publicidad",
    "Convivencia Vecinal y Ruidos Molestos",
    "Derechos, Tarifas y Concesiones Municipales",
    "Medio Ambiente, Humedales y Tenencia Responsable",
    "Obras, Urbanismo y Espacio Público",
    "Organización Interna y Participación Ciudadana",
    "Tránsito, Transporte y Estacionamientos",
    "Seguridad Ciudadana y Prevención"
}

class TestAuditWebRemediation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        status_file = DASHBOARD_DIR / "status_data.json"
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                cls.status_data = json.load(f)
        else:
            cls.status_data = {}

        raw_comunas = cls.status_data.get("comunas", [])
        if isinstance(raw_comunas, list):
            cls.comunas_by_name = {c.get("comuna"): c for c in raw_comunas}
        else:
            cls.comunas_by_name = raw_comunas

        municipal_file = DATA_DIR / "municipal_verified_records.json"
        if municipal_file.exists():
            with open(municipal_file, "r", encoding="utf-8") as f:
                cls.municipal_records = json.load(f)
        else:
            cls.municipal_records = []

        quarantine_file = DATA_DIR / "quarantined_records.json"
        if quarantine_file.exists():
            with open(quarantine_file, "r", encoding="utf-8") as f:
                q_data = json.load(f)
                if isinstance(q_data, dict):
                    cls.quarantine_records = q_data.get("records", [])
                else:
                    cls.quarantine_records = q_data
        else:
            cls.quarantine_records = []

    def test_h01_attribution_exclusive(self):
        """H01: Norma 1022727 (Ruidos Talcahuano) debe estar atribuida exclusivamente a Talcahuano y NUNCA a Talca."""
        self.assertTrue(self.status_data, "status_data.json no debe estar vacío")
        
        # Verificar registros comunales en status_data
        talca_records = self.comunas_by_name.get("Talca", {}).get("ordenanzas", [])
        talcahuano_records = self.comunas_by_name.get("Talcahuano", {}).get("ordenanzas", [])
        
        def has_1022727(records):
            for r in records:
                target = str(r.get("target_url") or "")
                rdf = str(r.get("rdf_url") or "")
                url = str(r.get("url") or "")
                if "1022727" in target or "1022727" in rdf or "1022727" in url:
                    return True
            return False

        self.assertFalse(has_1022727(talca_records), "H01: La norma 1022727 no debe pertenecer a Talca")
        self.assertTrue(has_1022727(talcahuano_records), "H01: La norma 1022727 debe pertenecer a Talcahuano")

    def test_h01_no_substring_false_positives(self):
        """H01: No deben existir atribuciones cruzadas por coincidencia de subcadena (e.g. Rauco en Arauco, Pica en Chépica)."""
        # Pares conocidos de subcadena errónea
        forbidden_pairs = [
            ("Pica", "Chépica"),
            ("Rauco", "Arauco"),
            ("Florida", "La Florida"),
            ("Lota", "Quillota"),
            ("Paine", "Torres del Paine"),
            ("Calera", "Calera de Tango"),
            ("Pinto", "María Pinto"),
            ("El Carmen", "Alto del Carmen"),
            ("Chillán", "Chillán Viejo")
        ]
        
        for shorter, longer in forbidden_pairs:
            longer_recs = self.comunas_by_name.get(longer, {}).get("ordenanzas", [])
            longer_urls = {r.get("url") for r in longer_recs if r.get("url")}
            
            shorter_recs = self.comunas_by_name.get(shorter, {}).get("ordenanzas", [])
            for r in shorter_recs:
                url = r.get("url")
                # Si una URL está en ambas comunas, verificar si es un error de subcadena
                if url and url in longer_urls:
                    # Si el organismo oficial es claramente el del nombre más largo, no puede estar en shorter
                    org = str(r.get("organismo", "")).lower()
                    self.assertNotIn(longer.lower(), org, f"H01: Documento de {longer} ({url}) asignado incorrectamente a {shorter}")

    def test_h02_documentary_admissibility_and_quarantine(self):
        """H02: Planes comunales, manuales de procedimientos y formularios administrativos deben estar en cuarentena y fuera de ordenanzas activas."""
        inadmissible_patterns = [
            r"plan\s+comunal\s+de\s+seguridad",
            r"manual\s+de\s+procedimiento",
            r"formulario\s+de\s+solicitud",
            r"plan\s+de\s+acci[oó]n\s+comunal\s+de\s+cambio\s+clim[aá]tico"
        ]
        
        # En status_data activo
        for comuna, cdata in self.comunas_by_name.items():
            for r in cdata.get("ordenanzas", []):
                titulo = r.get("titulo", "").lower()
                for pat in inadmissible_patterns:
                    self.assertIsNone(re.search(pat, titulo), f"H02: Instrumento no admisible encontrado en comuna {comuna}: {r.get('titulo')}")

        # Cuarentena debe existir y tener registros con motivo
        self.assertGreater(len(self.quarantine_records), 0, "H02: Debe existir archivo de cuarentena con registros excluidos")
        for q in self.quarantine_records:
            has_reason = ("motivo_cuarentena" in q) or ("quarantine_reason" in q)
            self.assertTrue(has_reason, "H02: Registro en cuarentena debe especificar motivo_cuarentena o quarantine_reason")

    def test_h03_taxonomy_canonical_axes(self):
        """H03: Todos los registros deben alinearse a los 9 ejes temáticos canónicos."""
        for comuna, cdata in self.comunas_by_name.items():
            for r in cdata.get("ordenanzas", []):
                materia = r.get("materia")
                self.assertIn(materia, CANONICAL_MATERIAS, f"H03: Materia '{materia}' en comuna {comuna} no pertenece a los 9 ejes canónicos")

    def test_h04_indicators_no_100_percent_verified(self):
        """H04: No debe existir el literal engañoso '100% Verificado' en los resúmenes de cobertura."""
        summary = self.status_data.get("summary_rows", [])
        for row in summary:
            cobertura = str(row.get("cobertura", ""))
            self.assertNotIn("100% Verificado", cobertura, f"H04: '100% Verificado' encontrado en resumen para {row.get('comuna')}")

        # Comprobar también en index.html
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("100% Verificado", index_html, "H04: '100% Verificado' encontrado como texto estático en index.html")

    def test_h08_comparator_renamed(self):
        """H08: La tarjeta no debe prometer un 'Comparador de Tarifas' automatizado inexistente."""
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.assertNotIn(">Comparador de Tarifas<", index_html, "H08: Texto '>Comparador de Tarifas<' aún presente en index.html")
        self.assertIn("Explorar Normativa Tarifaria", index_html, "H08: Falta nuevo rótulo 'Explorar Normativa Tarifaria' en index.html")

    def test_h09_accessibility_chat_and_modals(self):
        """H09: El botón de chat y los modales deben tener atributos de accesibilidad WCAG mínimos."""
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        # Chat toggle
        self.assertRegex(index_html, r'<button[^>]*id="chat-toggle-btn"[^>]*aria-label=', "H09: #chat-toggle-btn debe tener aria-label")
        # Modales con role="dialog" o aria-modal
        self.assertIn('role="dialog"', index_html, "H09: Debe haber modales con role='dialog'")

    def test_h10_responsive_no_overflow_390px(self):
        """H10: No deben existir anchos fijos mayores a 380px en reglas móviles que causen scroll horizontal en 390px."""
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("min-width: 400px", index_html, "H10: 'min-width: 400px' produce desborde horizontal en viewport de 390px")

    def test_h05_download_counts_reconciled(self):
        """H05: Las cifras de descarga deben reconciliarse exactamente con el universo de normas publicado."""
        csv_file = DASHBOARD_DIR / "descargas" / "catastro_ordenanzas_nacional_2026.csv"
        self.assertTrue(csv_file.exists(), "H05: Archivo CSV de descarga debe existir")
        
        with open(csv_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total_metrics = self.status_data.get("metrics", {}).get("total_ordenanzas", 0)
        self.assertEqual(len(rows), total_metrics, f"H05: El CSV descargable ({len(rows)}) debe coincidir con total_ordenanzas ({total_metrics})")

    def test_h06_coverage_period_and_cutoff_declared(self):
        """H06: El período de cobertura contemporáneo (2021–2026) y la fecha de corte deben estar explícitamente declarados."""
        scope = self.status_data.get("public_scope", {})
        self.assertIn("corte_fecha", scope, "H06: public_scope debe declarar corte_fecha")
        self.assertIn("Octubre 2026", scope["corte_fecha"], "H06: Fecha de corte debe ser Octubre 2026")
        self.assertIn("2021–2026", scope.get("periodo_cobertura_reciente", ""), "H06: Período reciente debe declarar 2021–2026")

    def test_h07_source_links_precision(self):
        """H07: Los enlaces de fuentes deben distinguir LeyChile BCN, decretos municipales y metadatos RDF."""
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn("Ver en BCN LeyChile", index_html, "H07: Debe rotular enlace hacia LeyChile")
        self.assertIn("Abrir Decreto Municipal (PDF)", index_html, "H07: Debe rotular enlaces a PDF municipal con tipo correcto")
        self.assertIn("Datos RDF / JSON", index_html, "H07: Debe rotular metadatos de datos.bcn.cl con su formato real")

    def test_h11_download_architecture_clarity(self):
        """H11: Debe diferenciar claramente la descarga directa abierta de la solicitud institucional con propósito."""
        index_html = (DASHBOARD_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn("descargar_csv_microdatos", index_html, "H11: Debe ofrecer descarga directa de microdatos CSV")
        self.assertIn("abrir_solicitud_excel", index_html, "H11: Debe rotular solicitud de planilla Excel")
        self.assertIn("abrir_solicitud_zip", index_html, "H11: Debe rotular solicitud de paquete ZIP")

if __name__ == "__main__":
    unittest.main()
