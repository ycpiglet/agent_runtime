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
