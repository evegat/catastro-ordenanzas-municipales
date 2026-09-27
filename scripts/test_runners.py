"""Prueba lanzadores en copias temporales, sin crawler real, red ni LM Studio."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(SHELL, "PowerShell requerido")
class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p090-runner-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        (self.root / "src").mkdir()
        for name in ("run_local_crawler.ps1", "run_sinim_discovery.ps1"):
            shutil.copy2(ROOT / "scripts" / name, self.root / "scripts" / name)

    def run_script(self, name, *args):
        return subprocess.run(
            [SHELL, "-NoProfile", "-File", str(self.root / "scripts" / name), *args],
            capture_output=True, timeout=25,
        )

    def fake_crawler(self, exit_code=0):
        (self.root / "src/continuous_commune_crawler.py").write_text(
            "from pathlib import Path\n"
            "p = Path('calls.txt')\n"
            "p.write_text(p.read_text() + 'call\\n' if p.exists() else 'call\\n')\n"
            f"raise SystemExit({exit_code})\n", encoding="utf-8")

    def test_missing_dependencies_fail_before_work(self):
        for name in ("run_local_crawler.ps1", "run_sinim_discovery.ps1"):
            result = self.run_script(name, "-ValidateOnly")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"ausente", result.stderr.lower())
        self.assertFalse((self.root / "logs").exists())
        self.assertFalse((self.root / "data").exists())

    def test_validate_only_never_invokes_crawler(self):
        self.fake_crawler()
        self.assertEqual(self.run_script("run_local_crawler.ps1", "-ValidateOnly").returncode, 0)
        self.assertFalse((self.root / "calls.txt").exists())

    def test_success_stops_at_batch_limit(self):
        self.fake_crawler()
        result = self.run_script("run_local_crawler.ps1", "-MaxBatches", "2", "-PauseMinutes", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "calls.txt").read_text().splitlines(), ["call", "call"])

    def test_repeated_failure_stops_after_two_attempts(self):
        self.fake_crawler(exit_code=1)
        result = self.run_script("run_local_crawler.ps1", "-MaxBatches", "10", "-PauseMinutes", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len((self.root / "calls.txt").read_text().splitlines()), 2)

    def test_completed_queue_stops_immediately(self):
        self.fake_crawler(exit_code=3)
        result = self.run_script("run_local_crawler.ps1", "-MaxBatches", "10", "-PauseMinutes", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len((self.root / "calls.txt").read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
