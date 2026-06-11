from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
TASK_SET_ID = "TASKSET-AR-RSI-OPERATING-SYSTEM"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [".", "src"]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run(
    command: list[str],
    *,
    expect_json_status: str | None = None,
    allow_returncodes: set[int] | None = None,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=_env(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    allowed = allow_returncodes or {0}
    record: dict[str, Any] = {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode not in allowed:
        record["status"] = "failed"
        return record
    if expect_json_status is not None:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            record["status"] = "failed"
            record["error"] = "stdout was not JSON"
            return record
        record["json"] = payload
        if payload.get("status") != expect_json_status:
            record["status"] = "failed"
            record["error"] = f"expected JSON status {expect_json_status}, got {payload.get('status')}"
            return record
    record["status"] = "passed"
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Verify {TASK_SET_ID} before closeout")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    checks = [
        run(
            [
                PYTHON,
                "-m",
                "py_compile",
                "scripts/planning_loop.py",
                "scripts/a2a_lifecycle_gate.py",
                "scripts/verify_rsi_operating_system_taskset.py",
            ]
        ),
        run(
            [
                PYTHON,
                "-m",
                "pytest",
                "tests/test_rsi_operating_system_docs.py",
                "tests/test_a2a_lifecycle_gate.py",
                "tests/test_planning_loop.py",
                "-q",
            ]
        ),
        run([PYTHON, "scripts/a2a_lifecycle_gate.py", "--json", "--write-record"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_loop.py", "gate", "--trigger", "manual", "--action", "scan", "--json"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_loop.py", "c-mode-gate", "--json"], expect_json_status="block", allow_returncodes={1}),
        run([PYTHON, "scripts/backlog_board.py", "--write"]),
        run([PYTHON, "scripts/owner_doc_format_gate.py", "--manifest", "owner-docs.yml"]),
        run([PYTHON, "scripts/task_identity.py", "check", "--check"]),
        run(
            [
                PYTHON,
                "scripts/taskset_work_gate.py",
                "--task-set-id",
                TASK_SET_ID,
                "--require-complete",
                "--check",
            ]
        ),
    ]
    failed = [check for check in checks if check.get("status") != "passed"]
    report = {
        "status": "pass" if not failed else "block",
        "task_set_id": TASK_SET_ID,
        "checks": checks,
        "failed_count": len(failed),
    }
    if args.out:
        out = ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
