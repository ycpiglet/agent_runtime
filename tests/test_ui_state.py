import json
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import ui_state


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task_text(task_id: str, *, status: str = "in_progress", owner: str = "lead-engineer") -> str:
    return "\n".join(
        [
            "---",
            f"id: {task_id}",
            f"status: {status}",
            f"owner: {owner}",
            "priority: P0",
            "tags:",
            "  - ui-console",
            "  - runtime-api",
            "audit_log:",
            "  - BACKLOG.md",
            "created: 2026-06-10",
            "blocked_reason: waiting on sample data",
            "---",
            "",
            "## Goal",
            "",
            "Expose a safe read-only state API.",
            "",
            "## Scope",
            "",
            "- Preserve source pointers.",
            "",
        ]
    )


def test_ui_state_adapter_normalizes_runtime_records_with_source_metadata(tmp_path):
    root = tmp_path
    _write(root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-227-ui-state-api.md", _task_text("TASK-AR-227"))
    _write(
        root / "agents" / "messages" / "inbox" / "MSG-20260610-120000-ui.md",
        "\n".join(
            [
                "---",
                "id: MSG-20260610-120000-ui",
                "from: owner",
                "to: lead-engineer",
                "type: instruction",
                "status: queued",
                "ts: 2026-06-10T12:00:00+09:00",
                "intent: build-ui-state-api",
                "task_id: TASK-AR-227",
                "---",
                "",
                "Please build the read-only adapter.",
                "",
            ]
        ),
    )
    _write(
        root / "agents" / "runtime" / "events" / "lead-engineer-2026-06-10.jsonl",
        json.dumps(
            {
                "ts": "2026-06-10T12:01:00+09:00",
                "role": "lead-engineer",
                "event": "task_started",
                "task_id": "TASK-AR-227",
            }
        )
        + "\n",
    )
    _write(
        root / "agents" / "runtime" / "sessions" / "lead-engineer.json",
        json.dumps(
            {
                "agent_id": "agent-1",
                "role": "lead-engineer",
                "status": "active",
                "task_id": "TASK-AR-227",
                "provider": "codex",
                "model": "gpt-5-codex",
            }
        ),
    )
    _write(root / "STATUS.md", "## 2026-06-10 - UI State API\n\n- Summary: build adapter.\n")

    state = ui_state.build_state(root, now="2026-06-10T12:05:00+09:00")

    assert state["generated_at"] == "2026-06-10T12:05:00+09:00"
    assert state["tasks"][0]["id"] == "TASK-AR-227"
    assert state["tasks"][0]["lane"] == "In Progress"
    assert state["tasks"][0]["owner_agent"] == "lead-engineer"
    assert state["tasks"][0]["blocked_reason"] == "waiting on sample data"
    assert state["tasks"][0]["source_path"] == "agents/lead_engineer/tasks/TASK-AR-227-ui-state-api.md"
    assert state["tasks"][0]["source_kind"] == "task_markdown"
    assert state["messages"][0]["channel"] == "task:TASK-AR-227"
    assert state["messages"][0]["source_kind"] == "message_markdown"
    assert state["events"][0]["id"].endswith(":1")
    assert state["events"][0]["severity"] == "info"
    assert state["agents"][0]["id"] == "agent-1"
    assert state["agents"][0]["current_task_id"] == "TASK-AR-227"
    assert state["goals"][0]["source_path"] == "STATUS.md"
    assert all("last_read_at" in source and "freshness" in source for source in state["sources"])


def test_ui_state_adapter_missing_optional_runtime_dirs_returns_empty_collections_and_gaps(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-228-console.md",
        _task_text("TASK-AR-228", status="planned"),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:05:00+09:00")

    assert [task["id"] for task in state["tasks"]] == ["TASK-AR-228"]
    assert state["agents"] == []
    assert state["messages"] == []
    assert state["events"] == []
    assert state["goals"] == []
    gap_paths = {gap["path"] for gap in state["gaps"]}
    assert "agents/runtime/sessions" in gap_paths
    assert "agents/messages/inbox" in gap_paths
    assert "agents/runtime/events" in gap_paths
    assert "STATUS.md" in gap_paths


def test_ui_state_adapter_uses_korean_goal_heading_for_description(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-229-korean.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-229",
                "status: planned",
                "owner: lead-engineer",
                "priority: P1",
                "---",
                "",
                "## 목표",
                "",
                "한국어 목표 문장을 UI 설명으로 사용한다.",
                "",
                "## 완료 기준",
                "",
                "- 설명이 헤딩으로 깨지지 않는다.",
                "",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:05:00+09:00")

    assert state["tasks"][0]["description"] == "한국어 목표 문장을 UI 설명으로 사용한다."


def test_ui_state_adapter_reports_malformed_records_as_warnings(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "events" / "lead-engineer-2026-06-10.jsonl",
        '{"ts": "bad"\n',
    )
    _write(tmp_path / "agents" / "runtime" / "sessions" / "bad.json", "{not-json")

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:05:00+09:00")

    assert state["events"] == []
    assert state["agents"] == []
    warning_kinds = {warning["kind"] for warning in state["warnings"]}
    assert "event-jsonl-parse-error" in warning_kinds
    assert "session-json-parse-error" in warning_kinds


def test_ui_state_filters_events_and_derives_error_evidence_replay_views(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "events" / "qa-2026-06-10.jsonl",
        "\n".join(
            [
                json.dumps(
                    {
                        "ts": "2026-06-10T12:00:00+09:00",
                        "role": "qa",
                        "event": "agent.error",
                        "task_id": "TASK-UI-231",
                        "goal_id": "goal-231",
                        "error": "Replay failed on evidence gap",
                        "evidence": ["reviews/evidence-gap.md"],
                    }
                ),
                json.dumps(
                    {
                        "ts": "2026-06-10T12:01:00+09:00",
                        "role": "lead-engineer",
                        "event": "task.completed",
                        "task_id": "TASK-UI-232",
                        "goal_id": "goal-232",
                    }
                ),
            ]
        )
        + "\n",
    )
    _write(
        tmp_path / "agents" / "messages" / "inbox" / "MSG-20260610-evidence.md",
        "\n".join(
            [
                "---",
                "id: MSG-20260610-evidence",
                "from: qa",
                "to: lead-engineer",
                "type: review",
                "status: queued",
                "ts: 2026-06-10T12:02:00+09:00",
                "intent: evidence-review",
                "task_id: TASK-UI-231",
                "evidence: reviews/evidence-message.md",
                "---",
                "",
                "Evidence message body.",
                "",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:05:00+09:00")
    filtered = ui_state.filter_events(
        state["events"],
        {"type": "agent.error", "agent": "qa", "task_id": "TASK-UI-231", "goal_id": "goal-231", "q": "evidence gap"},
    )

    assert [event["event"] for event in filtered] == ["agent.error"]
    assert state["errors"][0]["event_id"] == state["events"][0]["id"]
    assert state["errors"][0]["message"] == "Replay failed on evidence gap"
    assert {item["evidence"] for item in state["evidence"]} == {"reviews/evidence-gap.md", "reviews/evidence-message.md"}
    assert [item["goal_id"] for item in state["replay"] if item["goal_id"] == "goal-231"]
    assert all(record["freshness"] == "present" and record["last_updated"] for record in state["events"])


def test_ui_state_cli_emits_selected_resource_json(tmp_path, capsys):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-227-ui-state-api.md",
        _task_text("TASK-AR-227"),
    )

    assert cli_module.main(["ui-state", "--root", str(tmp_path), "--resource", "tasks", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["resource"] == "tasks"
    assert payload["items"][0]["id"] == "TASK-AR-227"
    assert payload["sources"]
