import json
from pathlib import Path

from agent_runtime import ui_commands
from agent_runtime import ui_state


NOW = "2026-06-10T12:30:00+09:00"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task(root: Path, task_id: str, *, order: int = 10, status: str = "planned") -> Path:
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-sample.md"
    _write(
        path,
        "\n".join(
            [
                "---",
                f"id: {task_id}",
                f"status: {status}",
                "owner: lead-engineer",
                "priority: P1",
                f"order: {order}",
                "tags:",
                "  - ui-console",
                "---",
                "",
                "## Goal",
                "",
                "Original task description.",
                "",
            ]
        ),
    )
    return path


def _write_backlog_board_script(root: Path) -> None:
    _write(
        root / "scripts" / "backlog_board.py",
        "\n".join(
            [
                "from pathlib import Path",
                "ROOT = Path(__file__).resolve().parents[1]",
                "(ROOT / 'BACKLOG-BOARD.md').write_text('synced\\n', encoding='utf-8')",
                "",
            ]
        ),
    )


def test_submit_create_task_writes_task_and_accepted_command(tmp_path):
    _write_backlog_board_script(tmp_path)

    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "task.create",
            "payload": {
                "id": "TASK-UI-100",
                "title": "Console created task",
                "description": "Created from the UI write API.",
                "status": "planned",
                "priority": "P1",
                "owner": "lead-engineer",
                "order": 7,
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-create",
    )

    assert result["status"] == "accepted"
    task_path = tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-UI-100-console-created-task.md"
    assert task_path.exists()
    text = task_path.read_text(encoding="utf-8")
    assert "id: TASK-UI-100" in text
    assert "title: Console created task" in text
    assert "Created from the UI write API." in text
    command_path = tmp_path / ".ui_outbox" / "COMMAND-20260610-123000-create.json"
    assert command_path.exists()
    stored = json.loads(command_path.read_text(encoding="utf-8"))
    assert stored["status"] == "accepted"
    assert stored["result"]["changed"] == ["agents/lead_engineer/tasks/TASK-UI-100-console-created-task.md"]
    state = ui_state.build_state(tmp_path, now=NOW)
    assert [task["id"] for task in state["tasks"]] == ["TASK-UI-100"]


def test_submit_create_task_rejects_overlong_title_without_crashing(tmp_path):
    """A very long title must fail validation, not raise an OS error.

    Regression for the beta-exploration finding: ``_create_task`` built the task
    filename from ``_slug(title)`` with no length bound, so a multi-thousand-char
    title produced a path over the OS limit and ``path.write_text`` raised an
    uncaught ``OSError``/``FileNotFoundError``. That exception propagated out of
    ``submit_command`` into the HTTP handler and reset the connection (no response
    body). The command path must instead return a clean ``failed`` result.
    """
    _write_backlog_board_script(tmp_path)

    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.create", "payload": {"title": "A" * 5000}},
        now=NOW,
        command_id="COMMAND-20260610-123000-overlong",
    )

    assert result["status"] == "failed"
    assert any("title" in err.lower() for err in result.get("errors", []))
    # Nothing should have been written to the tasks dir.
    tasks_dir = tmp_path / "agents" / "lead_engineer" / "tasks"
    assert not list(tasks_dir.glob("TASK-*.md")) if tasks_dir.exists() else True


def test_submit_update_task_validates_and_preserves_source_truth(tmp_path):
    _write_backlog_board_script(tmp_path)
    _task(tmp_path, "TASK-UI-101")

    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "task.update",
            "target": "TASK-UI-101",
            "payload": {
                "status": "in_progress",
                "priority": "P0",
                "owner": "qa",
                "title": "Updated title",
                "description": "Updated task body.",
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-update",
    )

    assert result["status"] == "accepted"
    state_task = ui_state.build_state(tmp_path, now=NOW)["tasks"][0]
    assert state_task["status"] == "in_progress"
    assert state_task["priority"] == "P0"
    assert state_task["owner_agent"] == "qa"
    assert state_task["title"] == "Updated title"
    assert state_task["description"] == "Updated task body."


