#!/usr/bin/env python3
"""Harness MyWorld v1: contratos y gates portables para productos digitales."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
START_RE = re.compile(r"<!-- myworld-harness:start version=.*? -->.*?<!-- myworld-harness:end -->", re.DOTALL)
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", ".next", ".astro", "coverage", "DataCompleta", "data"}
TEXT_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".ini", ".env", ".md", ".html", ".css", ".sql", ".ps1", ".sh", ".bat"}
TRIVY_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".lock", ".tf", ".hcl"}
TRIVY_NAMES = {
    "dockerfile", "containerfile", "requirements.txt", "requirements-dev.txt",
    "pipfile", "pipfile.lock", "poetry.lock", "pyproject.toml", "package.json",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
    "go.mod", "go.sum", "cargo.toml", "cargo.lock", "composer.json", "composer.lock",
}
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN [A-Z ]{1,40}PRIVATE KEY-----"),
    "provider_token": re.compile(r"(?:sk_live_|ghp_|github_pat_|AKIA)[A-Za-z0-9_-]{16,}"),
    "assigned_secret": re.compile(r"(?i)(?:api[_-]?key|secret|password|token|credential)\s*[:=]\s*['\"][^'\"\s]{16,}['\"]"),
    "database_url": re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s:@]+:[^\s@]+@[^\s/]+/[^\s]+"),
}
REQUIRED_PROFILE = {
    "schema_version", "product_id", "name", "owner", "myworld_project", "kind",
    "lifecycle_stage", "risk", "data_classification", "deployment", "repository",
    "commands", "critical_paths", "forbidden_paths", "multi_agent", "observability",
    "release", "evidence",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def result(name: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"check": name, "status": status, "detail": detail}
    row.update(extra)
    return row


def report(command: str, repo: Path | None, checks: list[dict[str, Any]], error: str | None = None) -> dict[str, Any]:
    states = [item["status"] for item in checks]
    if error:
        status = "error"
        exit_code = 2
    elif "fail" in states:
        status = "fail"
        exit_code = 1
    else:
        status = "pass"
        exit_code = 0
    return {
        "schema_version": VERSION,
        "timestamp": now_iso(),
        "command": command,
        "repository": str(repo) if repo else None,
        "status": status,
        "exit_code": exit_code,
        "summary": {
            "passed": states.count("pass"),
            "failed": states.count("fail"),
            "pending": states.count("pending"),
            "not_applicable": states.count("not_applicable"),
        },
        "checks": checks,
        "error": error,
    }


def print_report(payload: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json_text(payload), end="")
    else:
        print(f"Harness MyWorld {VERSION} | {payload['command']} | {payload['status'].upper()}")
        if payload.get("repository"):
            print(f"Repositorio: {payload['repository']}")
        for check in payload["checks"]:
            print(f"[{check['status'].upper()}] {check['check']}: {check['detail']}")
        if payload.get("error"):
            print(f"[ERROR] {payload['error']}")
    return int(payload["exit_code"])


def harness_home() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "inventory" / "repos.json").exists() and (parent / "schemas" / "harness-v1.schema.json").exists():
            return parent
    return None


def repository_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    if here.parent.name == ".myworld-harness":
        return here.parent.parent
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / "MYWORLD-HARNESS.json").exists() or (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd().resolve()


def profile_path(repo: Path) -> Path:
    return repo / "MYWORLD-HARNESS.json"


def load_profile(repo: Path) -> dict[str, Any]:
    path = profile_path(repo)
    if not path.exists():
        raise FileNotFoundError(f"Falta {path.name}")
    value = json_load(path)
    if not isinstance(value, dict):
        raise ValueError("El contrato debe ser un objeto JSON")
    return value


def schema_path(repo: Path) -> Path:
    local = repo / ".myworld-harness" / "schema.json"
    if local.exists():
        return local
    home = harness_home()
    if home:
        return home / "schemas" / "harness-v1.schema.json"
    raise FileNotFoundError("No se encontró el schema del harness")


def validate_profile(repo: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    try:
        profile = load_profile(repo)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [result("profile", "fail", str(exc))]
    missing = sorted(REQUIRED_PROFILE - set(profile))
    if missing:
        checks.append(result("profile.required", "fail", f"Campos ausentes: {', '.join(missing)}"))
        return checks
    if profile.get("schema_version") != VERSION:
        checks.append(result("profile.version", "fail", f"Esperada {VERSION}"))
    else:
        checks.append(result("profile.version", "pass", VERSION))
    try:
        import jsonschema  # type: ignore

        jsonschema.Draft202012Validator(json_load(schema_path(repo)), format_checker=jsonschema.FormatChecker()).validate(profile)
        checks.append(result("profile.schema", "pass", "Contrato válido"))
    except ImportError:
        checks.append(result("profile.schema", "pending", "jsonschema no disponible; se aplicó validación mínima"))
    except Exception as exc:  # jsonschema expone varias clases según versión
        checks.append(result("profile.schema", "fail", f"Contrato inválido: {type(exc).__name__}"))
    stage = profile.get("lifecycle_stage")
    release = profile.get("release", {})
    if stage in {"staging", "production", "maintenance"}:
        required = ["rollback_required"]
        if profile.get("deployment", {}).get("state") == "public" and any(item in profile.get("data_classification", []) for item in ("personal", "sensitive")):
            required += ["backup_required", "restore_test_required"]
        missing_controls = [key for key in required if not release.get(key)]
        checks.append(result("lifecycle.release_controls", "fail" if missing_controls else "pass", f"Faltan: {', '.join(missing_controls)}" if missing_controls else "Controles declarados"))
    else:
        checks.append(result("lifecycle.release_controls", "not_applicable", f"Etapa {stage}"))
    return checks


def validate_artifact(path: Path, kind: str) -> dict[str, Any]:
    home = harness_home()
    if not home:
        return report("validate", None, [], "Validación de artefactos requiere la fuente canónica")
    schema = home / "schemas" / ("harness-v1.schema.json" if kind == "product" else f"{kind}.schema.json")
    if not schema.exists() or not path.exists():
        return report("validate", None, [], "Schema o artefacto ausente")
    try:
        import jsonschema  # type: ignore

        validator = jsonschema.Draft202012Validator(json_load(schema), format_checker=jsonschema.FormatChecker())
        if kind == "pending" and path.suffix.lower() == ".ndjson":
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for record in records:
                validator.validate(record)
            detail = f"{path.name}: {len(records)} registro(s) válidos"
        else:
            validator.validate(json_load(path))
            detail = f"{path.name} válido"
        checks = [result(f"validate.{kind}", "pass", detail)]
        return report("validate", None, checks)
    except ImportError:
        return report("validate", None, [], "jsonschema no está instalado")
    except Exception as exc:
        return report("validate", None, [result(f"validate.{kind}", "fail", f"{type(exc).__name__}")])


def adapter_template(home: Path) -> tuple[str, str]:
    body = (home / "templates" / "AGENTS.block.md").read_text(encoding="utf-8").strip()
    digest = sha256_bytes(body.encode("utf-8"))
    block = f"<!-- myworld-harness:start version={VERSION} sha256={digest} -->\n{body}\n<!-- myworld-harness:end -->"
    return block, digest


def validate_adapter(repo: Path) -> list[dict[str, Any]]:
    agents = repo / "AGENTS.md"
    local_template = repo / ".myworld-harness" / "AGENTS.block.md"
    if not agents.exists() or not local_template.exists():
        return [result("adapter", "fail", "AGENTS.md o template local ausente")]
    body = local_template.read_text(encoding="utf-8").strip()
    expected = sha256_bytes(body.encode("utf-8"))
    text = agents.read_text(encoding="utf-8")
    match = START_RE.search(text)
    if not match:
        return [result("adapter", "fail", "Bloque administrado ausente")]
    marker = re.search(r"sha256=([a-f0-9]{64})", match.group(0))
    if not marker or marker.group(1) != expected or body not in match.group(0):
        return [result("adapter", "fail", "Bloque divergente")]
    return [result("adapter", "pass", f"v{VERSION} sha256={expected[:12]}")]


def git_output(repo: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def preflight(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo) + validate_adapter(repo)
    code, branch = git_output(repo, "branch", "--show-current")
    if code != 0:
        checks.append(result("git.repository", "fail", "No es un repositorio Git"))
    else:
        checks.append(result("git.repository", "pass", f"Rama: {branch or '(sin commits)'}"))
        _, status = git_output(repo, "status", "--porcelain")
        if status:
            checks.append(result("git.working_tree", "pending", "Hay cambios previos; deben preservarse", changed_files=len(status.splitlines())))
        else:
            checks.append(result("git.working_tree", "pass", "Limpio"))
        _, hooks = git_output(repo, "config", "--get", "core.hooksPath")
        checks.append(result("git.hooks", "pass" if hooks == ".githooks" else "fail", hooks or "core.hooksPath no configurado"))
    return report("preflight", repo, checks)


def executable_files(repo: Path, staged: bool) -> list[Path]:
    if staged:
        code, output = git_output(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        if code != 0:
            return []
        candidates = [repo / line for line in output.splitlines()]
    else:
        code, output = git_output(repo, "ls-files", "--cached", "--others", "--exclude-standard")
        if code == 0:
            candidates = [repo / line for line in output.splitlines()]
        else:
            candidates = []
            for root, dirs, files in os.walk(repo):
                dirs[:] = [item for item in dirs if item not in IGNORED_DIRS]
                candidates.extend(Path(root) / name for name in files)
    return [path for path in candidates if path.exists() and path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 2_000_000]


def trivy_files(repo: Path) -> list[Path]:
    code, output = git_output(repo, "ls-files", "--cached", "--others", "--exclude-standard")
    if code != 0:
        return []
    selected: list[Path] = []
    for relative in output.splitlines():
        path = repo / relative
        lower_name = path.name.lower()
        if not path.is_file() or path.stat().st_size > 10_000_000:
            continue
        if lower_name in TRIVY_NAMES or path.suffix.lower() in TRIVY_SUFFIXES or ".github/workflows/" in relative.replace("\\", "/"):
            selected.append(path)
    return selected


def run_trivy(executable: str, repo: Path) -> tuple[int, str, int]:
    files = trivy_files(repo)
    with tempfile.TemporaryDirectory(prefix="myworld-harness-trivy-") as temp_name:
        scan_root = Path(temp_name)
        for source in files:
            destination = scan_root / source.relative_to(repo)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        command = f'"{executable}" fs --scanners vuln,misconfig --severity HIGH,CRITICAL --exit-code 1 --no-progress "{scan_root}"'
        code, output = run_shell(command, repo, timeout=1200)
    return code, output, len(files)


def secret_scan(repo: Path, staged: bool = False) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in executable_files(repo, staged):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            lower = line.lower()
            if "placeholder" in lower or "example" in lower or "fake-secret-for-test" in lower:
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    findings.append({"path": str(path.relative_to(repo)), "line": line_no, "kind": label})
    if findings:
        return [result("security.builtin_secrets", "fail", f"{len(findings)} posible(s) secreto(s); valores omitidos", findings=findings)]
    return [result("security.builtin_secrets", "pass", f"{len(executable_files(repo, staged))} archivos revisados")]


def run_shell(command: str, repo: Path, timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(command, cwd=repo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    output = (proc.stdout + proc.stderr).strip()
    lines = output.splitlines()
    return proc.returncode, "\n".join(lines[-20:])[:4000]


def quality(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo)
    try:
        profile = load_profile(repo)
    except Exception as exc:
        return report("quality", repo, checks, str(exc))
    commands: list[str] = []
    for group in ("quality", "test", "build"):
        for command in profile["commands"].get(group, []):
            if command not in commands:
                commands.append(command)
    if not commands:
        checks.append(result("quality.commands", "not_applicable", "No hay comando automático aplicable; requiere revisión manual"))
    for index, command in enumerate(commands, 1):
        code, output = run_shell(command, repo)
        checks.append(result(f"quality.command.{index}", "pass" if code == 0 else "fail", f"exit={code}: {command}", output=output))
    return report("quality", repo, checks)


def find_executable(name: str) -> str | None:
    executable = shutil.which(name)
    if executable:
        return executable
    winget = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget.exists():
        matches = sorted(winget.glob(f"**/{name}.exe"))
        if matches:
            return str(matches[-1])
    return None


def tool_version(name: str) -> tuple[bool, str, str | None]:
    executable = find_executable(name)
    if not executable:
        return False, "no instalado", None
    code, output = run_shell(f'"{executable}" --version', Path.cwd(), timeout=30)
    return code == 0, output.splitlines()[0] if output else executable, executable


def security(repo: Path, staged: bool = False, no_external: bool = False) -> dict[str, Any]:
    checks = validate_profile(repo) + secret_scan(repo, staged)
    profile = load_profile(repo)
    if no_external:
        checks.append(result("security.external", "not_applicable", "Scanners externos delegados al runner"))
        return report("security", repo, checks)
    blocking_tools = profile["risk"] in {"high", "critical"} and profile["deployment"]["state"] == "public"
    for tool in ("gitleaks", "trivy"):
        available, version, executable = tool_version(tool)
        checks.append(result(f"security.tool.{tool}", "pass" if available else ("fail" if blocking_tools else "pending"), version))
        if available and not staged and executable:
            if tool == "gitleaks":
                command = f'"{executable}" git --no-banner --redact --exit-code 1 .'
                code, output = run_shell(command, repo, timeout=1200)
                scope = "historial Git"
            else:
                code, output, file_count = run_trivy(executable, repo)
                scope = f"{file_count} manifiesto(s) y archivo(s) de configuración elegibles"
            checks.append(result(f"security.scan.{tool}", "pass" if code == 0 else "fail", f"exit={code}; alcance={scope}; hallazgos sensibles redactados", output=output))
    return report("security", repo, checks)


def release_gate(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo)
    profile = load_profile(repo)
    if profile["lifecycle_stage"] not in {"staging", "production", "maintenance"}:
        checks.append(result("release.applicability", "not_applicable", f"Etapa {profile['lifecycle_stage']}"))
        return report("release", repo, checks)
    evidence = repo / ".myworld-harness" / "evidence" / "release.json"
    if not evidence.exists():
        checks.append(result("release.evidence", "fail", "Falta evidencia de versión, rollback, backup/restore y monitor"))
    else:
        try:
            data = json_load(evidence)
            required = {"version", "artifact", "rollback_tested", "monitor_verified"}
            if profile["release"]["backup_required"]:
                required |= {"backup_verified"}
            if profile["release"]["restore_test_required"]:
                required |= {"restore_tested"}
            missing = sorted(key for key in required if not data.get(key))
            checks.append(result("release.evidence", "fail" if missing else "pass", f"Faltan: {', '.join(missing)}" if missing else "Evidencia completa"))
        except Exception as exc:
            checks.append(result("release.evidence", "fail", f"JSON inválido: {type(exc).__name__}"))
    return report("release", repo, checks)


def postflight(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo) + validate_adapter(repo)
    code, output = git_output(repo, "diff", "--check")
    checks.append(result("postflight.diff_check", "pass" if code == 0 else "fail", "Sin errores de whitespace" if code == 0 else output[:1000]))
    evidence = repo / ".myworld-harness" / "evidence" / "postflight.json"
    checks.append(result("postflight.evidence", "pass" if evidence.exists() else "pending", "Evidencia presente" if evidence.exists() else "Debe registrarse al cerrar una tarea relevante"))
    return report("postflight", repo, checks)


def observe(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo)
    profile = load_profile(repo)
    monitors = profile["observability"]["monitors"]
    if not monitors:
        checks.append(result("observe.monitors", "not_applicable", f"Nivel {profile['observability']['level']} sin monitor externo"))
        return report("observe", repo, checks)
    for monitor in monitors:
        target = monitor["target"]
        try:
            request = urllib.request.Request(target, headers={"User-Agent": f"MyWorldHarness/{VERSION}"})
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(500_000).decode("utf-8", errors="ignore")
                status = response.status
            ok = 200 <= status < 400
            if monitor["type"] == "keyword":
                ok = ok and monitor.get("keyword", "").casefold() in body.casefold()
            checks.append(result(f"observe.{monitor['name']}", "pass" if ok else "fail", f"HTTP {status}; target={target}"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            checks.append(result(f"observe.{monitor['name']}", "fail", f"{type(exc).__name__}; target={target}"))
    return report("observe", repo, checks)


LAUNCHER = """param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)\n$python = (Get-Command python -ErrorAction Stop).Source\n& $python (Join-Path $PSScriptRoot 'harness.py') @Args\nexit $LASTEXITCODE\n"""
PRE_COMMIT = """#!/bin/sh
repo_root=$(git rev-parse --show-toplevel) || exit 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$repo_root/.myworld-harness/harness.ps1" preflight || exit $?
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$repo_root/.myworld-harness/harness.ps1" security --staged
exit $?
"""
PRE_PUSH = """#!/bin/sh
repo_root=$(git rev-parse --show-toplevel) || exit 2
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$repo_root/.myworld-harness/harness.ps1" quality || exit $?
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$repo_root/.myworld-harness/harness.ps1" security
exit $?
"""
CI_WORKFLOW = """name: MyWorld Harness v1

