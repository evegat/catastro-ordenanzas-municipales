"""Regresión del inventario: cambia el corpus sin mantener cifras manuales."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import generate_document_inventory as inventory


class InventoryTest(unittest.TestCase):
    def test_dynamic_counts_and_mismatched_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            dashboard = root / "dashboard"
            data.mkdir()
            dashboard.mkdir()
            snapshot = {
                "metrics": {"total_ordenanzas": 3, "comunas_con_datos": 1,
                            "total_comunas": 2, "ordenanzas_bcn": 1,
                            "ordenanzas_municipales_verificadas": 2},
                "comunas": [
                    {"comuna": "Con registros", "ordenanzas": [
                        {"fuente": "BCN"}, {"fuente": "Municipalidad"},
                        {"fuente": "BCN / LeyChile"}]},
                    {"comuna": "Sin registros", "ordenanzas": []}],
            }
            source = dashboard / "status_data.json"
            source.write_text(json.dumps(snapshot), encoding="utf-8")
            (data / "municipal_verified_records.json").write_text(
                json.dumps({"count": 2, "records": [
                    {"comuna": "Con registros", "verification": {"sha256": "abc"}},
                    {"comuna": "Con registros", "verification": {}}]}), encoding="utf-8")
            with patch.object(inventory, "DATA_DIR", data), \
                 patch.object(inventory, "DASHBOARD_DIR", dashboard), \
                 patch.object(sys, "argv", ["inventory", "--output-dir", str(root),
                                            "--datasets-dir", str(root / "absent")]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(inventory.run(), 0)
                manifest = json.loads((data / "document_inventory_manifest.json").read_text())
                self.assertEqual(manifest["conclusions"]["canonical_total_records"], 3)
                self.assertEqual(manifest["conclusions"]["municipal_verified_remote_records"], 2)
                self.assertEqual(manifest["municipal_verified"]["unique_sha256_count"], 1)
                self.assertEqual(manifest["status_data"]["comunas_baja_densidad_1_3_count"], 1)
                snapshot["metrics"]["total_ordenanzas"] = 100
                source.write_text(json.dumps(snapshot), encoding="utf-8")
                self.assertEqual(inventory.run(), 1)

    def test_only_pdf_files_with_pdf_header_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "nested/valid.pdf").write_bytes(b"%PDF-1.7\n")
            (root / "error.pdf").write_text("<html>Error</html>")
            (root / "readme.txt").write_text("Not a PDF")
            result = inventory.inspect_physical_pdfs(root)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["files"][0]["filename"], "nested/valid.pdf")


if __name__ == "__main__":
    unittest.main()
