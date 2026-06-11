"""Run focused closeout checks for TASKSET-AR-RSI-OPERATING-SYSTEM."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKSET_ID = "TASKSET-AR-RSI-OPERATING-SYSTEM"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [str(ROOT / "scripts"), str(ROOT / "src")]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


COMMANDS = [
    [
        sys.executable,
        "-m",
        "py_compile",
        "scripts/planning_loop.py",
        "scripts/a2a_lifecycle_gate.py",
        "scripts/verify_rsi_operating_system_taskset.py",
    ],
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_rsi_operating_system_docs.py",
        "tests/test_a2a_lifecycle_gate.py",
        "tests/test_planning_loop.py",
        "-q",
    ],
    [sys.executable, "scripts/a2a_lifecycle_gate.py", "--check"],
    [sys.executable, "scripts/planning_loop.py", "gate", "--trigger", "manual", "--action", "scan", "--json"],
    [sys.executable, "scripts/planning_loop.py", "metrics", "--json"],
    [sys.executable, "scripts/owner_doc_format_gate.py", "--manifest", "owner-docs.yml"],
    [sys.executable, "scripts/task_identity.py", "check", "--check"],
    [
        sys.executable,
        "scripts/taskset_work_gate.py",
        "--task-set-id",
        TASKSET_ID,
        "--require-complete",
        "--check",
    ],
    [sys.executable, "scripts/evidence_index_generator.py", "--check"],
]


def _run(command: list[str]) -> int:
    print("== " + " ".join(command) + " ==")
    result = subprocess.run(command, cwd=ROOT, env=_env(), check=False)
    if result.returncode != 0:
        print(f"RSI operating-system verification failed: {result.returncode}")
    return result.returncode


def _run_expected_c_mode_block() -> int:
    command = [sys.executable, "scripts/planning_loop.py", "c-mode-gate", "--json"]
    print("== " + " ".join(command) + " ==")
    result = subprocess.run(command, cwd=ROOT, env=_env(), capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("RSI operating-system verification failed: c-mode-gate did not emit JSON")
        return 1
    if payload.get("status") != "block":
        print(f"RSI operating-system verification failed: expected c-mode block, got {payload.get('status')}")
        return 1
    if not payload.get("reasons"):
        print("RSI operating-system verification failed: expected c-mode block reasons")
        return 1
    return 0


def main() -> int:
    for command in COMMANDS:
        code = _run(command)
        if code != 0:
            return code
    code = _run_expected_c_mode_block()
    if code != 0:
        return code
    print("RSI operating-system taskset verification: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

