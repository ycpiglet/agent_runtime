"""Read-only census for multi-pane runtime collaboration evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"active", "assigned", "claimed", "in_progress", "review", "running", "waiting_review", "working"}
CLAIMS_DIR = Path("agents/runtime/task_claims")
PANE_EVENTS = Path("agents/runtime/pane_events/pane-events.jsonl")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON record must be an object")
    return value


def _load_claims(root: Path, findings: list[str], data_gaps: list[str]) -> list[dict[str, Any]]:
    claim_dir = root / CLAIMS_DIR
    if not claim_dir.is_dir():
        data_gaps.append(CLAIMS_DIR.as_posix())
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claim_dir.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            findings.append(f"claim:invalid:{_rel(root, path)}:{exc}")
            continue
        payload["_source_path"] = _rel(root, path)
        claims.append(payload)
    return claims


def _load_pane_events(root: Path, findings: list[str], data_gaps: list[str]) -> list[dict[str, Any]]:
    path = root / PANE_EVENTS
    if not path.exists():
        data_gaps.append(PANE_EVENTS.parent.as_posix())
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(f"pane-event:invalid-json:{_rel(root, path)}:{line_number}:{exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"pane-event:invalid-record:{_rel(root, path)}:{line_number}")
            continue
        payload["_source_path"] = f"{_rel(root, path)}:{line_number}"
        events.append(payload)
    return events


def _claim_record(root: Path, claim: dict[str, Any], event_counts: Counter[str]) -> dict[str, Any]:
    worktree = str(claim.get("worktree_path") or "").strip()
    handoff = str(claim.get("handoff_path") or "").strip()
    return {
        "claim_id": claim.get("claim_id") or "",
        "task_id": claim.get("task_id") or "",
        "task_set_id": claim.get("task_set_id") or "",
        "agent_role": claim.get("agent_role") or "",
        "status": claim.get("status") or "",
        "phase": claim.get("phase") or "",
        "progress_pct": claim.get("progress_pct"),
        "worktree_path": worktree,
        "branch": claim.get("branch") or "",
        "last_heartbeat": claim.get("last_heartbeat") or "",
        "handoff_path": handoff,
        "log_path": claim.get("log_path") or "",
        "source_path": claim.get("_source_path") or "",
        "missing_worktree": bool(worktree and not (root / worktree).exists()),
        "missing_handoff": bool(handoff and not (root / handoff).exists()),
        "event_count": event_counts.get(str(claim.get("claim_id") or ""), 0),
    }


def build_report(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    findings: list[str] = []
    data_gaps: list[str] = []
    raw_claims = _load_claims(root_path, findings, data_gaps)
    events = _load_pane_events(root_path, findings, data_gaps)
    event_counts = Counter(str(event.get("claim_id") or "") for event in events if str(event.get("claim_id") or "").strip())
    claims = [_claim_record(root_path, claim, event_counts) for claim in raw_claims]
    active = [claim for claim in claims if str(claim.get("status") or "").lower() in ACTIVE_STATUSES]
    historical = [claim for claim in claims if claim not in active]

    task_sets: dict[str, dict[str, Any]] = {}
    for claim in claims:
        task_set_id = str(claim.get("task_set_id") or "unassigned")
        group = task_sets.setdefault(
            task_set_id,
            {"task_set_id": task_set_id, "claims_total": 0, "active": 0, "historical": 0, "roles": {}},
        )
        group["claims_total"] += 1
        if claim in active:
            group["active"] += 1
        else:
            group["historical"] += 1
        role = str(claim.get("agent_role") or "unknown")
        group["roles"][role] = group["roles"].get(role, 0) + 1

    status = "block" if any(item.startswith(("claim:invalid", "pane-event:invalid")) for item in findings) else "pass"
    if status == "pass" and (findings or data_gaps):
        status = "watch"
    return {
        "schema": "agent-runtime-multipane-census/v1",
        "status": status,
        "claims_total": len(claims),
        "active_claims": len(active),
        "historical_claims": len(historical),
        "active_panes_threshold": 5,
        "active_panes_threshold_met": len(active) >= 5,
        "pane_events": len(events),
        "missing_worktree_count": sum(1 for claim in claims if claim["missing_worktree"]),
        "missing_handoff_count": sum(1 for claim in claims if claim["missing_handoff"]),
        "data_gaps": data_gaps,
        "findings": findings,
        "active": active,
        "historical": historical,
        "task_sets": task_sets,
    }


def render_text(report: dict[str, Any], root: Path) -> str:
    lines = [
        f"multipane-census: {report['status']}",
        f"root={root.resolve()}",
        f"claims_total={report['claims_total']}",
        f"active_claims={report['active_claims']}",
        f"historical_claims={report['historical_claims']}",
        f"pane_events={report['pane_events']}",
        f"active_panes_threshold_met={str(report['active_panes_threshold_met']).lower()}",
    ]
    for gap in report["data_gaps"]:
        lines.append(f"- data-gap {gap}")
    for finding in report["findings"]:
        lines.append(f"- {finding}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build multi-pane runtime census")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_text(report, args.root))
    return 1 if args.check and report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