def test_submit_reorder_persists_stable_order_across_refresh(tmp_path):
    _write_backlog_board_script(tmp_path)
    _task(tmp_path, "TASK-UI-201", order=20)
    _task(tmp_path, "TASK-UI-202", order=30)

    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.reorder", "target": "TASK-UI-202", "payload": {"order": 5, "status": "ready"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-reorder",
    )

    assert result["status"] == "accepted"
    state_a = ui_state.build_state(tmp_path, now=NOW)
    state_b = ui_state.build_state(tmp_path, now=NOW)
    assert [task["id"] for task in state_a["tasks"]] == ["TASK-UI-202", "TASK-UI-201"]
    assert [task["id"] for task in state_b["tasks"]] == ["TASK-UI-202", "TASK-UI-201"]
    assert state_a["tasks"][0]["status"] == "ready"
    assert state_a["tasks"][0]["order"] == 5


def test_submit_comment_writes_runtime_visible_message(tmp_path):
    _task(tmp_path, "TASK-UI-301")

    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "task.comment",
            "target": "TASK-UI-301",
            "payload": {"comment": "Please review this task.", "to": "qa"},
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-comment",
    )

    assert result["status"] == "accepted"
    messages = ui_state.build_state(tmp_path, now=NOW)["messages"]
    assert len(messages) == 1
    assert messages[0]["task_id"] == "TASK-UI-301"
    assert messages[0]["to"] == "qa"
    assert "Please review this task." in messages[0]["body"]


def test_submit_archive_marks_task_completed_and_archived(tmp_path):
    _write_backlog_board_script(tmp_path)
    path = _task(tmp_path, "TASK-UI-350", status="in_progress")

    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.archive", "target": "TASK-UI-350", "payload": {}},
        now=NOW,
        command_id="COMMAND-20260610-123000-archive",
    )

    assert result["status"] == "accepted"
    text = path.read_text(encoding="utf-8")
    assert "status: completed" in text
    assert "archived: true" in text


def test_submit_invalid_update_is_rejected_and_stored(tmp_path):
    path = _task(tmp_path, "TASK-UI-401")
    before = path.read_text(encoding="utf-8")

    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.update", "target": "TASK-UI-401", "payload": {"status": "not-a-status"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-invalid",
    )

    assert result["status"] == "failed"
    assert any("invalid status" in error for error in result["errors"])
    assert path.read_text(encoding="utf-8") == before
    stored = json.loads((tmp_path / ".ui_outbox" / "COMMAND-20260610-123000-invalid.json").read_text(encoding="utf-8"))
    assert stored["status"] == "failed"
    assert stored["errors"] == result["errors"]