on:
  pull_request:
  push:

permissions:
  contents: read

jobs:
  harness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Activate repository hooks path
        run: git config core.hooksPath .githooks
      - name: Contract and adapter
        run: python .myworld-harness/harness.py preflight
      - name: Built-in secret scanner
        run: python .myworld-harness/harness.py security --no-external
      - name: Gitleaks 8.30.1
        run: docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:v8.30.1 git /repo --no-banner --redact --exit-code 1
      - name: Trivy 0.74.0
        run: docker run --rm -v "$PWD:/repo" aquasec/trivy:0.74.0 fs --scanners vuln,misconfig --severity HIGH,CRITICAL --exit-code 1 --no-progress --skip-dirs node_modules --skip-dirs .git /repo
"""


def write_if_changed(path: Path, content: str | bytes, dry_run: bool) -> bool:
    data = content if isinstance(content, bytes) else content.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return True


def merge_adapter(path: Path, block: str) -> str:
    current = path.read_text(encoding="utf-8") if path.exists() else "# AGENTS.md\n"
    if START_RE.search(current):
        return START_RE.sub(block, current).rstrip() + "\n"
    return current.rstrip() + "\n\n" + block + "\n"


def ensure_gitignore(repo: Path) -> str:
    path = repo / ".gitignore"
    current = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    additions = [item for item in (".myworld-harness/evidence/", ".myworld-harness/cache/") if item not in current.splitlines()]
    if not additions:
        return current
    return current.rstrip() + "\n\n# MyWorld Harness runtime evidence\n" + "\n".join(additions) + "\n"


def sync_repositories(dry_run: bool) -> dict[str, Any]:
    home = harness_home()
    if not home:
        return report("sync", None, [], "sync solo está disponible desde la fuente canónica")
    inventory = json_load(home / "inventory" / "repos.json")
    block, digest = adapter_template(home)
    schema = (home / "schemas" / "harness-v1.schema.json").read_bytes()
    script = Path(__file__).resolve().read_bytes()
    template = (home / "templates" / "AGENTS.block.md").read_bytes()
    checks: list[dict[str, Any]] = []
    for entry in inventory["managed"]:
        repo = Path(entry["path"])
        name = entry["profile"]["product_id"]
        if not repo.exists():
            checks.append(result(f"sync.{name}", "fail", "Ruta ausente"))
            continue
        changes = 0
        changes += write_if_changed(repo / "MYWORLD-HARNESS.json", json_text(entry["profile"]), dry_run)
        changes += write_if_changed(repo / "AGENTS.md", merge_adapter(repo / "AGENTS.md", block), dry_run)
        changes += write_if_changed(repo / ".myworld-harness" / "harness.py", script, dry_run)
        changes += write_if_changed(repo / ".myworld-harness" / "harness.ps1", LAUNCHER, dry_run)
        changes += write_if_changed(repo / ".myworld-harness" / "schema.json", schema, dry_run)
        for schema_source in sorted((home / "schemas").glob("*.schema.json")):
            changes += write_if_changed(repo / ".myworld-harness" / "schemas" / schema_source.name, schema_source.read_bytes(), dry_run)
        changes += write_if_changed(repo / ".myworld-harness" / "AGENTS.block.md", template, dry_run)
        changes += write_if_changed(repo / ".myworld-harness" / "VERSION", VERSION + "\n", dry_run)
        changes += write_if_changed(repo / ".githooks" / "pre-commit", PRE_COMMIT, dry_run)
        changes += write_if_changed(repo / ".githooks" / "pre-push", PRE_PUSH, dry_run)
        changes += write_if_changed(repo / ".github" / "workflows" / "myworld-harness.yml", CI_WORKFLOW, dry_run)
        changes += write_if_changed(repo / ".gitignore", ensure_gitignore(repo), dry_run)
        if (repo / ".git").exists() and not dry_run:
            git_output(repo, "config", "core.hooksPath", ".githooks")
        checks.append(result(f"sync.{name}", "pass", f"{changes} cambio(s) {'previstos' if dry_run else 'aplicados'}; adapter={digest[:12]}"))
    return report("sync", None, checks)


def inventory_report() -> dict[str, Any]:
    home = harness_home()
    if not home:
        return report("inventory", None, [], "Inventario no disponible en bundle local")
    data = json_load(home / "inventory" / "repos.json")
    checks = [result("inventory.managed", "pass", f"{len(data['managed'])} repositorios")]
    checks.append(result("inventory.excluded", "pass", f"{len(data['excluded'])} raíces excluidas con razón"))
    missing = [entry["path"] for entry in data["managed"] if not Path(entry["path"]).exists()]
    checks.append(result("inventory.paths", "fail" if missing else "pass", f"Ausentes: {len(missing)}" if missing else "Todas las rutas existen"))
    return report("inventory", None, checks)


def pending_report() -> dict[str, Any]:
    home = harness_home()
    if not home:
        return report("pending", None, [], "Registro central no disponible en bundle local")
    path = home / "state" / "pending.ndjson"
    rows: list[dict[str, Any]] = []
    errors = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                errors += 1
    open_rows = [row for row in rows if row.get("status") in {"open", "blocking"}]
    checks = [result("pending.syntax", "fail" if errors else "pass", f"Errores: {errors}" if errors else "NDJSON válido")]
    checks.append(result("pending.open", "pending" if open_rows else "pass", f"{len(open_rows)} pendiente(s) abierto(s)"))
    return report("pending", None, checks)


def audit(full: bool) -> dict[str, Any]:
    home = harness_home()
    if not home:
        return report("audit", None, [], "Auditoría global no disponible en bundle local")
    data = json_load(home / "inventory" / "repos.json")
    checks: list[dict[str, Any]] = []
    for entry in data["managed"]:
        repo = Path(entry["path"])
        if not repo.exists():
            checks.append(result(f"audit.{entry['profile']['product_id']}", "fail", "Ruta ausente"))
            continue
        reports = [preflight(repo)]
        if full:
            reports.extend([quality(repo), security(repo)])
            if entry["profile"]["deployment"]["state"] == "public":
                reports.extend([release_gate(repo), observe(repo)])
        failed = any(item["exit_code"] != 0 for item in reports)
        pending = sum(item["summary"]["pending"] for item in reports)
        checks.append(result(f"audit.{entry['profile']['product_id']}", "fail" if failed else ("pending" if pending else "pass"), f"{len(reports)} gate(s); pendientes={pending}"))
    return report("audit", None, checks)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Harness MyWorld v1")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "quality", "security", "release", "postflight", "observe"):
        item = sub.add_parser(name)
        item.add_argument("--repo")
        item.add_argument("--json", action="store_true")
        if name == "security":
            item.add_argument("--staged", action="store_true")
            item.add_argument("--no-external", action="store_true")
    inv = sub.add_parser("inventory")
    inv.add_argument("--json", action="store_true")
    sync = sub.add_parser("sync")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--json", action="store_true")
    pending = sub.add_parser("pending")
    pending.add_argument("--json", action="store_true")
    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument("--full", action="store_true")
    audit_parser.add_argument("--json", action="store_true")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("file")
    validate_parser.add_argument("--kind", required=True, choices=["product", "task", "session", "lock", "handoff", "evidence", "incident", "release", "pending"])
    validate_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.command == "inventory":
            payload = inventory_report()
        elif args.command == "sync":
            payload = sync_repositories(args.dry_run)
        elif args.command == "pending":
            payload = pending_report()
        elif args.command == "audit":
            payload = audit(args.full)
        elif args.command == "validate":
            payload = validate_artifact(Path(args.file).resolve(), args.kind)
        else:
            repo = repository_root(args.repo)
            if args.command == "preflight":
                payload = preflight(repo)
            elif args.command == "quality":
                payload = quality(repo)
            elif args.command == "security":
                payload = security(repo, args.staged, args.no_external)
            elif args.command == "release":
                payload = release_gate(repo)
            elif args.command == "postflight":
                payload = postflight(repo)
            else:
                payload = observe(repo)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = report(args.command, None, [], f"{type(exc).__name__}: {exc}")
    return print_report(payload, bool(getattr(args, "json", False)))


if __name__ == "__main__":
    raise SystemExit(main())
