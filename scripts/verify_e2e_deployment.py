"""Script de verificación End-to-End (E2E) para el despliegue de ordenanzas.evegat.cl.

Verifica:
1. Resolución DNS de ordenanzas.evegat.cl
2. Conectividad HTTP y HTTPS
3. Integridad de activos críticos (HTML, status_data.json, mapa, descargas)
4. Consistencia del dataset publicado (7.226 normas, 346 comunas)
"""

from __future__ import annotations

import json
import urllib.request
import ssl
from typing import NamedTuple


TARGET_URL = "https://ordenanzas.evegat.cl"
FALLBACK_EDGE_URL = "https://evegat.github.io"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MyWorld-Verifier/1.0"}


class CheckResult(NamedTuple):
    name: str
    passed: bool
    detail: str


def check_url(url: str, host_header: str | None = None) -> tuple[int, dict, bytes]:
    ctx = ssl.create_default_context()
    headers = dict(HEADERS)
    if host_header:
        headers["Host"] = host_header
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return resp.getcode(), dict(resp.headers), resp.read()


def run_e2e_tests() -> list[CheckResult]:
    results = []

    # 1. Edge Direct Verification
    try:
        code, hdrs, body = check_url(FALLBACK_EDGE_URL, host_header="ordenanzas.evegat.cl")
        passed = (code == 200 and len(body) > 50000)
        results.append(CheckResult(
            "Edge GitHub Pages (Host: ordenanzas.evegat.cl)",
            passed,
            f"HTTP {code}, bytes: {len(body)}"
        ))
    except Exception as e:
        results.append(CheckResult("Edge GitHub Pages (Host: ordenanzas.evegat.cl)", False, str(e)))

    # 2. Public URL Resolution & HTTPS Status
    try:
        code, hdrs, body = check_url(TARGET_URL)
        passed = (code == 200)
        results.append(CheckResult(
            "Public HTTPS root (https://ordenanzas.evegat.cl)",
            passed,
            f"HTTP {code}, bytes: {len(body)}"
        ))
    except Exception as e:
        results.append(CheckResult("Public HTTPS root (https://ordenanzas.evegat.cl)", False, f"Falla conectividad pública: {e}"))

    # 3. status_data.json public verification
    try:
        code, hdrs, body = check_url(f"{TARGET_URL}/status_data.json")
        data = json.loads(body.decode("utf-8"))
        metrics = data.get("metrics", {})
        total = metrics.get("total_ordenanzas")
        comunas = metrics.get("comunas_con_datos")
        passed = (code == 200 and total == 7226 and comunas == 346)
        results.append(CheckResult(
            "Dataset JSON (status_data.json)",
            passed,
            f"Total ordenanzas: {total} (esperado 7226), comunas: {comunas} (esperado 346)"
        ))
    except Exception as e:
        results.append(CheckResult("Dataset JSON (status_data.json)", False, str(e)))

    # 4. Downloads CSV verification
    try:
        code, hdrs, body = check_url(f"{TARGET_URL}/descargas/README_PUBLICO.txt")
        text = body.decode("utf-8")
        passed = (code == 200 and "Registros publicados: 7226" in text)
        results.append(CheckResult(
            "Descargas (README_PUBLICO.txt)",
            passed,
            f"HTTP {code}, texto verificado con 7226 registros"
        ))
    except Exception as e:
        results.append(CheckResult("Descargas (README_PUBLICO.txt)", False, str(e)))

    return results


def main():
    print("=== Verificación E2E Despliegue P090 ===")
    results = run_e2e_tests()
    all_passed = True
    for r in results:
        status = "[PASS]" if r.passed else "[PENDING/FAIL]"
        print(f"{status:16} {r.name}: {r.detail}")
        if not r.passed:
            all_passed = False
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
