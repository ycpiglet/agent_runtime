"""Minimal org/state read-API (org-delegation Unit 562, TASK-AR-562).

Aggregates REAL records (no fabricated data) for a later UI sub-project:
  - org_tree:    teams -> roles (ORG-MODEL.yml) -> live instances (runtime/instances/*.json)
  - work_state:  status counts (waiting/active/review/done) per taskset, with drill-down
  - token_ledger: est vs actual tokens per taskset

Text/JSON only — the visual org chart + characters are UI sub-project #3.
Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (step 6).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from org_model_gate import parse_frontmatter, parse_org_model  # noqa: E402  (stdlib, no PyYAML)

STATUS_BUCKETS = {
    "proposed": "waiting", "planned": "waiting", "worker_ready": "waiting",
    "active": "active", "in_progress": "active",
    "review": "review", "blocked": "review",
    "completed": "done", "closed": "done", "done": "done",
}


def load_org(root: Path = ROOT) -> dict:
    return parse_org_model((root / "agents" / "project" / "ORG-MODEL.yml").read_text(encoding="utf-8"))


def _alias_to_role(reg: dict) -> dict[str, str]:
    m = {}
    for role in reg["roles"]:
        for key in [role["id"], *role.get("aliases", [])]:
            m[str(key).strip().lower()] = role["id"]
    return m


def live_instances(root: Path = ROOT) -> list[dict]:
    d = root / "agents" / "runtime" / "instances"
    out = []
    if d.exists():
        for p in sorted(d.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8", errors="replace")))
            except Exception:
                continue
    return out


def org_tree(root: Path = ROOT) -> dict:
    reg = load_org(root)
    alias = _alias_to_role(reg)
    role_team = {r["id"]: r.get("team", "org") for r in reg["roles"]}
    tree: dict[str, dict] = {t["id"]: {} for t in reg.get("teams", [])}
    for inst in live_instances(root):
        role = alias.get(str(inst.get("role", "")).strip().lower())
        if not role:
            continue
        team = role_team.get(role, "org")
        tree.setdefault(team, {}).setdefault(role, []).append(
            inst.get("display_name") or inst.get("callsign") or inst.get("agent_instance_id", "?")
        )
    return tree


def _front(path: Path) -> dict:
    return parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))


def _task_metas(root: Path) -> list[dict]:
    d = root / "agents" / "lead_engineer" / "tasks"
    return [_front(p) for p in d.glob("TASK-*.md")] if d.exists() else []


def work_state(root: Path = ROOT, taskset_id: str | None = None) -> dict:
    by_set: dict[str, dict] = {}
    for meta in _task_metas(root):
        ts = meta.get("task_set_id")
        if not ts or (taskset_id and ts != taskset_id):
            continue
        bucket = STATUS_BUCKETS.get(str(meta.get("status", "")).lower(), "waiting")
        rec = by_set.setdefault(ts, {"waiting": 0, "active": 0, "review": 0, "done": 0, "tasks": []})
        rec[bucket] += 1
        rec["tasks"].append({"id": meta.get("id"), "status": meta.get("status"), "bucket": bucket})
    return by_set


def token_ledger(root: Path = ROOT) -> dict:
    led: dict[str, dict] = {}
    for meta in _task_metas(root):
        ts = meta.get("task_set_id")
        if not ts:
            continue
        rec = led.setdefault(ts, {"est_tokens": 0, "actual_tokens": 0})
        rec["est_tokens"] += int(meta.get("est_tokens", 0) or 0)
        rec["actual_tokens"] += int(meta.get("actual_tokens", 0) or 0)
    return led


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Org/state read-API (JSON).")
    ap.add_argument("--view", choices=["org", "state", "tokens", "all"], default="all")
    ap.add_argument("--taskset")
    a = ap.parse_args(argv)
    out = {}
    if a.view in ("org", "all"):
        out["org_tree"] = org_tree()
    if a.view in ("state", "all"):
        out["work_state"] = work_state(taskset_id=a.taskset)
    if a.view in ("tokens", "all"):
        out["token_ledger"] = token_ledger()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
