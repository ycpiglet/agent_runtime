"""Run focused closeout checks for TASKSET-AR-PM-OPERATING-SYSTEM."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKSET_ID = "TASKSET-AR-PM-OPERATING-SYSTEM"


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
        "scripts/model_routing.py",
        "scripts/task_unit_readiness_gate.py",
        "scripts/task_claim_dispatcher.py",
        "scripts/taskset_dispatcher.py",
        "scripts/backlog_board.py",
        "scripts/taskset_work_gate.py",
        "scripts/verify_pm_operating_system_taskset.py",
    ],
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_model_routing.py",
        "tests/test_task_unit_readiness_gate.py",
        "tests/test_task_claim_dispatcher.py",
        "tests/test_taskset_dispatcher.py",
        "tests/test_backlog_board_tasksets.py",
        "tests/test_taskset_work_gate.py",
        "tests/test_template_smoke.py",
        "-q",
    ],
    [
        sys.executable,
        "scripts/task_unit_readiness_gate.py",
        "--task-id",
        "TASK-AR-350",
        "--require-ready",
        "--check",
    ],
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
]


def main() -> int:
    for command in COMMANDS:
        print("== " + " ".join(command) + " ==")
        result = subprocess.run(command, cwd=ROOT, env=_env(), check=False)
        if result.returncode != 0:
            print(f"pm operating-system verification failed: {result.returncode}")
            return result.returncode
    print("pm operating-system taskset verification: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
