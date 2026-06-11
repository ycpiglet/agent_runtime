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


def _write_backlog_board_script(root: Path) -> None:
    _write(
        root / "scripts" / "backlog_board.py",
        "\n".join(
            [
                "from pathlib import Path",
                "Path('BACKLOG-BOARD.md').write_text('synced\\n', encoding='utf-8')",
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
    assert b"graph-list" in html.body
    assert b"state-machine-list" in html.body
    assert b"roadmap-list" in html.body
    assert css.status == 200
    assert b"--ink" in css.body
    assert b"--canvas" in css.body
    assert b"--primary" in css.body
    assert b"#010102" in css.body
    assert js.status == 200
    assert b"/api/state" in js.body
    assert b"/api/tasks" in js.body
    assert b"/api/messages" in js.body
    assert b"/api/commands" in js.body
    assert b"runtime.call_agent" in js.body
    assert b"filterEvents" in js.body
    assert b"renderMap" in js.body


def test_ui_console_shell_css_targets_served_dom_classes(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for class_name in [
        "shell",
        "layout",
        "work-surface",
        "kanban",
        "create-form",
        "runtime-form",
        "filter-row",
        "evidence-grid",
        "list-panel",
        "is-active",
    ]:
        assert class_name in html

    for selector in [
        ".shell",
        ".layout",
        ".work-surface",
        ".kanban",
        ".create-form",
        ".runtime-form",
        ".filter-row",
        ".evidence-grid",
        ".list-panel",
        ".tab.is-active",
        ".view.is-active",
    ]:
        assert selector in css


def test_ui_console_backlog_cards_surface_status_priority_taskset_and_evidence(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for marker in [
        "task-card-header",
        "task-card-title",
        "task-card-summary",
        "task-card-meta",
        "task-card-evidence",
        "task-card-taskset",
        "evidenceCountForTask",
    ]:
        assert marker in js

    for label in ["Status", "Priority", "Task set", "Evidence"]:
        assert f">{label}<" in js

    for selector in [
        ".task-card-header",
        ".task-card-title",
        ".task-card-summary",
        ".task-card-meta",
        ".task-card-evidence",
        ".task-card-taskset",
        ".task-card.status-blocked",
        ".task-card.status-completed",
        ".lane-count",
    ]:
        assert selector in css

    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    assert ".task-card-meta" in mobile_css


def test_ui_console_api_state_uses_ui_state_adapter(tmp_path):
    _write_task(tmp_path)

    response = ui_console.build_response("/api/state", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 200
    assert response.content_type == "application/json; charset=utf-8"
    assert payload["tasks"][0]["id"] == "TASK-AR-228"
    assert payload["tasks"][0]["source_path"] == "agents/lead_engineer/tasks/TASK-AR-228-console.md"


def test_ui_console_agents_view_contains_progress_fields(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-progress.json",
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-progress",
                "task_id": "TASK-AR-248",
                "task_set_id": "TASKSET-AR-PROGRESS",
                "agent_role": "lead-engineer",
                "team_id": "agent-runtime-core",
                "agent_instance_id": "le-1",
                "display_name": "lead_engineer@ui-01",
                "callsite_id": "terminal:wt-task-ar-248:tab-01",
                "pane_id": "terminal:wt-task-ar-248:tab-01",
                "status": "working",
                "phase": "implement",
                "step_index": 3,
                "step_total": 6,
                "progress_pct": 48,
                "status_text": "Rendering task-set progress cards",
                "worktree_path": ".worktrees/TASK-AR-248",
                "branch": "codex/task-ar-248-ui-01",
                "claimed_at": "2026-06-10T18:00:00+09:00",
                "last_heartbeat": "2026-06-10T18:05:00+09:00",
            }
        ),
    )

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    api = json.loads(ui_console.build_response("/api/task-sets", tmp_path).body.decode("utf-8"))

    assert "status_text" in js
    assert "step_index" in js
    assert "progress_pct" in js
    assert "renderTaskSets" in js
    assert api["resource"] == "task_sets"
    assert api["items"][0]["id"] == "TASKSET-AR-PROGRESS"


def test_ui_console_agent_and_command_panes_surface_operational_hierarchy(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for marker in [
        "agent-card",
        "agent-card-meta",
        "agent-score",
        "agent-claim",
        "command-card",
        "command-card-meta",
        "command-payload",
        "command-result",
        "formatCommandValue",
    ]:
        assert marker in js

    for label in [
        "Role",
        "Status",
        "Score",
        "Claim",
        "Progress",
        "Type",
        "Target",
        "Payload",
        "Result",
        "Risk",
    ]:
        assert f">{label}<" in js

    for selector in [
        ".agent-card",
        ".agent-card-meta",
        ".agent-score",
        ".agent-claim",
        ".command-card",
        ".command-card-meta",
        ".command-payload",
        ".command-result",
        ".command-card.risk-high",
    ]:
        assert selector in css


def test_ui_console_event_and_evidence_panes_surface_audit_hierarchy(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for control_id in [
        "event-filter-type",
        "event-filter-agent",
        "event-filter-task",
        "event-filter-goal",
        "event-filter-search",
    ]:
        assert control_id in html

    for marker in [
        "audit-card",
        "audit-card-meta",
        "event-card",
        "error-card",
        "evidence-card",
        "replay-card",
        "auditToneClass",
        "renderAuditMeta",
    ]:
        assert marker in js

    for label in [
        "Event",
        "Severity",
        "Actor",
        "Task",
        "Goal",
        "Source",
        "Evidence",
        "Replay",
    ]:
        assert f">{label}<" in js

    for selector in [
        ".audit-card",
        ".audit-card-meta",
        ".event-card",
        ".error-card",
        ".evidence-card",
        ".replay-card",
        ".audit-card.pass",
        ".audit-card.warn",
        ".audit-card.fail",
    ]:
        assert selector in css


def test_ui_console_map_planner_source_and_write_panes_surface_boundaries(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for host_id in [
        "graph-list",
        "state-machine-list",
        "roadmap-list",
        "planning-proposals-list",
        "planning-scans-list",
        "planning-requests-list",
        "sources-list",
        "command-log",
    ]:
        assert host_id in html

    for marker in [
        "surface-card",
        "surface-card-meta",
        "map-card",
        "graph-card",
        "state-machine-card",
        "roadmap-card",
        "planning-card",
        "source-card",
        "boundaryClass",
        "renderSurfaceMeta",
    ]:
        assert marker in js

    for label in [
        "Boundary",
        "Kind",
        "Source",
        "From",
        "To",
        "Status",
        "Risk",
        "Mutation",
    ]:
        assert f">{label}<" in js

    for selector in [
        ".surface-card",
        ".surface-card-meta",
        ".map-card",
        ".graph-card",
        ".state-machine-card",
        ".roadmap-card",
        ".planning-card",
        ".source-card",
        ".boundary-read",
        ".boundary-write",
    ]:
        assert selector in css


def test_ui_console_api_resource_routes_match_state_resources(tmp_path):
    _write_task(tmp_path, "TASK-AR-229")

    response = ui_console.build_response("/api/tasks", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))

    assert payload["resource"] == "tasks"
    assert payload["items"][0]["id"] == "TASK-AR-229"
    assert payload["sources"]


def test_ui_console_post_task_create_and_patch_update_routes(tmp_path):
    _write_backlog_board_script(tmp_path)

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


def test_ui_console_task_mutation_fails_when_backlog_board_sync_missing(tmp_path):
    create = ui_console.build_response(
        "/api/tasks",
        tmp_path,
        method="POST",
        body=json.dumps(
            {
                "id": "TASK-UI-602",
                "title": "Created without board sync",
                "status": "planned",
                "priority": "P2",
            }
        ).encode("utf-8"),
    )
    payload = json.loads(create.body.decode("utf-8"))

    assert create.status == 400
    assert payload["status"] == "failed"
    assert "BACKLOG-BOARD.md sync failed" in " ".join(payload["errors"])


def test_ui_console_reorder_message_and_invalid_routes(tmp_path):
    _write_backlog_board_script(tmp_path)
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
    _write_backlog_board_script(tmp_path)
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


def test_ui_console_graph_state_and_roadmap_routes(tmp_path):
    _write_task(tmp_path, "TASK-UI-232")
    _write(
        tmp_path / "agents" / "messages" / "inbox" / "MSG-20260610-graph.md",
        "\n".join(
            [
                "---",
                "id: MSG-20260610-graph",
                "from: owner",
                "to: qa",
                "type: instruction",
                "status: queued",
                "ts: 2026-06-10T12:10:00+09:00",
                "intent: graph-check",
                "task_id: TASK-UI-232",
                "---",
                "",
                "Check graph routes.",
                "",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "project" / "STATE-MACHINES.yml",
        "\n".join(
            [
                "machines:",
                "  - id: task",
                "    initial: planned",
                "    states:",
                "      - id: planned",
                "      - id: in_progress",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "project" / "ROADMAP.md",
        "# Roadmap\n\n## Current Phase\n\n- phase: UI console\n\n## Milestones\n\n- [ ] 2026-06-20: Graph view ready\n",
    )

    graph = json.loads(ui_console.build_response("/api/graph", tmp_path).body.decode("utf-8"))
    machines = json.loads(ui_console.build_response("/api/state-machines", tmp_path).body.decode("utf-8"))
    roadmap = json.loads(ui_console.build_response("/api/roadmap", tmp_path).body.decode("utf-8"))

    assert graph["resource"] == "graph"
    assert any(edge["from"] == "owner" and edge["to"] == "qa" for edge in graph["items"]["edges"])
    assert machines["resource"] == "state_machines"
    assert machines["items"][0]["id"] == "task"
    assert roadmap["resource"] == "roadmap"
    assert roadmap["items"]["milestones"][0]["title"] == "Graph view ready"


def test_ui_console_unknown_path_returns_404(tmp_path):
    response = ui_console.build_response("/missing", tmp_path)

    assert response.status == 404
    assert response.content_type == "text/plain; charset=utf-8"


def test_ui_console_favicon_route_is_quiet_for_browser_probe(tmp_path):
    response = ui_console.build_response("/favicon.ico", tmp_path)

    assert response.status == 204
    assert response.content_type == "image/x-icon"
    assert response.body == b""


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
