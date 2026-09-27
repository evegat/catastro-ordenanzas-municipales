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
from datetime import datetime, timedelta, timezone
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
CONTINUITY_STATUSES = {"active", "paused", "completed", "cancelled", "blocked", "recovery_needed", "abandoned"}
CONTINUITY_STATUS_ALIASES = {"complete": "completed"}
CONTINUITY_EVENT_TYPES = {
    "session_started", "work_claimed", "checkpoint", "files_changed",
    "verification_run", "handoff_created", "session_paused",
    "session_completed", "recovery_required",
    # Coordination Plane v0.3 hardening events. These extend the shared journal
    # rather than creating a second observability/event subsystem.
    "task_created", "task_claimed", "task_status_changed",
    "artifact_created", "approval_required", "approval_resolved",
    "telemetry_recorded", "lease_heartbeat", "lease_released",
}
CORE_MYWORLD_SKILLS = {
    "myworld-close-loop",
    "myworld-operational-check",
    "checkpoint",
    "unified-memory",
    "client-review-gate",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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
        if kind in {"pending", "event"} and path.suffix.lower() == ".ndjson":
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


def design_gate(repo: Path) -> dict[str, Any]:
    checks = validate_profile(repo)
    from myworld_design_engine import MyWorldDesignEngine
    engine = MyWorldDesignEngine(repo)
    result_data = engine.run_full_design_gate()
    checks.extend(result_data["checks"])
    return report("design", repo, checks)


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


def parse_simple_frontmatter(path: Path) -> dict[str, Any]:
    """Extrae pares clave-valor simples de frontmatter YAML o archivos YAML/JSON.

    Implementación mínima sin dependencias externas; no soporta listas o tipos
    complejos, pero devuelve cadenas escalares limpias.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    if path.suffix.lower() == ".md":
        if not lines or lines[0].strip() != "---":
            return {}
        try:
            end = lines.index("---", 1)
        except ValueError:
            return {}
        lines = lines[1:end]
    data: dict[str, Any] = {}
    for line in lines:
        if not line or line[0].isspace() or ":" not in line or line.lstrip().startswith("#"):
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        value = raw.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value.casefold() in {"true", "false"}:
            data[key] = value.casefold() == "true"
        elif value.casefold() in {"null", "none", "~"}:
            data[key] = None
        else:
            data[key] = value
    return data


def parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def continuity_vault(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    home = harness_home()
    if not home:
        raise FileNotFoundError("Continuidad requiere el Harness canónico o --vault")
    return home.parents[1]


def continuity_audit(vault: Path, stale_after_minutes: int = 60) -> dict[str, Any]:
    sessions_dir = vault / ".myworld-sessions"
    locks_dir = vault / ".myworld-locks"
    if not sessions_dir.exists() or not locks_dir.exists():
        return report("continuity audit", None, [], "Faltan .myworld-sessions o .myworld-locks")

    session_files = sorted(path for path in sessions_dir.iterdir() if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".json"})
    lock_files = sorted(path for path in locks_dir.iterdir() if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"})
    sessions: dict[str, tuple[Path, dict[str, Any]]] = {}
    missing_status: list[str] = []
    invalid_status: list[str] = []
    alias_status: list[str] = []
    duplicate_ids: list[str] = []
    stale_sessions: list[str] = []
    now = datetime.now(timezone.utc).astimezone()
    stale_before = now - timedelta(minutes=max(1, stale_after_minutes))

    for path in session_files:
        try:
            data = json_load(path) if path.suffix.lower() == ".json" else parse_simple_frontmatter(path)
        except (OSError, ValueError, json.JSONDecodeError):
            data = {}
        session_id = str(data.get("session") or data.get("session_id") or path.stem)
        if session_id in sessions:
            duplicate_ids.append(session_id)
        sessions[session_id] = (path, data)
        raw_status = str(data.get("status") or "").casefold()
        if not raw_status:
            missing_status.append(path.name)
        elif raw_status in CONTINUITY_STATUS_ALIASES:
            alias_status.append(path.name)
        elif raw_status not in CONTINUITY_STATUSES:
            invalid_status.append(path.name)
        normalized = CONTINUITY_STATUS_ALIASES.get(raw_status, raw_status)
        if normalized == "active":
            last_seen = parse_iso_datetime(data.get("heartbeat_at") or data.get("updated_at") or data.get("started_at"))
            if last_seen and last_seen < stale_before:
                stale_sessions.append(session_id)

    missing_records: list[str] = []
    malformed_locks: list[str] = []
    active_without_lease: list[str] = []
    expired_leases: list[str] = []
    for path in lock_files:
        try:
            data = json_load(path) if path.suffix.lower() == ".json" else parse_simple_frontmatter(path)
        except (OSError, ValueError, json.JSONDecodeError):
            data = {}
        if not all(data.get(key) for key in ("owner", "host", "session", "scope", "target", "status")):
            malformed_locks.append(path.name)
            continue
        status = str(data.get("status")).casefold()
        if status != "active":
            continue
        record = data.get("record")
        session_id = str(data.get("session"))
        if record:
            record_path = vault / str(record)
            if not record_path.exists():
                missing_records.append(path.name)
        elif session_id not in sessions:
            missing_records.append(path.name)
        lease_expires = parse_iso_datetime(data.get("lease_expires_at"))
        if lease_expires is None:
            active_without_lease.append(path.name)
        elif lease_expires < now:
            expired_leases.append(path.name)

    checks = [
        result("continuity.sessions.discovered", "pass", f"{len(session_files)} registro(s)"),
        result("continuity.sessions.missing_status", "fail" if missing_status else "pass", f"{len(missing_status)} sin status"),
        result("continuity.sessions.legacy_status", "pending" if alias_status else "pass", f"{len(alias_status)} usan alias complete"),
        result("continuity.sessions.invalid_status", "fail" if invalid_status else "pass", f"{len(invalid_status)} estado(s) inválido(s)"),
        result("continuity.sessions.duplicate_id", "fail" if duplicate_ids else "pass", f"{len(duplicate_ids)} ID duplicado(s)"),
        result("continuity.sessions.stale", "pending" if stale_sessions else "pass", f"{len(stale_sessions)} activa(s) sin pulso reciente", session_ids=stale_sessions[:20]),
        result("continuity.locks.discovered", "pass", f"{len(lock_files)} lock(s)"),
        result("continuity.locks.malformed", "fail" if malformed_locks else "pass", f"{len(malformed_locks)} malformado(s)"),
        result("continuity.locks.missing_record", "fail" if missing_records else "pass", f"{len(missing_records)} sin sesión asociada"),
        result("continuity.locks.no_lease", "pending" if active_without_lease else "pass", f"{len(active_without_lease)} activo(s) sin lease", files=active_without_lease[:20]),
        result("continuity.locks.expired", "pending" if expired_leases else "pass", f"{len(expired_leases)} lease(s) vencida(s)", files=expired_leases[:20]),
    ]
    payload = report("continuity audit", None, checks)
    payload["inventory"] = {
        "sessions": len(session_files),
        "locks": len(lock_files),
        "missing_status": missing_status,
        "legacy_status": alias_status,
        "invalid_status": invalid_status,
        "stale_sessions": stale_sessions,
        "malformed_locks": malformed_locks,
        "missing_records": missing_records,
        "active_without_lease": active_without_lease,
        "expired_leases": expired_leases,
    }
    return payload


def continuity_event_path(vault: Path, timestamp: datetime) -> Path:
    return vault / "3 - SistemaMyworld" / "harness" / "state" / "continuity" / "events" / f"{timestamp.date().isoformat()}.ndjson"


def append_continuity_event(vault: Path, event: dict[str, Any]) -> tuple[Path, bool]:
    timestamp = parse_iso_datetime(event.get("timestamp")) or datetime.now(timezone.utc).astimezone()
    path = continuity_event_path(vault, timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    event_id = str(event["event_id"])
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                if json.loads(line).get("event_id") == event_id:
                    return path, False
            except json.JSONDecodeError:
                continue
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return path, True


def continuity_checkpoint(
    vault: Path,
    session_id: str,
    project: str,
    work_item: str,
    event_type: str,
    next_action: str,
    files: list[str],
    evidence: list[str],
    event_id: str | None = None,
) -> dict[str, Any]:
    if event_type not in CONTINUITY_EVENT_TYPES:
        return report("continuity checkpoint", None, [], f"Tipo de evento inválido: {event_type}")
    timestamp = now_iso()
    if not event_id:
        seed = f"{session_id}|{project}|{work_item}|{event_type}|{timestamp}".encode("utf-8")
        event_id = f"EVD-{project}-{hashlib.sha256(seed).hexdigest()[:12]}"
    event = {
        "schema_version": VERSION,
        "event_id": event_id,
        "session_id": session_id,
        "project": project,
        "work_item": work_item,
        "type": event_type,
        "timestamp": timestamp,
        "files": files,
        "evidence": evidence,
        "next_action": next_action,
    }
    path, appended = append_continuity_event(vault, event)
    check = result("continuity.checkpoint", "pass", f"{'registrado' if appended else 'ya existía'}: {event_id}", path=str(path), appended=appended)
    payload = report("continuity checkpoint", None, [check])
    payload["event"] = event
    return payload


def continuity_recover(vault: Path, session_id: str) -> dict[str, Any]:
    sessions_dir = vault / ".myworld-sessions"
    matching_sessions: list[Path] = []
    for path in sessions_dir.iterdir() if sessions_dir.exists() else []:
        if not path.is_file():
            continue
        data = parse_simple_frontmatter(path) if path.suffix.lower() != ".json" else json_load(path)
        if str(data.get("session") or data.get("session_id") or path.stem) == session_id:
            matching_sessions.append(path)
    events: list[dict[str, Any]] = []
    events_dir = vault / "3 - SistemaMyworld" / "harness" / "state" / "continuity" / "events"
    if events_dir.exists():
        for path in sorted(events_dir.glob("*.ndjson")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("session_id") == session_id:
                    events.append(event)
    events.sort(key=lambda item: str(item.get("timestamp", "")))
    latest = events[-1] if events else None
    files = list(dict.fromkeys(item for event in events for item in event.get("files", [])))
    missing_files = [item for item in files if not (vault / item).exists()]
    checks = [
        result("continuity.recover.session", "pass" if matching_sessions else "fail", f"{len(matching_sessions)} registro(s)"),
        result("continuity.recover.events", "pass" if events else "pending", f"{len(events)} evento(s)"),
        result("continuity.recover.files", "pending" if missing_files else "pass", f"{len(missing_files)} archivo(s) ausente(s)"),
    ]
    payload = report("continuity recover", None, checks)
    payload["recovery"] = {
        "session_id": session_id,
        "session_records": [str(path.relative_to(vault)) for path in matching_sessions],
        "latest_event": latest,
        "files": files,
        "missing_files": missing_files,
        "next_action": latest.get("next_action") if latest else None,
        "dry_run": True,
    }
    return payload


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
    return report("audit", home, checks)

def skill_vault(explicit: str | None = None) -> Path:
    return continuity_vault(explicit)


def skill_catalog(vault: Path, category: str | None = None) -> dict[str, Any]:
    catalog_dir = vault / "3 - SistemaMyworld" / "Skills"
    active_dir = vault / ".agents" / "skills"
    if not catalog_dir.exists():
        return report("skill catalog", None, [], "Directorio de catálogo 3 - SistemaMyworld/Skills no existe")

    active_skills = {p.name for p in active_dir.iterdir() if p.is_dir()} if active_dir.exists() else set()
    items: list[dict[str, Any]] = []

    categories = [p for p in catalog_dir.iterdir() if p.is_dir()]
    for cat_path in categories:
        cat_name = cat_path.name
        if category and cat_name.lower() != category.lower():
            continue
        for skill_path in cat_path.iterdir():
            if not skill_path.is_dir():
                continue
            skill_name = skill_path.name
            skill_md = skill_path / "SKILL.md"
            meta = parse_simple_frontmatter(skill_md) if skill_md.exists() else {}
            items.append({
                "name": skill_name,
                "category": cat_name,
                "active": skill_name in active_skills,
                "description": meta.get("description", ""),
                "path": str(skill_path.relative_to(vault)),
            })

    checks = [
        result("skill.catalog", "pass", f"Total habilidades en catálogo: {len(items)}", total=len(items))
    ]
    rep = report("skill catalog", None, checks)
    rep["skills"] = items
    return rep


def skill_activate(vault: Path, name: str, target_repo: Path | None = None) -> dict[str, Any]:
    catalog_dir = vault / "3 - SistemaMyworld" / "Skills"
    dest_skills_dir = (target_repo / ".agents" / "skills") if target_repo else (vault / ".agents" / "skills")

    matching: list[Path] = []
    for cat_path in catalog_dir.iterdir() if catalog_dir.exists() else []:
        if not cat_path.is_dir():
            continue
        candidate = cat_path / name
        if candidate.is_dir():
            matching.append(candidate)

    if not matching:
        return report("skill activate", None, [], f"Habilidad '{name}' no encontrada en el catálogo")

    source_dir = matching[0]
    dest_dir = dest_skills_dir / name

    if dest_dir.exists():
        check = result("skill.activate", "pass", f"Habilidad '{name}' ya se encuentra activa", path=str(dest_dir))
        return report("skill activate", None, [check])

    dest_skills_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, dest_dir)
    check = result("skill.activate", "pass", f"Habilidad '{name}' activada con éxito", path=str(dest_dir))
    return report("skill activate", None, [check])


def skill_deactivate(vault: Path, name: str, target_repo: Path | None = None) -> dict[str, Any]:
    dest_skills_dir = (target_repo / ".agents" / "skills") if target_repo else (vault / ".agents" / "skills")
    dest_dir = dest_skills_dir / name

    if target_repo is None and name in CORE_MYWORLD_SKILLS:
        return report("skill deactivate", None, [], f"Habilidad '{name}' es parte del Core protegido de MyWorld y no debe desactivarse")

    if not dest_dir.exists():
        check = result("skill.deactivate", "pass", f"Habilidad '{name}' no estaba activa", path=str(dest_dir))
        return report("skill deactivate", None, [check])

    def _on_err(func, path, exc_info):
        try:
            os.chmod(path, 0o777)
            func(path)
        except Exception:
            pass

    shutil.rmtree(dest_dir, onerror=_on_err)
    check = result("skill.deactivate", "pass", f"Habilidad '{name}' desactivada con éxito", path=str(dest_dir))
    return report("skill deactivate", None, [check])


def skill_audit(vault: Path, target_repo: Path | None = None) -> dict[str, Any]:
    active_skills_dir = (target_repo / ".agents" / "skills") if target_repo else (vault / ".agents" / "skills")
    catalog_dir = vault / "3 - SistemaMyworld" / "Skills"

    checks: list[dict[str, Any]] = []
    if not active_skills_dir.exists():
        checks.append(result("skill.audit.directory", "pass", "Directorio .agents/skills no existe (0 activas)"))
        return report("skill audit", None, checks)

    active = [p for p in active_skills_dir.iterdir() if p.is_dir()]
    count = len(active)

    if target_repo is None and count > 25:
        checks.append(result("skill.audit.tokens", "warn", f"Exceso de skills activas en Vault ({count} > 25). Riesgo de inflación basal de tokens.", count=count))
    else:
        checks.append(result("skill.audit.tokens", "pass", f"Carga de skills controlada ({count} activas). Contexto basal protegido.", count=count))

    all_catalog_skills: set[str] = set()
    for cat_path in catalog_dir.iterdir() if catalog_dir.exists() else []:
        if cat_path.is_dir():
            all_catalog_skills.update(p.name for p in cat_path.iterdir() if p.is_dir())

    unbacked = [p.name for p in active if p.name not in all_catalog_skills]
    if unbacked:
        checks.append(result("skill.audit.parity", "warn", f"Habilidades activas sin respaldo en catálogo: {', '.join(unbacked)}", unbacked=unbacked))
    else:
        checks.append(result("skill.audit.parity", "pass", "Todas las habilidades activas están respaldadas en el catálogo"))

    return report("skill audit", None, checks)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Harness MyWorld v1")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "quality", "security", "design", "release", "postflight", "observe"):
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
    validate_parser.add_argument("--kind", required=True, choices=["product", "task", "session", "lock", "handoff", "artifact", "checkpoint", "evidence", "incident", "release", "pending", "event"])
    validate_parser.add_argument("--json", action="store_true")
    continuity_parser = sub.add_parser("continuity")
    continuity_sub = continuity_parser.add_subparsers(dest="continuity_command", required=True)
    continuity_audit_parser = continuity_sub.add_parser("audit")
    continuity_audit_parser.add_argument("--vault")
    continuity_audit_parser.add_argument("--stale-after-minutes", type=int, default=60)
    continuity_audit_parser.add_argument("--json", action="store_true")
    continuity_checkpoint_parser = continuity_sub.add_parser("checkpoint")
    continuity_checkpoint_parser.add_argument("--vault")
    continuity_checkpoint_parser.add_argument("--session", required=True)
    continuity_checkpoint_parser.add_argument("--project", required=True)
    continuity_checkpoint_parser.add_argument("--work-item", required=True)
    continuity_checkpoint_parser.add_argument("--type", default="checkpoint", choices=sorted(CONTINUITY_EVENT_TYPES))
    continuity_checkpoint_parser.add_argument("--next-action", required=True)
    continuity_checkpoint_parser.add_argument("--file", action="append", default=[])
    continuity_checkpoint_parser.add_argument("--evidence", action="append", default=[])
    continuity_checkpoint_parser.add_argument("--event-id")
    continuity_checkpoint_parser.add_argument("--json", action="store_true")
    continuity_recover_parser = continuity_sub.add_parser("recover")
    continuity_recover_parser.add_argument("session")
    continuity_recover_parser.add_argument("--vault")
    continuity_recover_parser.add_argument("--dry-run", action="store_true", required=True)
    continuity_recover_parser.add_argument("--json", action="store_true")

    coord_parser = sub.add_parser("coordination", help="Project Coordination Plane (MW-2026.09.02 Beta)")
    coord_parser.add_argument("coord_args", nargs=argparse.REMAINDER, help="Arguments passed to coordination_plane")

    skill_parser = sub.add_parser("skill", help="Catálogo y gestión quirúrgica de habilidades")
    skill_sub = skill_parser.add_subparsers(dest="skill_command", required=True)
    skill_cat_parser = skill_sub.add_parser("catalog")
    skill_cat_parser.add_argument("--category")
    skill_cat_parser.add_argument("--vault")
    skill_cat_parser.add_argument("--json", action="store_true")
    skill_act_parser = skill_sub.add_parser("activate")
    skill_act_parser.add_argument("name")
    skill_act_parser.add_argument("--repo")
    skill_act_parser.add_argument("--vault")
    skill_act_parser.add_argument("--json", action="store_true")
    skill_deact_parser = skill_sub.add_parser("deactivate")
    skill_deact_parser.add_argument("name")
    skill_deact_parser.add_argument("--repo")
    skill_deact_parser.add_argument("--vault")
    skill_deact_parser.add_argument("--json", action="store_true")
    skill_audit_parser = skill_sub.add_parser("audit")
    skill_audit_parser.add_argument("--repo")
    skill_audit_parser.add_argument("--vault")
    skill_audit_parser.add_argument("--json", action="store_true")

    dispatch_parser = sub.add_parser("dispatch", help="Despacho atómico inter-proyectos (inbox local)")
    dispatch_sub = dispatch_parser.add_subparsers(dest="dispatch_command", required=True)
    send_parser = dispatch_sub.add_parser("send", help="Enviar nota o artefacto a uno o más proyectos")
    send_parser.add_argument("--to", required=True, help="Destinatario(s) separados por coma: ej. evegat.cl,P020,P061")
    send_parser.add_argument("--from", dest="source", default="harness", help="Proyecto o rol de origen: ej. P050")
    send_parser.add_argument("--title", required=True, help="Título del aviso o entrega")
    send_parser.add_argument("--body", required=True, help="Cuerpo o instrucción para el destinatario")
    send_parser.add_argument("--attach", action="append", default=[], help="Ruta de archivo adjunto para copiar al inbox")
    send_parser.add_argument("--priority", default="normal", choices=["low", "normal", "high", "critical"])
    send_parser.add_argument("--json", action="store_true")

    check_parser = dispatch_sub.add_parser("check", help="Listar notas pendientes en el inbox de un proyecto")
    check_parser.add_argument("--project", required=True, help="Código o alias del proyecto: ej. P020 o evegat.cl")
    check_parser.add_argument("--all", action="store_true", help="Mostrar todas las notas, no solo las pendientes")
    check_parser.add_argument("--json", action="store_true")

    done_parser = dispatch_sub.add_parser("done", help="Marcar una nota del inbox como procesada")
    done_parser.add_argument("file", help="Ruta de la nota a marcar como procesada")
    done_parser.add_argument("--json", action="store_true")

    scan_parser = dispatch_sub.add_parser("scan", help="Escaneo masivo de proyectos con TypeSafe Jev (RLCD)")
    scan_parser.add_argument("--directive", required=True, help="Directiva o criterio de revisión")
    scan_parser.add_argument("--projects", help="Proyectos específicos separados por coma (ej. P020,P028,P061)")
    scan_parser.add_argument("--dispatch", action="store_true", help="Despachar automáticamente nota al inbox de proyectos afectados")
    scan_parser.add_argument("--from", dest="source", default="Auditoria-Masiva", help="Origen del requerimiento")
    scan_parser.add_argument("--json", action="store_true")

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
        elif args.command == "coordination":
            from coordination_plane import main as coord_main
            return coord_main(args.coord_args)
        elif args.command == "skill":
            vault = skill_vault(args.vault)
            target_repo = Path(args.repo).resolve() if getattr(args, "repo", None) else None
            if args.skill_command == "catalog":
                payload = skill_catalog(vault, args.category)
            elif args.skill_command == "activate":
                payload = skill_activate(vault, args.name, target_repo)
            elif args.skill_command == "deactivate":
                payload = skill_deactivate(vault, args.name, target_repo)
            else:
                payload = skill_audit(vault, target_repo)
        elif args.command == "continuity":
            vault = continuity_vault(args.vault)
            if args.continuity_command == "audit":
                payload = continuity_audit(vault, args.stale_after_minutes)
            elif args.continuity_command == "checkpoint":
                payload = continuity_checkpoint(
                    vault,
                    args.session,
                    args.project,
                    args.work_item,
                    args.type,
                    args.next_action,
                    args.file,
                    args.evidence,
                    args.event_id,
                )
            else:
                payload = continuity_recover(vault, args.session)
        elif args.command == "dispatch":
            from project_dispatch import VAULT_ROOT, dispatch_message, list_inbox, mark_processed
            if args.dispatch_command == "send":
                targets = [t.strip() for t in args.to.split(",") if t.strip()]
                res = dispatch_message(
                    targets=targets,
                    source=args.source,
                    title=args.title,
                    body=args.body,
                    attachments=args.attach,
                    priority=args.priority,
                    vault_root=VAULT_ROOT,
                )
                if getattr(args, "json", False):
                    print(json_text(res), end="")
                else:
                    print(f"Harness MyWorld {VERSION} | dispatch:send | OK")
                    for r in res["results"]:
                        print(f"[{r['status'].upper()}] {r['target']} -> {r.get('inbox_note', r.get('error'))}")
                return 0
            elif args.dispatch_command == "check":
                res = list_inbox(args.project, pending_only=not args.all, vault_root=VAULT_ROOT)
                if getattr(args, "json", False):
                    print(json_text(res), end="")
                else:
                    print(f"Harness MyWorld {VERSION} | dispatch:check | {res['count']} notas en {args.project}")
                    for m in res["messages"]:
                        print(f"- [{m['estado'].upper()}] {m['filename']}: {m['title']} (de: {m['origen']})")
                return 0
            elif args.dispatch_command == "done":
                res = mark_processed(args.file)
                if getattr(args, "json", False):
                    print(json_text(res), end="")
                else:
                    print(f"Harness MyWorld {VERSION} | dispatch:done | Nota procesada: {res['file']}")
                return 0
            elif args.dispatch_command == "scan":
                from jev_bulk_scan import scan_portfolio
                targets = [p.strip() for p in args.projects.split(",")] if args.projects else None
                res = scan_portfolio(
                    directive=args.directive,
                    target_projects=targets,
                    auto_dispatch=args.dispatch,
                    source_label=args.source,
                    vault_root=VAULT_ROOT,
                )
                if getattr(args, "json", False):
                    print(json_text(res), end="")
                else:
                    print("=" * 70)
                    print(f"ESCÁNER MASIVO MYWORLD | Motor: Jev RLCD / Fallback | Tiempo: {res['duration_seconds']}s")
                    print(f"Directiva: {res['directive']}")
                    print(f"Escaneados: {res['total_scanned']} | Afectados: {res['applied_count']} | Despachados: {res['dispatched_count']}")
                    print("=" * 70)
                    print(f"{'PROYECTO':<28} | {'APLICA':<7} | {'URGENCIA':<9} | {'PROB':<6} | {'MOTOR'}")
                    print("-" * 70)
                    for r in res["results"]:
                        aplica_txt = "SÍ" if r["aplica"] else "NO"
                        disp_txt = " [ENVIADO]" if r.get("despachado") else ""
                        print(f"{r['name'][:28]:<28} | {aplica_txt:<7} | {r['urgencia']:<9} | {r['probabilidad']:<6} | {r['motor']}{disp_txt}")
                    print("=" * 70)
                return 0
            else:
                payload = {"error": f"Comando dispatch desconocido: {args.dispatch_command}"}
        else:
            repo = repository_root(args.repo)
            if args.command == "preflight":
                payload = preflight(repo)
            elif args.command == "quality":
                payload = quality(repo)
            elif args.command == "security":
                payload = security(repo, args.staged, args.no_external)
            elif args.command == "design":
                payload = design_gate(repo)
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
