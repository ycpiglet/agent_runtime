"""Attention Inbox derived read (decision-first console IA Unit 1, TASK-AR-563).

Aggregate existing work-item frontmatter + runtime claims into the 6-group
"what needs me now" inbox the cockpit (Unit 2) renders. Read-only; stdlib-only
(repo + CI are PyYAML-free; frontmatter via org_model_gate.parse_frontmatter).
No new storage, no gate execution, no fabricated items.

Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md (§A).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from org_model_gate import parse_frontmatter  # noqa: E402  (stdlib frontmatter parser)

DONE = {"completed", "closed", "done"}
ACTIVE = {"active", "in_progress"}
# Unowned work is "ready but no one has it": planned/ready, not done, no owner/claim.
READY = {"planned", "ready", "todo", "open", "backlog"}
GROUP_ORDER = ["approval_pending", "blocked", "gate_failures", "gate_watch",
               "runtime_anomalies", "cost_anomalies", "stale", "unowned"]

# Decision-first console IA P1 (RFC-2026-06-23): the Owner-chosen urgency order
# for the cockpit's typed attention inbox. Each derived group maps onto one of
# these five tiers; the cockpit ranks items by (tier, severity).
RANK_TIERS = ["gate", "blocked", "stale", "risk", "unowned"]
GROUP_TIER = {
    "approval_pending": "gate",   # owner gate awaiting approval
    "gate_failures": "gate",      # failed gate
    "gate_watch": "gate",         # gate in watch state (low-emphasis, TASK-AR-630)
    "blocked": "blocked",         # blocked chain
    "stale": "stale",             # stale claim / no update
    "runtime_anomalies": "risk",  # cross-host claim conflict
    "cost_anomalies": "risk",     # budget breach (at-risk)
    "unowned": "unowned",         # ready work, no owner
}


def _load_tasks(tasks_dir: Path) -> list[dict]:
    return [parse_frontmatter(Path(p).read_text(encoding="utf-8", errors="replace"))
            for p in glob.glob(str(tasks_dir / "TASK-*.md"))]


def _item(group: str, meta: dict, why: str, action: str, *, severity: int = 1, age_days: int = 0) -> dict:
    return {"group": group, "id": meta.get("id"),
            "title": meta.get("title") or meta.get("id"),
            "why": why, "age_days": age_days, "severity": severity, "action": action}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_dt(value):
    try:
        return _dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def approval_pending(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        if str(m.get("approval_required", "")).lower() in ("true", "1", "yes") \
                and str(m.get("status", "")).lower() not in DONE:
            out.append(_item("approval_pending", m, "approval_required", "approve / gate", severity=3))
    return out


def blocked(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        st = str(m.get("status", "")).lower()
        if st == "blocked" or (m.get("blocked_by") and st not in DONE):
            out.append(_item("blocked", m, f"status={st or 'blocked'}", "resolve blocker", severity=2))
    return out


def gate_failures(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        n = _num(m.get("gate_failure_count"))
        if n and n > 0:
            out.append(_item("gate_failures", m, f"{int(n)} gate failures", "fix gate", severity=2))
    return out


def cost_anomalies(tasks: list[dict]) -> list[dict]:
    out = []
    for m in tasks:
        est, act, cap = _num(m.get("est_tokens")), _num(m.get("actual_tokens")), _num(m.get("budget_cap"))
        if act is not None and ((est is not None and act > est) or (cap is not None and act > cap)):
            out.append(_item("cost_anomalies", m, f"actual {int(act)} > budget", "review cost", severity=2))
    return out


def stale(tasks: list[dict], *, now, stale_days: int = 7) -> list[dict]:
    out = []
    for m in tasks:
        if str(m.get("status", "")).lower() not in ACTIVE:
            continue
        ts = _parse_dt(m.get("updated_at"))
        if ts is None:
            continue
        age = (now - ts).days
        if age >= stale_days:
            out.append(_item("stale", m, f"no update {age}d", "review / refresh", severity=1, age_days=age))
    return out


def unowned(tasks: list[dict]) -> list[dict]:
    """Ready/planned work that nobody owns yet (RFC 'unowned' attention tier)."""
    out = []
    for m in tasks:
        st = str(m.get("status", "")).lower()
        if st in DONE or st not in READY:
            continue
        owner = str(m.get("owner", "")).strip().lower()
        if owner and owner not in ("none", "unassigned", "tbd"):
            continue
        out.append(_item("unowned", m, "ready, no owner", "assign owner", severity=1))
    return out


def _gate_record_newer(new: tuple, prev: tuple) -> bool:
    """Recency for gate records: parsed-datetime order when both records carry a
    stamp (tz-aware, so mixed offsets compare correctly); file-order fallback
    when either side lacks one, so a recovery record without generated_at still
    supersedes an older watch instead of leaving it stuck (W4b, TASK-AR-630)."""
    new_epoch, new_index = new
    prev_epoch, prev_index = prev
    if new_epoch is not None and prev_epoch is not None:
        return (new_epoch, new_index) >= (prev_epoch, prev_index)
    return new_index >= prev_index


def gate_watch(root: Path) -> list[dict]:
    """Gates whose LATEST record is in the watch state (TASK-AR-630).

    The masterplan gap: watch-state gate signals (e.g. compound_cadence ratio
    over threshold) lived only in reviews/*GATE*.json and never reached the
    cockpit, so the Owner saw block-or-nothing. Promote them as low-severity
    (severity 0) items in the gate tier — visible, but quiet. Only the newest
    record per gate kind counts: a gate that recovered to pass emits nothing.
    """
    reviews_dir = root / "reviews"
    if not reviews_dir.is_dir():
        return []
    # W4b(630): order records by parsed datetime when possible (tz-aware, so
    # mixed offsets compare correctly); records with no/unparseable stamp fall
    # back to file-order recency so a recovered pass without generated_at still
    # supersedes an older watch instead of leaving it stuck forever.
    latest: dict[str, tuple[tuple, str]] = {}  # kind -> (order_key, status)
    for index, path in enumerate(sorted(reviews_dir.glob("*GATE*.json"))):
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        status = str(data.get("status") or data.get("result") or "").strip().lower()
        schema = str(data.get("schema") or "")
        kind = schema.split("/")[0].replace("agent-runtime-", "") if schema else path.stem
        parsed = _parse_dt(data.get("generated_at"))
        if parsed is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_dt.timezone.utc)
        epoch = parsed.timestamp() if parsed is not None else None
        prev = latest.get(kind)
        if prev is None or _gate_record_newer((epoch, index), prev[0]):
            latest[kind] = ((epoch, index), status)
    out = []
    for kind in sorted(latest):
        _order, status = latest[kind]
        if status != "watch":
            continue
        out.append({"group": "gate_watch", "id": kind, "title": kind,
                    "why": "latest gate record is watch", "age_days": 0,
                    "severity": 0, "action": "review gate"})
    return out


def _claim_conflicts(root: Path):
    try:
        from multi_host_claim_gate import detect_conflicts, load_claims
        return detect_conflicts(load_claims(root / "agents" / "runtime" / "task_claims"))
    except Exception:
        return []


def runtime_anomalies(root: Path) -> list[dict]:
    out = []
    for c in _claim_conflicts(root):
        out.append({"group": "runtime_anomalies", "id": c.get("resource"),
                    "title": c.get("resource"),
                    "why": "cross-host claim conflict: " + ",".join(c.get("hosts", [])),
                    "age_days": 0, "severity": 3, "action": "resolve claim"})
    return out


def inbox(root: Path, *, now=None, stale_days: int = 7) -> dict:
    now = now or _dt.datetime.now(_dt.timezone.utc).astimezone()
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks = _load_tasks(tasks_dir) if tasks_dir.exists() else []
    groups = {
        "approval_pending": approval_pending(tasks),
        "blocked": blocked(tasks),
        "gate_failures": gate_failures(tasks),
        "gate_watch": gate_watch(root),
        "runtime_anomalies": runtime_anomalies(root),
        "cost_anomalies": cost_anomalies(tasks),
        "stale": stale(tasks, now=now, stale_days=stale_days),
        "unowned": unowned(tasks),
    }
    for items in groups.values():
        items.sort(key=lambda i: i["severity"], reverse=True)
    counts = {g: len(groups[g]) for g in GROUP_ORDER}
    return {"groups": {g: groups[g] for g in GROUP_ORDER}, "counts": counts,
            "total": sum(counts.values()),
            "rank_order": list(RANK_TIERS), "ranked": _ranked(groups)}


def _ranked(groups: dict[str, list[dict]]) -> list[dict]:
    """Flatten the typed groups into the Owner-chosen urgency order.

    Items are ordered by tier (gate > blocked > stale > risk > unowned), then by
    severity (desc) within a tier. Each item gets a ``rank`` tier tag so the
    cockpit can render the ranked inbox without re-deriving the order.
    """
    flat: list[dict] = []
    seen: set = set()
    for tier_index, tier in enumerate(RANK_TIERS):
        tier_items = []
        for group, items in groups.items():
            if GROUP_TIER.get(group) != tier:
                continue
            for item in items:
                # An item surfaced by a higher tier is not re-listed in a lower
                # one (e.g. a gate-pending task is not also reported as unowned).
                key = item.get("id")
                if key is not None and key in seen:
                    continue
                if key is not None:
                    seen.add(key)
                tier_items.append({**item, "rank": tier, "rank_index": tier_index})
        tier_items.sort(key=lambda i: i["severity"], reverse=True)
        flat.extend(tier_items)
    return flat


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Attention inbox (what needs a human now).")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    data = inbox(ROOT)
    if a.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"attention-inbox: {data['total']} items needing attention" if data["total"]
              else "attention-inbox: nothing needs you")
        for g, n in data["counts"].items():
            if n:
                print(f"  {g}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
