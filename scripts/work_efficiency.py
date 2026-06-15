"""Actual-metrics capture + multi-factor work evaluation (TASK-AR-368).

The work-schema already carries est_*/actual_*/team; work.py close records actuals.
This adds the *evaluation* layer the Owner asked for ("low token use yet high maturity"):
per-item efficiency (outcome per cost) + est-vs-actual variance, sortable/filterable by
priority, difficulty, tokens, hours, team, variance, and efficiency.

Read-only over task frontmatter. Stdlib-only (CI is PyYAML-free).
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
DELIVERED = {"completed", "closed", "done"}
SORT_KEYS = ("actual_tokens", "actual_hours", "token_variance", "hour_variance",
             "efficiency", "priority", "difficulty", "team")


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def item_metrics(meta: dict) -> dict:
    est_t, act_t = _num(meta.get("est_tokens")), _num(meta.get("actual_tokens"))
    est_h, act_h = _num(meta.get("est_hours")), _num(meta.get("actual_hours"))
    delivered = str(meta.get("status", "")).lower() in DELIVERED
    token_var = (est_t - act_t) if (est_t is not None and act_t is not None) else None
    hour_var = (est_h - act_h) if (est_h is not None and act_h is not None) else None
    # efficiency = outcome (delivered) per cost (actual tokens); higher is better.
    efficiency = None
    if delivered and act_t and act_t > 0:
        efficiency = round(1000.0 / act_t, 4)        # delivered units per 1k tokens
    return {
        "id": meta.get("id"),
        "status": meta.get("status"),
        "team": meta.get("team") or meta.get("owner"),
        "priority": meta.get("priority"),
        "difficulty": meta.get("difficulty"),
        "est_tokens": est_t, "actual_tokens": act_t, "token_variance": token_var,
        "est_hours": est_h, "actual_hours": act_h, "hour_variance": hour_var,
        "delivered": delivered, "efficiency": efficiency,
    }


def evaluate(tasks_dir: Path = TASKS, *, taskset: str | None = None) -> list[dict]:
    out = []
    for p in sorted(tasks_dir.glob("TASK-*.md")):
        meta = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if taskset and meta.get("task_set_id") != taskset:
            continue
        out.append(item_metrics(meta))
    return out


def rank(rows: list[dict], by: str = "efficiency", *, desc: bool = True) -> list[dict]:
    if by not in SORT_KEYS:
        raise ValueError(f"unknown sort key {by!r}; choose from {SORT_KEYS}")
    # Two-pass so missing values sort LAST regardless of direction (desc would
    # otherwise flip a None-flag and float them to the top).
    present = [r for r in rows if r.get(by) is not None]
    absent = [r for r in rows if r.get(by) is None]
    present.sort(key=lambda r: r[by], reverse=desc)
    return present + absent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate work items by actuals/efficiency.")
    ap.add_argument("--sort", choices=SORT_KEYS, default="efficiency")
    ap.add_argument("--taskset")
    ap.add_argument("--delivered-only", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = evaluate(taskset=a.taskset)
    if a.delivered_only:
        rows = [r for r in rows if r["delivered"]]
    rows = rank(rows, by=a.sort)
    if a.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        print(f"work-efficiency: {len(rows)} items sorted by {a.sort}")
        for r in rows[:25]:
            print(f"  {r['id']}  eff={r['efficiency']}  act_tok={r['actual_tokens']}  "
                  f"tok_var={r['token_variance']}  team={r['team']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
