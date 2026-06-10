import json
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import ui_console


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_task(root: Path, task_id: str = "TASK-AR-228") -> None:
    _write(
        root / "agents" / "lead_engineer" / "tasks" / f"{task_id}-console.md",
        "\n".join(
            [
                "---",
                f"id: {task_id}",
                "status: in_progress",
                "owner: lead-engineer",
                "priority: P0",
                "tags:",
                "  - ui-console",
                "---",
                "",
                "## Goal",
                "",
                "Render the read-only console.",
                "",
            ]
        ),
    )


def test_ui_console_serves_html_shell_and_assets(tmp_path):
    html = ui_console.build_response("/", tmp_path)
    css = ui_console.build_response("/app.css", tmp_path)
    js = ui_console.build_response("/app.js", tmp_path)

    assert html.status == 200
    assert html.content_type == "text/html; charset=utf-8"
    assert b'id="runtime-console-app"' in html.body
    assert b"Backlog" in html.body
    assert b"Agents" in html.body
    assert b"command-log" in html.body
    assert b"runtime-command-form" in html.body
    assert b"event-filter-type" in html.body
    assert b"evidence-list" in html.body
    assert b"errors-list" in html.body
    assert css.status == 200
    assert b"--ink" in css.body
    assert js.status == 200
    assert b"/api/state" in js.body
    assert b"/api/tasks" in js.body
    assert b"/api/messages" in js.body
    assert b"/api/commands" in js.body
    assert b"runtime.call_agent" in js.body
    assert b"filterEvents" in js.body


def test_ui_console_api_state_uses_ui_state_adapter(tmp_path):
    _write_task(tmp_path)

    response = ui_console.build_response("/api/state", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 200
    assert response.content_type == "application/json; charset=utf-8"
    assert payload["tasks"][0]["id"] == "TASK-AR-228"
    assert payload["tasks"][0]["source_path"] == "agents/lead_engineer/tasks/TASK-AR-228-console.md"


def test_ui_console_api_resource_routes_match_state_resources(tmp_path):
    _write_task(tmp_path, "TASK-AR-229")

    response = ui_console.build_response("/api/tasks", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))

    assert payload["resource"] == "tasks"
    assert payload["items"][0]["id"] == "TASK-AR-229"
    assert payload["sources"]


def test_ui_console_post_task_create_and_patch_update_routes(tmp_path):
    create = ui_console.build_response(
        "/api/tasks",
        tmp_path,
        method="POST",
        body=json.dumps(
            {
                "id": "TASK-UI-601",
                "title": "Created from route",
                "description": "Route-created task.",
                "status": "planned",
                "priority": "P2",
                "owner": "lead-engineer",
            }
        ).encode("utf-8"),
    )
    created = json.loads(create.body.decode("utf-8"))
    patch = ui_console.build_response(
        "/api/tasks/TASK-UI-601",
        tmp_path,
        method="PATCH",
        body=json.dumps({"status": "in_progress", "priority": "P0"}).encode("utf-8"),
    )
    patched = json.loads(patch.body.decode("utf-8"))
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))

    assert create.status == 202
    assert created["status"] == "accepted"
    assert patch.status == 202
    assert patched["status"] == "accepted"
    assert state["tasks"][0]["id"] == "TASK-UI-601"
    assert state["tasks"][0]["status"] == "in_progress"
    assert state["commands"][-1]["status"] == "accepted"


def test_ui_console_reorder_message_and_invalid_routes(tmp_path):
    _write_task(tmp_path, "TASK-UI-701")
    reorder = ui_console.build_response(
        "/api/tasks/TASK-UI-701/reorder",
        tmp_path,
        method="POST",
        body=json.dumps({"order": 2, "status": "ready"}).encode("utf-8"),
    )
    message = ui_console.build_response(
        "/api/messages",
        tmp_path,
        method="POST",
        body=json.dumps({"task_id": "TASK-UI-701", "comment": "Route comment", "to": "qa"}).encode("utf-8"),
    )
    invalid = ui_console.build_response(
        "/api/tasks/TASK-UI-701",
        tmp_path,
        method="PATCH",
        body=json.dumps({"status": "bad"}).encode("utf-8"),
    )

    assert reorder.status == 202
    assert message.status == 202
    assert invalid.status == 400
    failed = json.loads(invalid.body.decode("utf-8"))
    assert failed["status"] == "failed"
    assert "invalid status" in " ".join(failed["errors"])


def test_ui_console_archive_route_marks_task_complete(tmp_path):
    _write_task(tmp_path, "TASK-UI-801")

    response = ui_console.build_response(
        "/api/tasks/TASK-UI-801/archive",
        tmp_path,
        method="POST",
        body=b"{}",
    )
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))

    assert response.status == 202
    assert state["tasks"][0]["status"] == "completed"
    assert "Archive" in ui_console.JS


def test_ui_console_post_runtime_command_route_writes_agent_message(tmp_path):
    _write_task(tmp_path, "TASK-UI-901")

    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {
                "type": "runtime.call_agent",
                "target": "qa",
                "payload": {
                    "actor": "owner",
                    "instruction": "Review TASK-UI-901.",
                    "reason": "UI smoke for runtime command route.",
                    "task_id": "TASK-UI-901",
                },
            }
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert state["commands"][-1]["type"] == "runtime.call_agent"
    assert state["messages"][-1]["intent"] == "runtime.call_agent"
    assert state["messages"][-1]["to"] == "qa"


def test_ui_console_events_route_filters_by_query_params(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "events" / "qa.jsonl",
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

    response = ui_console.build_response(
        "/api/events?type=agent.error&agent=qa&task_id=TASK-UI-231&goal_id=goal-231&q=evidence",
        tmp_path,
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 200
    assert payload["resource"] == "events"
    assert [event["event"] for event in payload["items"]] == ["agent.error"]


def test_ui_console_unknown_path_returns_404(tmp_path):
    response = ui_console.build_response("/missing", tmp_path)

    assert response.status == 404
    assert response.content_type == "text/plain; charset=utf-8"


def test_ui_console_cli_dispatches_to_server(monkeypatch, tmp_path):
    captured = {}

    def fake_run_server(root, *, host, port):
        captured["root"] = root
        captured["host"] = host
        captured["port"] = port
        return 0

    monkeypatch.setattr(ui_console, "run_server", fake_run_server)

    assert cli_module.main(["ui-console", "--root", str(tmp_path), "--host", "127.0.0.1", "--port", "8765"]) == 0
    assert captured == {"root": tmp_path, "host": "127.0.0.1", "port": 8765}
