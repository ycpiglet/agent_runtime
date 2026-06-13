"""Execute declarative UI automation rules in the governance gate chain (TASK-AR-331).

Rules are authored in the UI (proposal-only) and persisted as declarative JSON
files under ``agents/project/automation/rules/*.json``. This gate is the single
EXECUTION point for those rules: the UI only does CRUD + the active/inactive
toggle. Each rule has the shape::

    {"id": "...", "name": "...", "trigger": "status_change|due_passed|blocked_too_long",
     "action": "board_regen|escalation_message|label_apply", "params": {...},
     "active": true}

Execution is intentionally OFF-BY-DEFAULT and no-op-safe:

- when no rules directory / no rule files exist, the gate passes with 0 rules
  executed (so the owner-governance approve path keeps working),
- inactive rules are skipped,
- invalid rules are reported as findings but never crash the gate,
- ``--check`` only fails when an ACTIVE, VALID rule could not be matched to a
  known trigger/action (a genuine wiring error), never merely because rules
  exist.

Actions are recorded as append-only runtime events
(``agents/runtime/events/automation_rules.jsonl``); the gate never mutates the
canonical SSoT directly. ``board_regen`` is the one action that delegates to an
existing executable (``scripts/backlog_board.py --write``) when triggered.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


RULES_GLOB = "agents/project/automation/rules/*.json"
TASKS_GLOB = "agents/lead_engineer/tasks/TASK-*.md"
EVENT_LOG = "agents/runtime/events/automation_rules.jsonl"

VALID_TRIGGERS = ("status_change", "due_passed", "blocked_too_long")
VALID_ACTIONS = ("board_regen", "escalation_message", "label_apply")
DONE_STATUSES = {"completed", "done", "released", "완료"}
BLOCKED_STATUSES = {"blocked", "hold", "보류"}
DEFAULT_BLOCKED_DAYS = 3


@dataclass
class Finding:
    severity: str  # "block" | "watch" | "info"
    rule_id: str
    detail: str


@dataclass
class Outcome:
    rules_total: int = 0
    rules_active: int = 0
    rules_executed: int = 0
    rules_invalid: int = 0
    actions: list[dict] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            out[match.group(1)] = match.group(2).strip().strip("'\"")
    return out


def _parse_date(value: str) -> datetime | None:
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


def _days_since(value: str, now: datetime) -> float | None:
    start = _parse_date(value)
    if start is None:
        return None
    return max(0.0, (now - start).total_seconds() / 86400.0)


def load_rules(root: Path) -> tuple[list[dict], list[Finding]]:
    rules: list[dict] = []
    findings: list[Finding] = []
    for path in sorted(root.glob(RULES_GLOB)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(Finding("watch", path.stem, f"unreadable rule file: {exc}"))
            continue
        if not isinstance(payload, dict):
            findings.append(Finding("watch", path.stem, "rule file is not a JSON object"))
            continue
        payload.setdefault("id", path.stem)
        rules.append(payload)
    return rules, findings


def load_tasks(root: Path) -> list[dict[str, str]]:
    tasks: list[dict[str, str]] = []
    for path in sorted(root.glob(TASKS_GLOB)):
        try:
            meta = _frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if meta:
            meta["__path"] = path.as_posix()
            tasks.append(meta)
    return tasks


def _matched_tasks(trigger: str, params: dict, tasks: list[dict[str, str]], now: datetime) -> list[str]:
    matched: list[str] = []
    for task in tasks:
        status = str(task.get("status") or "").strip().lower()
        if status in DONE_STATUSES:
            continue
        task_id = str(task.get("id") or Path(task.get("__path", "")).stem)
        if trigger == "status_change":
            want = str(params.get("status") or "").strip().lower()
            if not want or status == want:
                matched.append(task_id)
        elif trigger == "due_passed":
            days = _days_since(str(task.get("due") or ""), now)
            if days is not None and days > 0:
                matched.append(task_id)
        elif trigger == "blocked_too_long":
            if status in BLOCKED_STATUSES:
                threshold = float(params.get("days", DEFAULT_BLOCKED_DAYS))
                since = str(task.get("blocked_since") or task.get("updated_at") or task.get("created") or "")
                days = _days_since(since, now)
                if days is not None and days >= threshold:
                    matched.append(task_id)
    return matched


def execute(root: Path, *, apply_actions: bool = False) -> Outcome:
    now_dt = datetime.now(timezone.utc)
    outcome = Outcome()
    rules, findings = load_rules(root)
    outcome.findings.extend(findings)
    outcome.rules_total = len(rules)
    if not rules:
        # Off-by-default: nothing authored, nothing to do.
        return outcome

    tasks = load_tasks(root)
    events: list[dict] = []
    for rule in rules:
        rule_id = str(rule.get("id") or "rule")
        trigger = str(rule.get("trigger") or "").strip()
        action = str(rule.get("action") or "").strip()
        if trigger not in VALID_TRIGGERS or action not in VALID_ACTIONS:
            outcome.rules_invalid += 1
            outcome.findings.append(
                Finding("watch", rule_id, f"invalid rule (trigger={trigger!r} action={action!r}); skipped")
            )
            continue
        if not bool(rule.get("active", False)):
            outcome.findings.append(Finding("info", rule_id, "inactive; skipped"))
            continue

        outcome.rules_active += 1
        params = rule.get("params") if isinstance(rule.get("params"), dict) else {}
        matched = _matched_tasks(trigger, params, tasks, now_dt)
        action_record = {
            "ts": _now_iso(),
            "event": "automation_rule_executed",
            "rule_id": rule_id,
            "trigger": trigger,
            "action": action,
            "matched_task_ids": matched,
            "matched": len(matched),
            "applied": False,
        }

        if matched and action == "board_regen" and apply_actions:
            script = root / "scripts" / "backlog_board.py"
            if script.exists():
                rc = subprocess.call([sys.executable, str(script), "--write"], cwd=root)
                action_record["applied"] = rc == 0
                if rc != 0:
                    outcome.findings.append(Finding("watch", rule_id, "board_regen action: backlog_board.py --write failed"))
        # escalation_message / label_apply are recorded as proposals-via-events;
        # the runtime executor consumes the event to write the message/label.
        outcome.rules_executed += 1
        outcome.actions.append(action_record)
        events.append(action_record)

    if events and apply_actions:
        log_path = root / EVENT_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    return outcome


def render(root: Path, outcome: Outcome) -> str:
    blocks = sum(1 for finding in outcome.findings if finding.severity == "block")
    status = "fail" if blocks else "pass"
    lines = [
        f"automation-rules-gate: {status}",
        f"root={root.resolve()}",
        f"rules_total={outcome.rules_total}",
        f"rules_active={outcome.rules_active}",
        f"rules_executed={outcome.rules_executed}",
        f"rules_invalid={outcome.rules_invalid}",
        f"actions={len(outcome.actions)}",
        f"findings={len(outcome.findings)}",
    ]
    for finding in outcome.findings:
        lines.append(f"- {finding.severity} {finding.rule_id}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute declarative UI automation rules")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail (exit 1) on block findings")
    parser.add_argument("--apply", action="store_true", help="Apply side effects (board regen, event log)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    outcome = execute(root, apply_actions=args.apply)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if any(f.severity == "block" for f in outcome.findings) else "pass",
                    "rules_total": outcome.rules_total,
                    "rules_active": outcome.rules_active,
                    "rules_executed": outcome.rules_executed,
                    "rules_invalid": outcome.rules_invalid,
                    "actions": outcome.actions,
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
