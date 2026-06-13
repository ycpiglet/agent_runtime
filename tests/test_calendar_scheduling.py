"""Focused tests for the Calendar / scheduling feature (TASK-AR-335).

Coverage:
- calendar resource aggregates milestones + meetings + completions + deadlines
  + scheduled items,
- month/week view renders (sidebar link, view container, JS render fns),
- schedule.create is proposal-only (declarative record, NO direct dispatch),
- cron-like repeat parsing,
- reminder emission for due-soon / overdue,
- tokenization-safe (calendar CSS uses var(--token) only),
- the local scheduler script is no-op-safe + emits dispatch/reminder events.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from agent_runtime import ui_commands
from agent_runtime import ui_console
from agent_runtime import ui_state


NOW = "2026-06-13T09:00:00+09:00"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEDULER = REPO_ROOT / "scripts" / "scheduled_dispatch_gate.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_project(root: Path) -> None:
    """A small project with one of each calendar source."""
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-X-1.md",
        "---\nid: TASK-X-1\nstatus: in_progress\ndue: 2026-06-14\n---\n## Goal\nopen with a due date\n",
    )
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-X-2.md",
        "---\nid: TASK-X-2\nstatus: done\ncompleted_at: 2026-06-10\n---\n## Goal\ncompleted task\n",
    )
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-X-3.md",
        "---\nid: TASK-X-3\nstatus: in_progress\ndue: 2026-06-01\n---\n## Goal\noverdue task\n",
    )
    _write(
        root / "agents" / "project" / "ROADMAP.md",
        "- phase: build\n- next_milestone: ship v1\n- [ ] 2026-06-15: ship v1\n",
    )
    _write(
        root / "reviews" / "MEETING-2026-06-12-sync.md",
        "---\nid: MEETING-1\ntype: meeting\ndate: 2026-06-12\n---\n# Sync\nBottom Line: done.\n",
    )


def _apply_schedule_proposals(root: Path) -> None:
    """Simulate the runtime executor applying schedule proposals to SSoT files."""
    sched_dir = root / "agents" / "project" / "schedules"
    sched_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted((root / ".ui_outbox" / "schedules").glob("SCHEDREQ-*.json")):
        proposal = json.loads(path.read_text(encoding="utf-8"))
        if proposal.get("action") == "create" and proposal.get("schedule"):
            schedule = proposal["schedule"]
            (sched_dir / f"{schedule['id']}.json").write_text(
                json.dumps(schedule, ensure_ascii=False), encoding="utf-8"
            )


# ---- cron-like repeat parsing -------------------------------------------------


def test_parse_cron_accepts_valid_expressions():
    assert ui_commands.parse_cron("0 9 * * 1")["valid"] is True
    parsed = ui_commands.parse_cron("*/15 9 * * *")
    assert parsed["valid"] is True
    assert parsed["fields"]["minute"] == [0, 15, 30, 45]
    assert parsed["fields"]["hour"] == [9]
    assert parsed["fields"]["day_of_week"] == "*"
    # comma list
    assert ui_commands.parse_cron("0 9,17 * * *")["fields"]["hour"] == [9, 17]


def test_parse_cron_rejects_invalid_expressions():
    assert ui_commands.parse_cron("9 9 9")["valid"] is False  # too few fields
    assert ui_commands.parse_cron("99 9 * * *")["valid"] is False  # minute out of range
    assert ui_commands.parse_cron("0 9 * * 9")["valid"] is False  # dow out of range
    assert ui_commands.parse_cron("")["valid"] is False
    assert ui_commands.parse_cron("a 9 * * *")["valid"] is False


# ---- schedule.create / cancel are proposal-only -------------------------------


def test_schedule_create_is_proposal_only_no_direct_dispatch(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "schedule.create", "payload": {"taskset_id": "TASKSET-AR-DEMO", "mode": "repeat", "cron": "0 9 * * 1", "name": "Weekly"}},
        now=NOW,
    )
    assert result["status"] == "queued"
    payload = result["result"]
    assert payload["mutation_boundary"] == "proposal_only"
    assert payload["execution_boundary"] == "local_scheduler"

    # The proposal is a declarative record under .ui_outbox/schedules ...
    proposals = list((tmp_path / ".ui_outbox" / "schedules").glob("SCHEDREQ-*.json"))
    assert len(proposals) == 1
    proposal = json.loads(proposals[0].read_text(encoding="utf-8"))
    assert proposal["mutation_boundary"] == "proposal_only"
    assert proposal["executor"] == "scripts/scheduled_dispatch_gate.py"
    assert proposal["schedule"]["cron"] == "0 9 * * 1"
    assert proposal["schedule"]["cron_fields"]["day_of_week"] == [1]

    # ... and the console NEVER writes the canonical schedule file or any SSoT.
    assert not (tmp_path / "agents" / "project" / "schedules").exists()


def test_schedule_reserve_requires_run_at_and_validates(tmp_path):
    bad = ui_commands.submit_command(
        tmp_path, {"type": "schedule.create", "payload": {"taskset_id": "TS", "mode": "reserve"}}, now=NOW
    )
    assert bad["status"] == "failed"
    assert any("run_at" in err for err in bad["errors"])

    good = ui_commands.submit_command(
        tmp_path,
        {"type": "schedule.create", "payload": {"taskset_id": "TS", "mode": "reserve", "run_at": "2026-06-20T18:00:00+09:00"}},
        now=NOW,
    )
    assert good["status"] == "queued"


def test_schedule_create_rejects_bad_mode_and_cron(tmp_path):
    bad_mode = ui_commands.submit_command(
        tmp_path, {"type": "schedule.create", "payload": {"taskset_id": "TS", "mode": "loop"}}, now=NOW
    )
    assert bad_mode["status"] == "failed"
    bad_cron = ui_commands.submit_command(
        tmp_path, {"type": "schedule.create", "payload": {"taskset_id": "TS", "mode": "repeat", "cron": "99 9 * * *"}}, now=NOW
    )
    assert bad_cron["status"] == "failed"


def test_schedule_cancel_is_proposal_only(tmp_path):
    result = ui_commands.submit_command(
        tmp_path, {"type": "schedule.cancel", "target": "SCHED-demo", "payload": {"actor": "ui"}}, now=NOW
    )
    assert result["status"] == "queued"
    assert result["result"]["action"] == "cancel"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    proposal = json.loads(next((tmp_path / ".ui_outbox" / "schedules").glob("SCHEDREQ-*.json")).read_text(encoding="utf-8"))
    assert proposal["schedule"] is None


# ---- calendar resource aggregates all sources ---------------------------------


def test_calendar_aggregates_all_sources(tmp_path):
    _seed_project(tmp_path)
    ui_commands.submit_command(
        tmp_path,
        {"type": "schedule.create", "payload": {"taskset_id": "TASKSET-AR-DEMO", "mode": "reserve", "run_at": "2026-06-16T18:00:00+09:00", "name": "One-shot"}},
        now=NOW,
    )
    _apply_schedule_proposals(tmp_path)

    state = ui_state.build_state(tmp_path, now=NOW)
    calendar = state["calendar"]
    by_kind = calendar["totals"]["by_kind"]
    assert by_kind.get("milestone") == 1
    assert by_kind.get("meeting") == 1
    assert by_kind.get("completion") == 1
    assert by_kind.get("deadline") == 2  # TASK-X-1 (due soon) + TASK-X-3 (overdue)
    assert by_kind.get("scheduled") == 1

    # Events are indexed by day for the month/week grid.
    assert "2026-06-15" in calendar["by_date"]  # milestone
    assert "2026-06-12" in calendar["by_date"]  # meeting
    assert "2026-06-10" in calendar["by_date"]  # completion
    assert "2026-06-16" in calendar["by_date"]  # reserved dispatch


def test_calendar_resource_via_build_resource(tmp_path):
    _seed_project(tmp_path)
    resource = ui_state.build_resource(tmp_path, "calendar", now=NOW)
    assert resource["resource"] == "calendar"
    assert resource["items"]["schema"] == ui_state.CALENDAR_SCHEMA
    schedules = ui_state.build_resource(tmp_path, "schedules", now=NOW)
    assert schedules["items"]["schema"] == ui_state.SCHEDULES_SCHEMA


# ---- reminder emission for due-soon / overdue ---------------------------------


def test_calendar_emits_due_soon_and_overdue_reminders(tmp_path):
    _seed_project(tmp_path)
    state = ui_state.build_state(tmp_path, now=NOW)
    reminders = state["calendar"]["reminders"]
    severities = {item["severity"] for item in reminders}
    assert "overdue" in severities  # TASK-X-3 due 2026-06-01
    assert "due_soon" in severities  # TASK-X-1 due 2026-06-14, milestone 2026-06-15

    # Each reminder is event-shaped and names its (pending) consumer (TASK-AR-338).
    for item in reminders:
        assert item["event"] == "calendar_reminder"
        assert "338" in item["consumer"]
        assert item["severity"] in {"due_soon", "overdue"}

    totals = state["calendar"]["totals"]
    assert totals["overdue"] >= 1
    assert totals["due_soon"] >= 1


def test_reminder_status_boundaries():
    assert ui_state._reminder_status("2026-06-01", NOW) == "overdue"
    assert ui_state._reminder_status("2026-06-13", NOW) == "due_soon"  # today
    assert ui_state._reminder_status("2026-06-16", NOW) == "due_soon"  # within horizon
    assert ui_state._reminder_status("2026-07-01", NOW) == "upcoming"
    assert ui_state._reminder_status(None, NOW) is None


# ---- month/week view renders (markup + JS) ------------------------------------


def test_calendar_view_and_sidebar_registered(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    assert 'data-view="calendar"' in html
    assert 'data-route="work/calendar"' in html
    assert 'id="view-calendar"' in html
    assert 'id="calendar-grid"' in html
    assert 'id="schedule-form"' in html


def test_calendar_js_render_functions_present(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function renderCalendar" in js
    assert "function renderSchedules" in js
    assert "renderCalendar();" in js
    assert "renderSchedules();" in js
    # month/week mode toggle + nav.
    assert 'calendarMode = "week"' in js
    assert 'calendarMode = "month"' in js
    assert "function calendarVisibleDays" in js
    # schedule.create + schedule.cancel are issued via /api/commands.
    assert '"schedule.create"' in js
    assert '"schedule.cancel"' in js


def test_calendar_api_routes(tmp_path):
    cal = ui_console.build_response("/api/calendar", tmp_path)
    assert cal.status == 200
    assert json.loads(cal.body.decode("utf-8"))["resource"] == "calendar"
    sched = ui_console.build_response("/api/schedules", tmp_path)
    assert json.loads(sched.body.decode("utf-8"))["resource"] == "schedules"


# ---- tokenization-safe --------------------------------------------------------


def test_calendar_css_uses_tokens_not_raw_hex(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    # Pull only the calendar CSS lines and assert no raw hex/rgba literals.
    calendar_lines = [line for line in css.splitlines() if ".calendar" in line or "calendar-" in line]
    assert calendar_lines, "expected calendar CSS rules"
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in calendar_lines:
        assert not hex_pattern.search(line), f"raw hex in calendar CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in calendar CSS: {line.strip()}"
    # Spot-check token usage.
    assert ".calendar-event-scheduled { border-color: var(--teal-line); background: var(--teal-soft); }" in css


# ---- local scheduler script ---------------------------------------------------


def _run_scheduler(root: Path, now: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCHEDULER), "--root", str(root), "--now", now, "--json"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_scheduler_is_noop_safe_with_no_schedules(tmp_path):
    out = _run_scheduler(tmp_path, NOW)
    assert out["status"] == "pass"
    assert out["schedules_total"] == 0
    assert out["due"] == 0


def test_scheduler_emits_dispatch_for_due_reserve(tmp_path):
    _write(
        tmp_path / "agents" / "project" / "schedules" / "SCHED-1.json",
        json.dumps({"id": "SCHED-1", "taskset_id": "TS", "mode": "reserve", "run_at": "2026-06-13T08:00:00+09:00", "active": True}),
    )
    out = _run_scheduler(tmp_path, "2026-06-13T09:00:00+09:00")
    assert out["due"] == 1
    assert out["dispatches"][0]["event"] == "scheduled_dispatch_due"
    assert out["dispatches"][0]["boundary"] == "request_only"


def test_scheduler_matches_repeat_cron(tmp_path):
    # 2026-06-15 is a Monday; cron "0 9 * * 1" should fire at 09:00.
    _write(
        tmp_path / "agents" / "project" / "schedules" / "SCHED-2.json",
        json.dumps({"id": "SCHED-2", "taskset_id": "TS", "mode": "repeat", "cron": "0 9 * * 1", "active": True}),
    )
    fired = _run_scheduler(tmp_path, "2026-06-15T09:00:00+09:00")
    assert fired["due"] == 1
    not_fired = _run_scheduler(tmp_path, "2026-06-15T10:00:00+09:00")
    assert not_fired["due"] == 0


def test_scheduler_apply_writes_event_log(tmp_path):
    _write(
        tmp_path / "agents" / "project" / "schedules" / "SCHED-3.json",
        json.dumps({"id": "SCHED-3", "taskset_id": "TS", "mode": "reserve", "run_at": "2026-06-13T08:00:00+09:00", "active": True}),
    )
    proc = subprocess.run(
        [sys.executable, str(SCHEDULER), "--root", str(tmp_path), "--now", "2026-06-13T09:00:00+09:00", "--apply"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    log = tmp_path / "agents" / "runtime" / "events" / "scheduled_dispatch.jsonl"
    assert log.exists()
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(rec["event"] == "scheduled_dispatch_due" for rec in records)
