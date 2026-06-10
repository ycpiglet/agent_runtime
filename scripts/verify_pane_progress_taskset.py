"""Run the focused TASKSET-AR-PANE-PROGRESS closeout checks.

This script is intentionally a thin wrapper around the exact verification
commands recorded in the task-set review. It is not run automatically by
generating it; execute it only when verification is explicitly approved.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [".", "src"]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _run(label: str, command: list[str]) -> int:
    print(f"== {label} ==")
    print(" ".join(command))
    result = subprocess.run(command, cwd=ROOT, env=_env(), check=False)
    if result.returncode != 0:
        print(f"{label}: failed ({result.returncode})")
        return result.returncode
    print(f"{label}: passed")
    return 0


def main() -> int:
    checks = (
        (
            "focused pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_ui_state.py",
                "tests/test_ui_console.py",
                "tests/test_task_claim_dispatcher.py",
                "tests/test_continuity_contract_gate.py",
                "-q",
            ],
        ),
        (
            "taskset work gate",
            [sys.executable, "scripts/taskset_work_gate.py", "--check"],
        ),
        (
            "continuity contract gate",
            [sys.executable, "scripts/continuity_contract_gate.py", "--check"],
        ),
    )
    for label, command in checks:
        code = _run(label, command)
        if code != 0:
            return code
    print("pane-progress taskset verification: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
