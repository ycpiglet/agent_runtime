from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [
        sys.executable,
        "scripts/taskset_work_gate.py",
        "--task-set-id",
        "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION",
        "--require-complete",
        "--check",
    ],
    [sys.executable, "scripts/owner_governance_gate.py"],
]


def main() -> int:
    for command in COMMANDS:
        result = subprocess.run(command, text=True)
        if result.returncode != 0:
            return result.returncode
    print("session closeout taskset verification: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
