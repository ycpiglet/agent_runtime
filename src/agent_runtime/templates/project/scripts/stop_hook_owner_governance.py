"""Stop hook wrapper for the Owner governance gate.

The governance gate prints human-readable logs. Stop hooks only emit structured
JSON when they need to block; successful stops stay silent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

import stop_hook_session_scope


ROOT = Path(__file__).resolve().parents[1]
MAX_MESSAGE_CHARS = 6000
HOOK_LOG_DIR_ENV = "AGENT_RUNTIME_HOOK_LOG_DIR"


def _clip(text: str) -> str:
    if len(text) <= MAX_MESSAGE_CHARS:
        return text
    return text[:MAX_MESSAGE_CHARS] + "\n...[truncated]"


def _run_gate() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/owner_governance_gate.py", "--allow-empty-owner-docs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _hook_log_dir() -> Path:
    override = os.environ.get(HOOK_LOG_DIR_ENV)
    if override:
        return Path(override)
    return ROOT / ".codex" / "hook-logs"


def _selected_env() -> dict[str, str | None]:
    return {
        "PYTHON_EXE": os.environ.get("PYTHON_EXE"),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "AGENT_RUNTIME_RSI_DISABLE": os.environ.get("AGENT_RUNTIME_RSI_DISABLE"),
        "SOURCE_DATE_EPOCH": os.environ.get("SOURCE_DATE_EPOCH"),
    }


def write_diagnostic(result: subprocess.CompletedProcess[str], payload: dict[str, str], *, log_dir: Path | None = None) -> Path | None:
    directories = [log_dir or _hook_log_dir()]
    fallback = ROOT / "agents" / "runtime" / "hook-logs"
    if fallback not in directories:
        directories.append(fallback)
    for directory in directories:
        try:
            path = _write_diagnostic_file(directory, result, payload)
            return path
        except OSError:
            continue
    return None


def _write_diagnostic_file(directory: Path, result: subprocess.CompletedProcess[str], payload: dict[str, str]) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = directory / f"stop-owner-governance-{stamp}-{os.getpid()}.json"
        diagnostic: dict[str, Any] = {
            "schema": "agent-runtime-stop-hook-diagnostic/v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "root": str(ROOT),
            "cwd": os.getcwd(),
            "sys_executable": sys.executable,
            "python_version": sys.version,
            "argv": sys.argv,
            "env": _selected_env(),
            "command": list(result.args) if isinstance(result.args, (list, tuple)) else result.args,
            "returncode": result.returncode,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "payload": payload,
        }
        path.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def build_payload(result: subprocess.CompletedProcess[str], *, diagnostic_path: Path | None = None) -> dict[str, str]:
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    prefix = f"hook diagnostic: {diagnostic_path}\n" if diagnostic_path else ""
    if result.returncode == 0:
        return {
            "decision": "approve",
            "reason": "owner governance gate passed",
            "systemMessage": _clip(prefix + output),
        }
    return {
        "decision": "block",
        "reason": f"owner governance gate failed with code {result.returncode}",
        "systemMessage": _clip(prefix + output),
    }


def emit_stop_payload(payload: dict[str, str]) -> None:
    if payload.get("decision") == "block":
        print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    scope = stop_hook_session_scope.assess(stop_hook_session_scope.read_hook_input(), root=ROOT)
    if scope.get("bypass"):
        return 0
    result = _run_gate()
    payload = build_payload(result)
    diagnostic_path = write_diagnostic(result, payload)
    if diagnostic_path is not None:
        payload = build_payload(result, diagnostic_path=diagnostic_path)
        write_diagnostic(result, payload, log_dir=diagnostic_path.parent)
    emit_stop_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
