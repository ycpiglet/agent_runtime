"""Append-only pane collaboration event log.

The log records pane/worktree/task-set coordination events without mutating
canonical SSoT documents. Derived views can replay this file together with task
claims and task markdown.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-pane-event/v1"
DEFAULT_LOG = "agents/runtime/pane_events/pane-events.jsonl"
CENSUS_EVENTS = ("instance_spawned", "instance_heartbeat", "instance_terminated")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _parse_ts(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def event_log_path(root: Path) -> Path:
    return root / DEFAULT_LOG


def load_events(root: Path) -> list[dict[str, Any]]:
    path = event_log_path(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{_rel(root, path)}:{line_number}: pane event must be a JSON object")
        events.append(payload)
    return events


def _next_seq(events: list[dict[str, Any]]) -> int:
    values: list[int] = []
    for event in events:
        try:
            values.append(int(event.get("seq", 0)))
        except (TypeError, ValueError):
            continue
    return (max(values) if values else 0) + 1


def append_event(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    records = load_events(root)
    payload = {
        "schema": SCHEMA,
        "seq": _next_seq(records),
        "ts": event.get("ts") or _now_iso(),
        "event": event["event"],
        "actor": event.get("actor") or "unknown",
        "task_id": event.get("task_id") or "",
        "task_set_id": event.get("task_set_id") or "",
        "claim_id": event.get("claim_id") or "",
        "worktree_path": event.get("worktree_path") or "",
    }
    for key in (
        "actor_role",
        "agent_instance_id",
        "display_name",
        "callsite_id",
        "ssot_path",
        "message",
        "orchestrator_approved",
        "verified_by",
        "verifier_role",
    ):
        if key in event and event[key] not in (None, ""):
            payload[key] = event[key]
    path = event_log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def append_census_event(
    root: Path,
    event: str,
    *,
    agent_instance_id: str,
    actor_role: str = "",
    display_name: str = "",
    callsite_id: str = "",
    task_id: str = "",
    task_set_id: str = "",
    claim_id: str = "",
    worktree_path: str = "",
    message: str = "",
    ts: str | None = None,
) -> dict[str, Any]:
    """Append an instance lifecycle census event.

    Census events (``instance_spawned``/``instance_heartbeat``/
    ``instance_terminated``) always carry ``agent_instance_id`` so
    point-in-time census queries can replay the log per instance.
    """
    if event not in CENSUS_EVENTS:
        raise ValueError(f"census event must be one of {', '.join(CENSUS_EVENTS)}")
    instance_id = str(agent_instance_id or "").strip()
    if not instance_id:
        raise ValueError("agent_instance_id is required for census events")
    return append_event(
        root,
        {
            "event": event,
            "actor": instance_id,
            "agent_instance_id": instance_id,
            "actor_role": actor_role,
            "display_name": display_name,
            "callsite_id": callsite_id,
            "task_id": task_id,
            "task_set_id": task_set_id,
            "claim_id": claim_id,
            "worktree_path": worktree_path,
            "message": message,
            "ts": ts,
        },
    )


def census(events: list[dict[str, Any]], *, at: str | None = None) -> dict[str, Any]:
    """Build a point-in-time instance census from lifecycle events.

    Events newer than ``at`` are ignored. Events whose timestamp cannot be
    parsed are included conservatively so instances never silently disappear
    from the census because of a malformed timestamp.
    """
    cutoff = _parse_ts(at)
    instances: dict[str, dict[str, Any]] = {}
    for event in sorted(events, key=lambda item: int(item.get("seq") or 0)):
        name = str(event.get("event") or "")
        if name not in CENSUS_EVENTS:
            continue
        instance_id = str(event.get("agent_instance_id") or event.get("actor") or "").strip()
        if not instance_id:
            continue
        ts = str(event.get("ts") or "")
        if cutoff is not None:
            parsed = _parse_ts(ts)
            if parsed is not None and parsed > cutoff:
                continue
        row = instances.setdefault(
            instance_id,
            {
                "agent_instance_id": instance_id,
                "active": False,
                "spawned_at": "",
                "terminated_at": "",
                "last_seen": "",
                "actor_role": "",
                "display_name": "",
                "task_id": "",
                "task_set_id": "",
            },
        )
        for field in ("actor_role", "display_name", "task_id", "task_set_id"):
            value = str(event.get(field) or "").strip()
            if value:
                row[field] = value
        row["last_seen"] = ts or row["last_seen"]
        if name == "instance_spawned":
            row["active"] = True
            row["spawned_at"] = ts
            row["terminated_at"] = ""
        elif name == "instance_heartbeat":
            if not row["terminated_at"]:
                row["active"] = True
        elif name == "instance_terminated":
            row["active"] = False
            row["terminated_at"] = ts

    rows = [instances[key] for key in sorted(instances)]
    active = [row for row in rows if row["active"]]
    return {
        "at": at or "",
        "summary": {
            "instance_count": len(rows),
            "active_count": len(active),
            "terminated_count": len(rows) - len(active),
        },
        "instances": rows,
    }


def summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    task_sets: dict[str, dict[str, Any]] = {}
    active_claims: dict[str, str] = {}
    ssot_write_attempts = 0
    for event in events:
        task_set_id = str(event.get("task_set_id") or "").strip() or "unassigned"
        group = task_sets.setdefault(
            task_set_id,
            {
                "task_set_id": task_set_id,
                "event_count": 0,
                "active_claim_ids": set(),
                "last_event": None,
                "last_ts": None,
            },
        )
        group["event_count"] += 1
        group["last_event"] = event.get("event")
        group["last_ts"] = event.get("ts")
        claim_id = str(event.get("claim_id") or "").strip()
        if claim_id:
            if event.get("event") == "claim_released":
                active_claims.pop(claim_id, None)
            else:
                active_claims[claim_id] = task_set_id
        if event.get("event") == "ssot_write_attempted":
            ssot_write_attempts += 1

    for claim_id, task_set_id in active_claims.items():
        task_sets.setdefault(
            task_set_id,
            {"task_set_id": task_set_id, "event_count": 0, "active_claim_ids": set(), "last_event": None, "last_ts": None},
        )["active_claim_ids"].add(claim_id)

    task_set_rows: list[dict[str, Any]] = []
    for task_set_id in sorted(task_sets):
        row = dict(task_sets[task_set_id])
        row["active_claim_ids"] = sorted(row["active_claim_ids"])
        task_set_rows.append(row)

    return {
        "summary": {
            "event_count": len(events),
            "task_set_count": len(task_set_rows),
            "ssot_write_attempts": ssot_write_attempts,
        },
        "task_sets": task_set_rows,
    }


def cmd_record(args: argparse.Namespace) -> int:
    event = append_event(
        args.root,
        {
            "event": args.event,
            "actor": args.actor,
            "task_id": args.task_id,
            "task_set_id": args.task_set_id,
            "claim_id": args.claim_id,
            "worktree_path": args.worktree_path,
            "ssot_path": args.ssot_path,
            "message": args.message,
            "ts": args.now,
            "orchestrator_approved": args.orchestrator_approved,
        },
    )
    payload = {"status": "recorded", "path": _rel(args.root.resolve(), event_log_path(args.root.resolve())), "event": event}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"pane-event-log: recorded seq={event['seq']}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    payload = summarize_events(load_events(args.root.resolve()))
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"pane-event-log: events={payload['summary']['event_count']}")
    return 0


def cmd_census_record(args: argparse.Namespace) -> int:
    event = append_census_event(
        args.root,
        args.event,
        agent_instance_id=args.agent_instance_id,
        actor_role=args.actor_role,
        display_name=args.display_name,
        callsite_id=args.callsite_id,
        task_id=args.task_id,
        task_set_id=args.task_set_id,
        claim_id=args.claim_id,
        worktree_path=args.worktree_path,
        message=args.message,
        ts=args.now,
    )
    payload = {"status": "recorded", "path": _rel(args.root.resolve(), event_log_path(args.root.resolve())), "event": event}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"pane-event-log: recorded seq={event['seq']}")
    return 0


def cmd_census(args: argparse.Namespace) -> int:
    payload = census(load_events(args.root.resolve()), at=args.at)
    summary = payload["summary"]
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else f"pane-event-log: instances={summary['instance_count']} active={summary['active_count']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append/read pane collaboration events")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--event", required=True)
    record.add_argument("--actor", required=True)
    record.add_argument("--task-id", default="")
    record.add_argument("--task-set-id", default="")
    record.add_argument("--claim-id", default="")
    record.add_argument("--worktree-path", default="")
    record.add_argument("--ssot-path", default="")
    record.add_argument("--message", default="")
    record.add_argument("--now")
    record.add_argument("--orchestrator-approved", action="store_true")
    record.add_argument("--json", action="store_true")
    record.set_defaults(func=cmd_record)

    summary = sub.add_parser("summary")
    summary.add_argument("--json", action="store_true")
    summary.set_defaults(func=cmd_summary)

    census_record = sub.add_parser("census-record", help="Append an instance lifecycle census event")
    census_record.add_argument("--event", required=True, choices=CENSUS_EVENTS)
    census_record.add_argument("--agent-instance-id", required=True)
    census_record.add_argument("--actor-role", default="")
    census_record.add_argument("--display-name", default="")
    census_record.add_argument("--callsite-id", default="")
    census_record.add_argument("--task-id", default="")
    census_record.add_argument("--task-set-id", default="")
    census_record.add_argument("--claim-id", default="")
    census_record.add_argument("--worktree-path", default="")
    census_record.add_argument("--message", default="")
    census_record.add_argument("--now")
    census_record.add_argument("--json", action="store_true")
    census_record.set_defaults(func=cmd_census_record)

    census_query = sub.add_parser("census", help="Point-in-time instance census from lifecycle events")
    census_query.add_argument("--at", default=None, help="ISO timestamp; ignore lifecycle events newer than this")
    census_query.add_argument("--json", action="store_true")
    census_query.set_defaults(func=cmd_census)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