def test_submit_missing_task_id_and_unsafe_direct_file_mutation_are_rejected(tmp_path):
    missing = ui_commands.submit_command(
        tmp_path,
        {"type": "task.update", "payload": {"status": "ready"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-missing",
    )
    unsafe = ui_commands.submit_command(
        tmp_path,
        {
            "type": "task.update",
            "target": "TASK-UI-999",
            "payload": {"status": "ready", "source_path": "agents/lead_engineer/tasks/TASK-UI-999.md"},
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-unsafe",
    )

    assert missing["status"] == "failed"
    assert any("missing task id" in error for error in missing["errors"])
    assert unsafe["status"] == "failed"
    assert any("direct file mutation" in error for error in unsafe["errors"])


def test_list_commands_returns_accepted_and_failed_write_states(tmp_path):
    _write_backlog_board_script(tmp_path)
    _task(tmp_path, "TASK-UI-501")
    ui_commands.submit_command(
        tmp_path,
        {"type": "task.update", "target": "TASK-UI-501", "payload": {"status": "ready"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-a",
    )
    ui_commands.submit_command(
        tmp_path,
        {"type": "task.update", "target": "TASK-UI-501", "payload": {"status": "bad"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-b",
    )

    states = ui_commands.list_commands(tmp_path)

    assert [state["id"] for state in states] == ["COMMAND-20260610-123000-a", "COMMAND-20260610-123000-b"]
    assert [state["status"] for state in states] == ["accepted", "failed"]


def test_submit_call_agent_writes_runtime_visible_message_with_safety_metadata(tmp_path):
    _task(tmp_path, "TASK-UI-601")

    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "runtime.call_agent",
            "target": "qa",
            "payload": {
                "actor": "owner",
                "instruction": "Review TASK-UI-601 and report blockers.",
                "reason": "Need a second-pass review before continuing.",
                "task_id": "TASK-UI-601",
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-call-agent",
    )

    assert result["status"] == "queued"
    assert result["actor"] == "owner"
    assert result["reason"] == "Need a second-pass review before continuing."
    assert result["task_id"] == "TASK-UI-601"
    assert result["approval_required"] is False
    assert result["risk_level"] == "low"
    messages = ui_state.build_state(tmp_path, now=NOW)["messages"]
    assert len(messages) == 1
    assert messages[0]["to"] == "qa"
    assert messages[0]["type"] == "runtime-command"
    assert messages[0]["intent"] == "runtime.call_agent"
    assert messages[0]["task_id"] == "TASK-UI-601"
    assert "Review TASK-UI-601" in messages[0]["body"]


def test_high_risk_runtime_command_requires_approval_before_execution(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "runtime.call_agent",
            "target": "lead-engineer",
            "payload": {
                "actor": "owner",
                "instruction": "Commit, push, and open a PR after installing dependencies.",
                "reason": "Publish changes.",
                "task_id": "TASK-UI-602",
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-approval",
    )

    assert result["status"] == "approval_required"
    assert result["approval_required"] is True
    assert result["risk_level"] == "high"
    assert "commit" in " ".join(result["approval_reasons"])
    assert ui_state.build_state(tmp_path, now=NOW)["messages"] == []


def test_goal_lifecycle_command_records_explicit_unsupported_runtime_state(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "runtime.goal.pause",
            "target": "goal-123",
            "payload": {
                "actor": "owner",
                "goal_id": "goal-123",
                "reason": "Pause until the owner reviews the next boundary.",
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-pause-goal",
    )

    assert result["status"] == "pending_runtime_support"
    assert result["approval_required"] is False
    assert result["goal_id"] == "goal-123"
    assert result["result"]["runtime_support"] == "unsupported"
    assert result["result"]["next"] == "runtime executor must consume this command before UI can claim execution"


# ----- TASK-AR-327: meeting.start / seminar.start (proposal-only) -----


def test_meeting_and_seminar_commands_in_allowlist():
    assert "meeting.start" in ui_commands.COMMAND_TYPES
    assert "seminar.start" in ui_commands.COMMAND_TYPES


def test_meeting_start_writes_proposal_not_direct_reviews_file(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "meeting.start",
            "payload": {
                "actor": "owner",
                "topic": "Release readiness sync",
                "participants": ["lead-engineer", "qa"],
                "rounds": 3,
                "channel": "general",
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-meeting",
    )

    assert result["status"] == "queued"
    assert result["result"]["meeting_type"] == "meeting"
    assert result["result"]["records_to"] == "reviews/MEETING-2026-06-10-release-readiness-sync.md"
    assert result["result"]["mutation_boundary"] == "proposal_only"

    # The handler writes a proposal under .ui_outbox, NOT a reviews/ file.
    proposals = list((tmp_path / ".ui_outbox" / "meetings").glob("MEETREQ-*.json"))
    assert len(proposals) == 1
    proposal = json.loads(proposals[0].read_text(encoding="utf-8"))
    assert proposal["meeting_type"] == "meeting"
    assert proposal["participants"] == ["lead-engineer", "qa"]
    assert proposal["consensus_round"] is True
    assert not (tmp_path / "reviews").exists()

    # A runtime event is recorded so the summon is traceable.
    event_text = (tmp_path / "agents" / "runtime" / "events" / "ui_meeting_requests.jsonl").read_text(encoding="utf-8")
    event = json.loads(event_text.strip())
    assert event["event"] == "meeting.start"
    assert event["topic"] == "Release readiness sync"
    assert event["records_to"] == "reviews/MEETING-2026-06-10-release-readiness-sync.md"


def test_seminar_start_records_seminar_path_and_single_participant_ok(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "seminar.start",
            "payload": {
                "actor": "owner",
                "topic": "Async runtime patterns",
                "rounds": 2,
            },
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-seminar",
    )

    assert result["status"] == "queued"
    assert result["result"]["meeting_type"] == "seminar"
    assert result["result"]["records_to"] == "reviews/SEMINAR-2026-06-10-async-runtime-patterns.md"


def test_meeting_start_rejects_missing_topic_and_too_few_participants(tmp_path):
    missing_topic = ui_commands.submit_command(
        tmp_path,
        {"type": "meeting.start", "payload": {"participants": ["a", "b"]}},
        now=NOW,
        command_id="COMMAND-20260610-123000-notopic",
    )
    assert missing_topic["status"] == "failed"
    assert "topic is required" in missing_topic["errors"]

    too_few = ui_commands.submit_command(
        tmp_path,
        {"type": "meeting.start", "payload": {"topic": "Solo", "participants": ["only-one"]}},
        now=NOW,
        command_id="COMMAND-20260610-123000-solo",
    )
    assert too_few["status"] == "failed"
    assert any("participants" in error for error in too_few["errors"])


# ----- TASK-AR-329: taskset lifecycle, move, bulk edit + undo, templates -----

REGISTRY_REL = "agents/project/work-items/TASKSET-DEFINITIONS.json"


def test_taskset_create_is_proposal_only_and_never_writes_registry(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.create", "payload": {"actor": "owner", "display_name": "Risk Watch", "summary": "watch risks"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tscreate",
    )

    assert result["status"] == "queued"
    assert result["result"]["task_set_id"] == "TASKSET-RISK-WATCH"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    # The console must NOT write the canonical registry directly.
    assert not (tmp_path / REGISTRY_REL).exists()
    proposal_files = list((tmp_path / ".ui_outbox" / "tasksets").glob("TASKSETREQ-*.json"))
    assert len(proposal_files) == 1
    proposal = json.loads(proposal_files[0].read_text(encoding="utf-8"))
    assert proposal["action"] == "create"
    assert proposal["task_set_id"] == "TASKSET-RISK-WATCH"
    assert "sync_taskset_registry" in proposal["sync"]
    # Runtime event recorded for traceability.
    event_path = tmp_path / "agents" / "runtime" / "events" / "ui_taskset_requests.jsonl"
    assert event_path.exists()


def test_taskset_rename_and_archive_emit_proposals(tmp_path):
    rename = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.rename", "target": "TASKSET-AR-DEMO", "payload": {"display_name": "Demo Renamed"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tsrename",
    )
    assert rename["status"] == "queued"
    assert rename["result"]["action"] == "rename"

    archive = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.archive", "target": "TASKSET-AR-DEMO", "payload": {}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tsarchive",
    )
    assert archive["status"] == "queued"
    assert archive["result"]["action"] == "archive"
    archive_proposal = json.loads(
        (tmp_path / ".ui_outbox" / "tasksets" / "TASKSETREQ-20260610-123000-tsarchive.json").read_text(encoding="utf-8")
    )
    assert archive_proposal["archived"] is True
    assert not (tmp_path / REGISTRY_REL).exists()


def test_taskset_rename_requires_display_name(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.rename", "target": "TASKSET-AR-DEMO", "payload": {}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tsnoname",
    )
    assert result["status"] == "failed"
    assert "display_name is required" in result["errors"]


def test_taskset_template_instantiates_recurring_pattern(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.template", "payload": {"actor": "owner", "template": "analysis-suite", "display_name": "Q3 Analysis"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tstpl",
    )
    assert result["status"] == "queued"
    assert result["result"]["task_count"] == 4
    assert result["result"]["task_set_id"] == "TASKSET-Q3-ANALYSIS"
    proposal = json.loads(
        (tmp_path / ".ui_outbox" / "tasksets" / "TASKSETTPL-20260610-123000-tstpl.json").read_text(encoding="utf-8")
    )
    assert proposal["taskset_create"]["payload"]["task_set_id"] == "TASKSET-Q3-ANALYSIS"
    assert len(proposal["tasks"]) == 4
    assert all(t["payload"]["task_set_id"] == "TASKSET-Q3-ANALYSIS" for t in proposal["tasks"])
    # No tasks or registry written directly by the console.
    assert not (tmp_path / REGISTRY_REL).exists()
    assert not list((tmp_path / "agents" / "lead_engineer" / "tasks").glob("TASK-*.md")) if (tmp_path / "agents" / "lead_engineer" / "tasks").exists() else True


def test_taskset_template_rejects_unknown_key(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "taskset.template", "payload": {"template": "nope"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-tsbad",
    )
    assert result["status"] == "failed"
    assert any("unknown taskset template" in error for error in result["errors"])


def test_task_move_changes_task_set_id_and_syncs_board(tmp_path):
    _write_backlog_board_script(tmp_path)
    path = _task(tmp_path, "TASK-UI-500")

    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.move", "target": "TASK-UI-500", "payload": {"task_set_id": "TASKSET-AR-NEW-HOME"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-move",
    )
    assert result["status"] == "accepted"
    assert result["result"]["backlog_board_updated"] is True
    assert "task_set_id: TASKSET-AR-NEW-HOME" in path.read_text(encoding="utf-8")


def test_task_move_rejects_invalid_taskset_id(tmp_path):
    _write_backlog_board_script(tmp_path)
    _task(tmp_path, "TASK-UI-501")
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.move", "target": "TASK-UI-501", "payload": {"task_set_id": "not-a-taskset"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-movebad",
    )
    assert result["status"] == "failed"
    assert any("invalid taskset id" in error for error in result["errors"])


def test_task_bulk_edit_applies_to_all_and_captures_undo_snapshot(tmp_path):
    _write_backlog_board_script(tmp_path)
    _task(tmp_path, "TASK-UI-600", status="planned")
    _task(tmp_path, "TASK-UI-601", status="planned")

    result = ui_commands.submit_command(
        tmp_path,
        {
            "type": "task.bulk_edit",
            "payload": {"task_ids": ["TASK-UI-600", "TASK-UI-601"], "status": "in_progress", "priority": "P0"},
        },
        now=NOW,
        command_id="COMMAND-20260610-123000-bulk",
    )
    assert result["status"] == "accepted"
    assert result["result"]["count"] == 2
    undo = result["result"]["undo"]
    assert undo["type"] == "task.bulk_edit"
    befores = {item["id"]: item["before"] for item in undo["items"]}
    assert befores["TASK-UI-600"]["status"] == "planned"
    assert befores["TASK-UI-600"]["priority"] == "P1"

    state = ui_state.build_state(tmp_path, now=NOW)
    statuses = {task["id"]: task["status"] for task in state["tasks"]}
    assert statuses["TASK-UI-600"] == "in_progress"
    assert statuses["TASK-UI-601"] == "in_progress"

    # Undo path is itself a bulk_edit using the captured before-state.
    undo_result = ui_commands.submit_command(
        tmp_path,
        {"type": "task.bulk_edit", "payload": {"task_ids": ["TASK-UI-600", "TASK-UI-601"], "status": "planned", "priority": "P1"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-undo",
    )
    assert undo_result["status"] == "accepted"
    state2 = ui_state.build_state(tmp_path, now=NOW)
    statuses2 = {task["id"]: task["status"] for task in state2["tasks"]}
    assert statuses2["TASK-UI-600"] == "planned"


def test_task_bulk_edit_requires_ids_and_fields(tmp_path):
    no_ids = ui_commands.submit_command(
        tmp_path,
        {"type": "task.bulk_edit", "payload": {"status": "planned"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-noids",
    )
    assert no_ids["status"] == "failed"
    assert any("task_ids" in error for error in no_ids["errors"])

    _task(tmp_path, "TASK-UI-700")
    no_fields = ui_commands.submit_command(
        tmp_path,
        {"type": "task.bulk_edit", "payload": {"task_ids": ["TASK-UI-700"]}},
        now=NOW,
        command_id="COMMAND-20260610-123000-nofields",
    )
    assert no_fields["status"] == "failed"
    assert any("at least one of status/priority/owner" in error for error in no_fields["errors"])


def test_new_command_types_in_allowlist():
    for command_type in ["taskset.create", "taskset.rename", "taskset.archive", "taskset.template", "task.move", "task.bulk_edit"]:
        assert command_type in ui_commands.COMMAND_TYPES


# --- Team/role assignment change command (TASK-AR-337) ---------------------


def test_assignment_set_is_proposal_only(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "assignment.set", "target": "TASK-AR-001", "payload": {"team": "Agent Runtime Core", "role": "qa", "actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-assign",
    )
    assert result["status"] == "queued"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    # Team/role are normalized to safe slugs.
    assert result["result"]["assignment"] == {"team": "agent-runtime-core", "role": "qa"}

    # A proposal file is written under .ui_outbox/assignments -- NOT the task file.
    proposals = list((tmp_path / ".ui_outbox" / "assignments").glob("ASSIGNREQ-*.json"))
    assert len(proposals) == 1
    stored = json.loads(proposals[0].read_text(encoding="utf-8"))
    assert stored["type"] == "assignment.set"
    assert stored["task_id"] == "TASK-AR-001"
    assert stored["mutation_boundary"] == "proposal_only"
    # No task file was created/edited by the console.
    assert not (tmp_path / "agents" / "lead_engineer" / "tasks").exists()


def test_assignment_set_requires_a_field_and_valid_task(tmp_path):
    no_fields = ui_commands.submit_command(
        tmp_path,
        {"type": "assignment.set", "target": "TASK-AR-001", "payload": {"actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-assign-nofields",
    )
    assert no_fields["status"] == "failed"
    assert any("at least one of team/role/assignee" in error for error in no_fields["errors"])

    bad_id = ui_commands.submit_command(
        tmp_path,
        {"type": "assignment.set", "target": "NOT-A-TASK", "payload": {"team": "core"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-assign-badid",
    )
    assert bad_id["status"] == "failed"
    assert any("invalid task id" in error for error in bad_id["errors"])


def test_assignment_set_rejects_direct_file_mutation(tmp_path):
    unsafe = ui_commands.submit_command(
        tmp_path,
        {"type": "assignment.set", "target": "TASK-AR-001", "payload": {"team": "core", "path": "/etc/passwd"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-assign-unsafe",
    )
    assert unsafe["status"] == "failed"
    assert any("direct file mutation is not allowed" in error for error in unsafe["errors"])


def test_assignment_command_type_in_allowlist():
    assert "assignment.set" in ui_commands.COMMAND_TYPES


# --- TASK-AR-338: @mention, message pin/react, notification prefs ----------


def test_mention_notify_emits_runtime_message_proposal(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "mention.notify", "target": "@lead-engineer", "payload": {"message": "please look", "actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-mention",
    )
    assert result["status"] == "queued"
    assert result["result"]["mention_target"] == "lead-engineer"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    # A runtime message (proposal-only) is queued under agents/messages/inbox.
    messages = list((tmp_path / "agents" / "messages" / "inbox").glob("MSG-*.md"))
    assert len(messages) == 1
    body = messages[0].read_text(encoding="utf-8")
    assert "to: lead-engineer" in body
    assert "@lead-engineer please look" in body
    # The mention is then aggregated by the notification center.
    notifications = ui_state.build_notifications(
        [], {"reminders": []}, [], ui_state.load_messages(tmp_path, NOW, []), ui_state.load_notifications_config(tmp_path, NOW, []), NOW
    )
    mentions = [item for item in notifications["notifications"] if item["kind"] == "mention"]
    assert any(item["mention_target"] == "lead-engineer" for item in mentions)


def test_mention_notify_requires_target_and_message(tmp_path):
    no_target = ui_commands.submit_command(
        tmp_path,
        {"type": "mention.notify", "payload": {"message": "hi", "actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-mention-notarget",
    )
    assert no_target["status"] == "failed"
    assert any("mention target is required" in error for error in no_target["errors"])

    no_msg = ui_commands.submit_command(
        tmp_path,
        {"type": "mention.notify", "target": "owner", "payload": {"actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-mention-nomsg",
    )
    assert no_msg["status"] == "failed"
    assert any("mention message is required" in error for error in no_msg["errors"])


def test_message_pin_is_proposal_only(tmp_path):
    result = ui_commands.submit_command(
        tmp_path,
        {"type": "message.pin", "target": "MSG-20260610-1", "payload": {"actor": "owner"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-pin",
    )
    assert result["status"] == "queued"
    assert result["result"]["mutation_boundary"] == "proposal_only"
    assert result["result"]["pinned"] is True
    proposals = list((tmp_path / ".ui_outbox" / "messages").glob("MSGREQ-*.json"))
    assert len(proposals) == 1
    stored = json.loads(proposals[0].read_text(encoding="utf-8"))
    assert stored["action"] == "pin"
    assert stored["message_id"] == "MSG-20260610-1"
    # No canonical message file was written by the console.
    assert not (tmp_path / "agents" / "messages" / "inbox").exists()


def test_message_react_normalizes_to_safe_reaction(tmp_path):
    ok = ui_commands.submit_command(
        tmp_path,
        {"type": "message.react", "target": "MSG-1", "payload": {"reaction": "ack", "actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-react-ok",
    )
    assert ok["status"] == "queued"
    assert ok["result"]["reaction"] == "ack"

    bad = ui_commands.submit_command(
        tmp_path,
        {"type": "message.react", "target": "MSG-1", "payload": {"reaction": "<script>", "actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-react-bad",
    )
    assert bad["status"] == "failed"
    assert any("invalid reaction" in error for error in bad["errors"])


def test_notification_commands_are_proposal_only(tmp_path):
    read = ui_commands.submit_command(
        tmp_path,
        {"type": "notification.read", "target": "notif:blocked:TASK-AR-1", "payload": {"actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-read",
    )
    assert read["status"] == "queued"
    assert read["result"]["mutation_boundary"] == "proposal_only"

    sub = ui_commands.submit_command(
        tmp_path,
        {"type": "notification.subscribe", "payload": {"kinds": ["blocked", "bogus"], "severities": ["overdue"], "actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-sub",
    )
    assert sub["status"] == "queued"
    # Unknown axis values are filtered out; only valid kinds/severities survive.
    assert sub["result"]["preference"]["kinds"] == ["blocked"]
    assert sub["result"]["preference"]["severities"] == ["overdue"]

    mute = ui_commands.submit_command(
        tmp_path,
        {"type": "notification.mute", "payload": {"keyword": "noisy", "actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-mute",
    )
    assert mute["status"] == "queued"
    assert mute["result"]["preference"]["keyword"] == "noisy"

    # All write to .ui_outbox/notifications, never the canonical config file.
    proposals = list((tmp_path / ".ui_outbox" / "notifications").glob("NOTIFREQ-*.json"))
    assert len(proposals) == 3
    assert not (tmp_path / "agents" / "project" / "ui" / "notifications.json").exists()


def test_notification_subscribe_requires_an_axis(tmp_path):
    empty = ui_commands.submit_command(
        tmp_path,
        {"type": "notification.subscribe", "payload": {"actor": "ui"}},
        now=NOW,
        command_id="COMMAND-20260610-123000-sub-empty",
    )
    assert empty["status"] == "failed"
    assert any("at least one of kinds/severities/tasksets" in error for error in empty["errors"])


def test_ar338_command_types_in_allowlist():
    for command_type in ["mention.notify", "message.pin", "message.react", "notification.read", "notification.mute", "notification.subscribe"]:
        assert command_type in ui_commands.COMMAND_TYPES
