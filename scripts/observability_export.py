"""External observability export (TASK-AR-553, product-maturity-uplift).

Aggregate runtime metrics from real records (task frontmatter, claims, pane/runtime
events) and export them for external scrapers — JSON or Prometheus text exposition
format. Read-only; stdlib-only (the repo + CI are PyYAML-free).
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
CLAIMS = ROOT / "agents" / "runtime" / "task_claims"
INSTANCES = ROOT / "agents" / "runtime" / "instances"
DONE = {"completed", "closed", "done"}
ACTIVE = {"active", "in_progress"}


def collect(root: Path = ROOT) -> dict:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    by_status: dict[str, int] = {}
    est_tokens = actual_tokens = 0
    for p in tasks_dir.glob("TASK-*.md"):
        meta = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        st = str(meta.get("status", "unknown")).lower()
        by_status[st] = by_status.get(st, 0) + 1
        est_tokens += int(meta.get("est_tokens", 0) or 0)
        actual_tokens += int(meta.get("actual_tokens", 0) or 0)
    claims_dir = root / "agents" / "runtime" / "task_claims"
    claims = len(list(claims_dir.glob("CLAIM-*.json"))) if claims_dir.exists() else 0
    inst_dir = root / "agents" / "runtime" / "instances"
    instances = len(list(inst_dir.glob("*.json"))) if inst_dir.exists() else 0
    done = sum(by_status.get(s, 0) for s in DONE)
    active = sum(by_status.get(s, 0) for s in ACTIVE)
    total = sum(by_status.values())
    return {
        "tasks_total": total,
        "tasks_done": done,
        "tasks_active": active,
        "tasks_by_status": by_status,
        "claims_total": claims,
        "instances_total": instances,
        "est_tokens_total": est_tokens,
        "actual_tokens_total": actual_tokens,
        "completion_ratio": round(done / total, 4) if total else 0.0,
    }


def to_prometheus(metrics: dict) -> str:
    lines = []
    def emit(name, value, help_):
        lines.append(f"# HELP agent_runtime_{name} {help_}")
        lines.append(f"# TYPE agent_runtime_{name} gauge")
        lines.append(f"agent_runtime_{name} {value}")
    emit("tasks_total", metrics["tasks_total"], "Total work items")
    emit("tasks_done", metrics["tasks_done"], "Completed/closed/done work items")
    emit("tasks_active", metrics["tasks_active"], "Active/in-progress work items")
    emit("claims_total", metrics["claims_total"], "Runtime task claims on disk")
    emit("instances_total", metrics["instances_total"], "Agent instance records")
    emit("est_tokens_total", metrics["est_tokens_total"], "Sum of estimated tokens")
    emit("actual_tokens_total", metrics["actual_tokens_total"], "Sum of actual tokens")
    emit("completion_ratio", metrics["completion_ratio"], "Done / total work items")
    for status, n in sorted(metrics["tasks_by_status"].items()):
        safe = "".join(c if c.isalnum() else "_" for c in status)
        lines.append(f'agent_runtime_tasks_status{{status="{safe}"}} {n}')
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export runtime observability metrics.")
    ap.add_argument("--format", choices=["json", "prometheus"], default="json")
    ap.add_argument("--out", help="write to a file instead of stdout")
    a = ap.parse_args(argv)
    metrics = collect()
    text = (json.dumps(metrics, indent=2, ensure_ascii=False) if a.format == "json"
            else to_prometheus(metrics))
    if a.out:
        Path(a.out).write_text(text.rstrip("\n") + "\n", encoding="utf-8")  # exactly one trailing newline
        print(f"observability: {a.format} metrics written to {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
