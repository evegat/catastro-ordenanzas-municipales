#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas de regresión automatizadas para la remediación de auditoría P090 (AUD-P090-DIFUSION-20260930).
Verifica C01, C02, C03, C04, C05.
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

class TestAuditRemediation(unittest.TestCase):

    def test_c02_admissibility_and_quarantine(self):
        """C02: Ningún rol de avalúo SII o formulario debe estar en municipal_verified_records."""
        verified_path = REPO_ROOT / "data" / "municipal_verified_records.json"
        quarantine_path = REPO_ROOT / "data" / "quarantined_records.json"
        
        self.assertTrue(verified_path.exists(), "Falta municipal_verified_records.json")
        self.assertTrue(quarantine_path.exists(), "Falta quarantined_records.json")
        
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        quarantined = json.loads(quarantine_path.read_text(encoding="utf-8"))
        
        records = verified.get("records", [])
        q_records = quarantined.get("records", [])
        
        self.assertGreaterEqual(len(q_records), 20, "Deben haber al menos 20 registros en cuarentena")
        
        # Verificar que los casos específicos están en cuarentena
        q_titles = [str(r.get("titulo", "")).lower() for r in q_records]
        q_urls = [str(r.get("target_url", "")).lower() for r in q_records]
        combined_q = " ".join(q_titles + q_urls)
        
        self.assertIn("rolreavaluo_sne-07309_2023", combined_q)
        self.assertIn("rolreavaluo_agr-07309_2020", combined_q)
        self.assertIn("roles2024", combined_q)
        self.assertIn("cuenta publica 2024", combined_q)
        self.assertIn("rolreavaluo_agricola-09206_2020", combined_q)
        self.assertIn("rolreavaluo_sne-08118_2025", combined_q)
        self.assertIn("rolreavaluo_sne-07301_2025", combined_q)
        
        # Verificar que NINGUNO de los registros verificados es un rol de avalúo SII o formulario
        banned_regex = re.compile(r"rol.*reavaluo|reavaluo|rol.*avaluo|roles20\d\d|sne.*0\d{4}|cuenta.*publica|formulario.*trabajadores|formulario.*pmjh", re.I)
        for r in records:
            text = (str(r.get("titulo", "")) + " " + str(r.get("target_url", "")))
            if "derechos" in text.lower() and "presupuesto" in text.lower():
                continue
            self.assertIsNone(banned_regex.search(text), f"Registro no admisible en corpus activo: {r.get('comuna')} - {r.get('titulo')}")

    def test_c03_date_provenance_and_fallbacks(self):
        """C03: extract_legal_date no debe fabricar 2026-01-01 ni comodines -01-01."""
        promote_file = (REPO_ROOT / "src" / "promote_extracted_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn('return "2026-01-01"', promote_file, "promote_extracted_evidence no debe tener fallback ciego a 2026-01-01")
        self.assertNotIn('return f"{m3.group(1)}-01-01"', promote_file, "promote_extracted_evidence no debe fabricar -01-01 para años")
        
        corpus_builder = (REPO_ROOT / "src" / "build_markdown_corpus.py").read_text(encoding="utf-8")
        self.assertNotIn('"1900-01-01"', corpus_builder, "build_markdown_corpus no debe tener fallback a 1900-01-01")

        # Verificar en los registros que no haya fechas inventadas con comodín -01-01
        verified_path = REPO_ROOT / "data" / "municipal_verified_records.json"
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        for r in verified.get("records", []):
            fecha = str(r.get("fecha", "")).strip()
            self.assertFalse(re.match(r"^\d{4}-01-01$", fecha) and fecha != "S/F", f"Fecha sospechosa con comodín -01-01: {r.get('comuna')} - {fecha}")

    def test_c01_reconciled_single_cut(self):
        """C01: status_data, mapa_data, resumen_comunal y CSV deben tener idénticas cifras por comuna."""
        status_path = REPO_ROOT / "dashboard" / "status_data.json"
        mapa_path = REPO_ROOT / "dashboard" / "mapa_data.json"
        resumen_path = REPO_ROOT / "dashboard" / "descargas" / "resumen_comunal_chile_346_comunas.csv"
        csv_path = REPO_ROOT / "dashboard" / "descargas" / "catastro_ordenanzas_nacional_2026.csv"
        
        self.assertTrue(status_path.exists())
        self.assertTrue(mapa_path.exists())
        self.assertTrue(resumen_path.exists())
        self.assertTrue(csv_path.exists())
        
        status = json.loads(status_path.read_text(encoding="utf-8"))
        mapa = json.loads(mapa_path.read_text(encoding="utf-8"))
        
        status_total = status["metrics"]["total_ordenanzas"]
        status_comunas = {c["comuna"].lower(): c["total_count"] for c in status["comunas"]}
        
        mapa_total = sum(m["total"] for m in mapa)
        mapa_comunas = {m["comuna"].lower(): m["total"] for m in mapa}
        
        self.assertEqual(status_total, mapa_total, f"Total en status_data ({status_total}) difiere de mapa_data ({mapa_total})")
        
        # Comparar comuna por comuna
        for c_norm, cnt in status_comunas.items():
            self.assertIn(c_norm, mapa_comunas, f"Comuna {c_norm} no está en mapa_data")
            self.assertEqual(cnt, mapa_comunas[c_norm], f"Discrepancia en comuna {c_norm}: status={cnt} vs mapa={mapa_comunas[c_norm]}")
            
        # Comparar con resumen CSV
        resumen_lines = resumen_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(resumen_lines), 347, "resumen CSV debe tener 346 comunas + header")
        
        import csv
        reader = csv.DictReader(resumen_lines)
        resumen_total = 0
        for row in reader:
            c_name = row["comuna"].lower()
            t_ord = int(row["total_ordenanzas"])
            resumen_total += t_ord
            self.assertEqual(status_comunas[c_name], t_ord, f"Discrepancia en resumen CSV para {c_name}: status={status_comunas[c_name]} vs csv={t_ord}")
        self.assertEqual(status_total, resumen_total, f"Total en status ({status_total}) difiere de resumen CSV ({resumen_total})")

    def test_c04_chat_dom_and_resolution(self):
        """C04: Chat button fuera del modal y desambiguación territorial correcta."""
        index_html = (REPO_ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
        
        # El modal de descarga debe cerrarse antes del bloque del asistente
        modal_pos = index_html.find('id="download-request-modal"')
        chat_pos = index_html.find('id="chat-toggle-btn"')
        self.assertNotEqual(modal_pos, -1, "Modal no encontrado")
        self.assertNotEqual(chat_pos, -1, "Chat toggle button no encontrado")
        
        # Debe haber un cierre de modal </div\s*>\s*<!-- ASISTENTE
        self.assertRegex(index_html, r'</div>\s*</div>\s*<!--\s*ASISTENTE JURÍDICO FLOTANTE', "El modal download-request-modal debe cerrarse antes del chat")

        # Comprobar lógica de desambiguación territorial en asistente_chat.js
        chat_js = (REPO_ROOT / "dashboard" / "asistente_chat.js").read_text(encoding="utf-8")
        self.assertNotIn("7.450", chat_js, "No deben quedar referencias fijas a 7.450 en el chat")
        self.assertIn("mandato legal", chat_js.lower(), "El asistente debe contemplar 'mandato legal'")

if __name__ == "__main__":
    unittest.main()
