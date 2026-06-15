"""Unit-readiness migration report (TASK-AR-373, work-hierarchy closure Phase 5).

Make it visible which planned tasks are already worker-ready (have unit specs that
pass the readiness gate) and which still need planner refinement into units before
dispatch. Read-only report over real task frontmatter + the units/ tree.

Stdlib-only (CI runs PyYAML-free): frontmatter is parsed via org_model_gate.parse_frontmatter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from org_model_gate import parse_frontmatter  # noqa: E402  (stdlib, no PyYAML)

TASKS = ROOT / "agents" / "lead_engineer" / "tasks"
UNITS = TASKS / "units"
# Statuses that still need planner refinement / dispatch (not yet done/active).
PENDING = {"proposed", "planned"}


def _unit_files(task_id: str, units_root: Path = UNITS) -> list[Path]:
    d = units_root / task_id
    return sorted(d.glob("UNIT-*.md")) if d.exists() else []


def report(tasks_dir: Path = TASKS, units_root: Path = UNITS) -> dict:
    has_units: list[dict] = []
    needs_refinement: list[str] = []
    for p in sorted(tasks_dir.glob("TASK-*.md")):
        meta = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        status = str(meta.get("status", "")).lower()
        if status not in PENDING:
            continue
        units = _unit_files(meta.get("id", p.stem), units_root)
        if units:
            ready = sum(1 for u in units
                        if str(parse_frontmatter(u.read_text(encoding="utf-8", errors="replace"))
                                .get("status", "")).lower() in {"worker_ready", "ready", "in_progress", "completed"})
            has_units.append({"task": meta.get("id", p.stem), "units": len(units), "worker_ready": ready})
        else:
            needs_refinement.append(meta.get("id", p.stem))
    return {
        "pending_total": len(has_units) + len(needs_refinement),
        "with_worker_ready_units": has_units,
        "needs_refinement": needs_refinement,
        "summary": {
            "ready_to_dispatch": len(has_units),
            "needs_planner_refinement": len(needs_refinement),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report planned tasks' unit readiness.")
    ap.add_argument("--json", action="store_true", help="emit JSON (default: summary text)")
    a = ap.parse_args(argv)
    r = report()
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        s = r["summary"]
        print(f"unit-readiness: {s['ready_to_dispatch']} ready-to-dispatch, "
              f"{s['needs_planner_refinement']} need refinement (of {r['pending_total']} pending)")
        for t in r["needs_refinement"]:
            print(f"  needs-units: {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
