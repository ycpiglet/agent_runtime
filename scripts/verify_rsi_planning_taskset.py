from __future__ import annotations

import json
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def _env() -> dict[str, str]:
    env = os.environ.copy()
    paths = [".", "src"]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run(command: list[str], *, expect_json_status: str | None = None, allow_returncodes: set[int] | None = None) -> dict[str, object]:
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
    record: dict[str, object] = {
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify TASKSET-AR-RSI-PLANNING before closeout")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    checks = [
        run(
            [
                PYTHON,
                "-m",
                "py_compile",
                "scripts/planning_loop.py",
                "scripts/planning_trigger.py",
                "scripts/release_version_consistency_steward.py",
                "scripts/close_rsi_planning_taskset.py",
            ]
        ),
        run(
            [
                PYTHON,
                "-m",
                "pytest",
                "tests/test_planning_loop.py",
                "tests/test_release_version_consistency_steward.py",
                "tests/test_planning_ui.py",
                "-q",
            ]
        ),
        run([PYTHON, "scripts/planning_loop.py", "gate", "--trigger", "manual", "--action", "scan", "--json"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_loop.py", "gate", "--trigger", "ui", "--action", "scan", "--json"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_loop.py", "dedupe-outbox", "--json"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_trigger.py", "--trigger", "schedule", "--json"], expect_json_status="pass"),
        run([PYTHON, "scripts/planning_loop.py", "c-mode-gate", "--json"], expect_json_status="block", allow_returncodes={1}),
        run([PYTHON, "scripts/backlog_board.py", "--write"]),
        run([PYTHON, "scripts/owner_governance_gate.py"]),
        run([PYTHON, "scripts/taskset_work_gate.py", "--task-set-id", "TASKSET-AR-RSI-PLANNING", "--check"]),
    ]
    failed = [check for check in checks if check.get("status") != "passed"]
    report = {
        "status": "pass" if not failed else "block",
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
