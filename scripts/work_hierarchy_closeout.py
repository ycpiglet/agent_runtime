"""Work-hierarchy conflict-surface closeout gate (TASK-AR-374, Phase 5).

A single closeout wrapper that runs the registration/identity/owner-doc/taskset gates
and the unit-readiness report, so the taskset's "conflict surfaces are closed" claim is
proven by executable evidence rather than prose. Exits non-zero if any gate fails.

Stdlib-only; subprocess output decoded utf-8/replace (Windows cp949 safety).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
TASKSET = "TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE"

GATES: list[list[str]] = [
    [PY, "scripts/task_identity.py", "check", "--check"],
    [PY, "scripts/work_item_classifier.py", "--check"],
    [PY, "scripts/owner_doc_format_gate.py", "--manifest", "owner-docs.yml"],
    [PY, "scripts/taskset_work_gate.py", "--task-set-id", TASKSET, "--require-complete", "--check"],
    [PY, "scripts/unit_readiness_report.py"],
]


def run_gates(gates: list[list[str]], root: Path = ROOT) -> list[dict]:
    results = []
    for cmd in gates:
        try:
            r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
            ok, rc = r.returncode == 0, r.returncode
        except (OSError, subprocess.SubprocessError) as exc:
            ok, rc = False, f"error:{exc}"
        results.append({"cmd": " ".join(str(c) for c in cmd[1:]), "rc": rc, "ok": ok})
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the work-hierarchy closeout gate chain.")
    ap.parse_args(argv)
    results = run_gates(GATES)
    for r in results:
        print(f"{'PASS' if r['ok'] else 'FAIL'} {r['cmd']}")
    failed = [r for r in results if not r["ok"]]
    print(f"work-hierarchy-closeout: {len(results) - len(failed)}/{len(results)} gates pass")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
