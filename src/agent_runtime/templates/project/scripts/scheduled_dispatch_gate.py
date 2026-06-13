"""LOCAL scheduler for reserved / repeating taskset dispatches (TASK-AR-335).

Schedules are authored in the Calendar view (PROPOSAL-ONLY) and persisted as
declarative JSON files under ``agents/project/schedules/*.json``. This script is
the single LOCAL execution point that:

- decides which schedules are DUE relative to ``--now`` (``reserve`` = a fixed
  ``run_at`` timestamp that has passed; ``repeat`` = a 5-field cron-like cadence
  whose minute/hour/day/month/dow all match), and
- emits append-only dispatch + due-soon/overdue reminder events that downstream
  consumers (taskset_dispatcher, TASK-AR-338 notification center) read.

It is intentionally OFF-BY-DEFAULT and no-op-safe:

- no schedules dir / no files -> passes with 0 due, 0 emitted,
- inactive / invalid schedules are skipped (invalid ones reported as findings),
- ``--check`` only fails (exit 1) on a genuine wiring error (an ACTIVE, VALID
  schedule that cannot be interpreted), never merely because schedules exist.

Crucially this script NEVER runs ``taskset_dispatcher`` itself and NEVER mutates
the SSoT. It emits a ``scheduled_dispatch_due`` event (a dispatch REQUEST) plus
``calendar_reminder`` events; an external executor consumes those. There is no
network access and no external service -- everything is local files.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


SCHEDULES_GLOB = "agents/project/schedules/*.json"
DISPATCH_EVENT_LOG = "agents/runtime/events/scheduled_dispatch.jsonl"

VALID_MODES = ("reserve", "repeat")
DUE_SOON_DAYS = 3

# Cron field bounds: minute hour day-of-month month day-of-week (0 = Sunday).
_CRON_BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))
_CRON_NAMES = ("minute", "hour", "day_of_month", "month", "day_of_week")


@dataclass
class Finding:
    severity: str  # "block" | "watch" | "info"
    schedule_id: str
    detail: str


@dataclass
class Outcome:
    schedules_total: int = 0
    schedules_active: int = 0
    schedules_invalid: int = 0
    due: int = 0
    dispatches: list[dict] = field(default_factory=list)
    reminders: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _parse_dt(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for candidate in (value, value[:19], value[:10]):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_cron_field(token: str, low: int, high: int) -> list[int] | str | None:
    """Parse one cron field into a set of allowed ints, ``"*"``, or None on error."""
    token = token.strip()
    if not token:
        return None
    if token == "*":
        return "*"
    if token.startswith("*/"):
        step_raw = token[2:]
        if not step_raw.isdigit() or int(step_raw) <= 0:
            return None
        step = int(step_raw)
        return [value for value in range(low, high + 1) if (value - low) % step == 0]
    values: list[int] = []
    for part in token.split(","):
        part = part.strip()
        if not re.fullmatch(r"-?\d+", part or ""):
            return None
        value = int(part)
        if value < low or value > high:
            return None
        values.append(value)
    return sorted(set(values))


def parse_cron(expression: str) -> dict | None:
    """Return ``{name: "*"|[ints]}`` for a valid 5-field cron, else None."""
    tokens = (expression or "").split()
    if len(tokens) != 5:
        return None
    fields: dict[str, list[int] | str] = {}
    for token, name, (low, high) in zip(tokens, _CRON_NAMES, _CRON_BOUNDS):
        parsed = _parse_cron_field(token, low, high)
        if parsed is None:
            return None
        fields[name] = parsed
    return fields


def cron_matches(fields: dict, moment: datetime) -> bool:
    """True when every cron field matches ``moment`` (minute granularity)."""

    def _ok(name: str, actual: int) -> bool:
        spec = fields.get(name)
        return spec == "*" or (isinstance(spec, list) and actual in spec)

    # cron day-of-week: 0 = Sunday; Python weekday(): 0 = Monday.
    dow = (moment.weekday() + 1) % 7
    return (
        _ok("minute", moment.minute)
        and _ok("hour", moment.hour)
        and _ok("day_of_month", moment.day)
        and _ok("month", moment.month)
        and _ok("day_of_week", dow)
    )


def load_schedules(root: Path) -> tuple[list[dict], list[Finding]]:
    schedules: list[dict] = []
    findings: list[Finding] = []
    for path in sorted(root.glob(SCHEDULES_GLOB)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(Finding("watch", path.stem, f"unreadable schedule file: {exc}"))
            continue
        if not isinstance(payload, dict):
            findings.append(Finding("watch", path.stem, "schedule file is not a JSON object"))
            continue
        payload.setdefault("id", path.stem)
        schedules.append(payload)
    return schedules, findings


def _reminder_for(schedule: dict, now_dt: datetime) -> dict | None:
    """Build a due-soon/overdue reminder for a reserve schedule, or None."""
    run_at = _parse_dt(str(schedule.get("run_at") or ""))
    if run_at is None:
        return None
    delta_days = (run_at.date() - now_dt.date()).days
    severity: str | None = None
    if delta_days < 0:
        severity = "overdue"
    elif delta_days <= DUE_SOON_DAYS:
        severity = "due_soon"
    if severity is None:
        return None
    return {
        "ts": _now_iso(),
        "event": "calendar_reminder",
        "severity": severity,
        "entity_kind": "schedule",
        "calendar_kind": "scheduled",
        "entity_id": str(schedule.get("id")),
        "title": str(schedule.get("name") or schedule.get("id")),
        "taskset_id": str(schedule.get("taskset_id") or ""),
        "date": run_at.date().isoformat(),
        "consumer": "TASK-AR-338 notification-center (pending)",
    }


def execute(root: Path, *, now: datetime | None = None, apply_actions: bool = False) -> Outcome:
    now_dt = now or datetime.now(timezone.utc)
    outcome = Outcome()
    schedules, findings = load_schedules(root)
    outcome.findings.extend(findings)
    outcome.schedules_total = len(schedules)
    if not schedules:
        return outcome

    events: list[dict] = []
    for schedule in schedules:
        sched_id = str(schedule.get("id") or "schedule")
        mode = str(schedule.get("mode") or "").strip().lower()
        taskset_id = str(schedule.get("taskset_id") or "").strip()

        invalid: list[str] = []
        if mode not in VALID_MODES:
            invalid.append(f"unknown mode: {mode!r}")
        if not taskset_id:
            invalid.append("missing taskset_id")
        cron_fields: dict | None = None
        if mode == "reserve" and not schedule.get("run_at"):
            invalid.append("reserve schedule missing run_at")
        if mode == "repeat":
            cron_fields = parse_cron(str(schedule.get("cron") or ""))
            if cron_fields is None:
                invalid.append("repeat schedule has an unparseable cron expression")
        if invalid:
            outcome.schedules_invalid += 1
            # An ACTIVE schedule that is invalid is a genuine wiring error.
            severity = "block" if bool(schedule.get("active", True)) else "watch"
            outcome.findings.append(Finding(severity, sched_id, "; ".join(invalid)))
            continue

        if not bool(schedule.get("active", True)):
            outcome.findings.append(Finding("info", sched_id, "inactive; skipped"))
            continue
        outcome.schedules_active += 1

        # Reminder publication (reserve schedules carry a concrete date).
        reminder = _reminder_for(schedule, now_dt) if mode == "reserve" else None
        if reminder is not None:
            outcome.reminders.append(reminder)
            events.append(reminder)

        # Due-ness.
        due = False
        fire_at: str | None = None
        if mode == "reserve":
            run_at = _parse_dt(str(schedule.get("run_at") or ""))
            if run_at is not None and run_at <= now_dt:
                due = True
                fire_at = run_at.isoformat()
        elif mode == "repeat" and cron_fields is not None:
            if cron_matches(cron_fields, now_dt):
                due = True
                fire_at = now_dt.replace(second=0, microsecond=0).isoformat()

        if not due:
            continue
        outcome.due += 1
        dispatch = {
            "ts": _now_iso(),
            "event": "scheduled_dispatch_due",
            "schedule_id": sched_id,
            "taskset_id": taskset_id,
            "mode": mode,
            "fire_at": fire_at,
            "boundary": "request_only",
            "note": "dispatch REQUEST emitted by the local scheduler; an executor runs taskset_dispatcher. The console/gate never runs it directly.",
        }
        outcome.dispatches.append(dispatch)
        events.append(dispatch)

    if events and apply_actions:
        log_path = root / DISPATCH_EVENT_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return outcome


def render(root: Path, outcome: Outcome) -> str:
    blocks = sum(1 for finding in outcome.findings if finding.severity == "block")
    status = "fail" if blocks else "pass"
    lines = [
        f"scheduled-dispatch-gate: {status}",
        f"root={root.resolve()}",
        f"schedules_total={outcome.schedules_total}",
        f"schedules_active={outcome.schedules_active}",
        f"schedules_invalid={outcome.schedules_invalid}",
        f"due={outcome.due}",
        f"dispatches={len(outcome.dispatches)}",
        f"reminders={len(outcome.reminders)}",
        f"findings={len(outcome.findings)}",
    ]
    for finding in outcome.findings:
        lines.append(f"- {finding.severity} {finding.schedule_id}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local scheduler for reserved/repeating taskset dispatches")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--now", type=str, default=None, help="ISO timestamp to evaluate against (defaults to now)")
    parser.add_argument("--check", action="store_true", help="Fail (exit 1) on block findings")
    parser.add_argument("--apply", action="store_true", help="Append dispatch + reminder events to the event log")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    now_dt = _parse_dt(args.now) if args.now else None
    outcome = execute(root, now=now_dt, apply_actions=args.apply)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if any(f.severity == "block" for f in outcome.findings) else "pass",
                    "schedules_total": outcome.schedules_total,
                    "schedules_active": outcome.schedules_active,
                    "schedules_invalid": outcome.schedules_invalid,
                    "due": outcome.due,
                    "dispatches": outcome.dispatches,
                    "reminders": outcome.reminders,
                    "findings": [vars(finding) for finding in outcome.findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render(root, outcome))
    if args.check and any(finding.severity == "block" for finding in outcome.findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
