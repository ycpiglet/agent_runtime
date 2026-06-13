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
                "ROOT = Path(__file__).resolve().parents[1]",
                "(ROOT / 'BACKLOG-BOARD.md').write_text('synced\\n', encoding='utf-8')",
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
    assert b"Tasksets" in html.body
    assert b"Agents" in html.body
    assert b"command-log" in html.body
    assert b"runtime-command-form" in html.body
    assert b"taskset-filter" in html.body
    assert b"taskset-quick-list" in html.body
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
    assert b"/api/stream" in js.body
    assert b"/api/tasks" in js.body
    assert b"/api/messages" in js.body
    assert b"/api/commands" in js.body
    assert b"runtime.call_agent" in js.body
    assert b"planning.approve" in js.body
    assert b"planning.reject" in js.body
    assert b"filterEvents" in js.body
    assert b"queueTaskSetCommand" in js.body
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
        "taskset-toolbar",
        "taskset-grid",
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
        ".taskset-toolbar",
        ".taskset-grid",
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
    assert "primary_alias" in js
    assert "taskset-action" in js
    assert "renderTaskSetDirectory" in js
    assert api["resource"] == "task_sets"
    assert api["items"][0]["id"] == "TASKSET-AR-PROGRESS"


def test_ui_console_taskset_directory_surfaces_aliases_and_safe_commands(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for marker in [
        "view-tasksets",
        "taskset-filter",
        "taskset-status-filter",
        "taskset-quick-list",
    ]:
        assert marker in html

    for marker in [
        "taskSetCards",
        "taskSetInstruction",
        "queueTaskSetCommand",
        "primary_alias",
        "runtime.assign_task",
        "runtime.request_review",
        "taskSetCommand",
    ]:
        assert marker in js

    for selector in [
        ".taskset-toolbar",
        ".taskset-grid",
        ".taskset-card-header",
        ".taskset-card-meta",
        ".alias-row",
        ".taskset-actions",
        ".taskset-action",
        ".taskset-card.taskset-status-active",
    ]:
        assert selector in css


def test_ui_console_surfaces_multipane_assurance_panel(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert "multipane-assurance-list" in html
    assert "Multi-pane assurance" in js
    assert "active panes" in js
    assert "role coverage" in js
    assert "drift" in js
    assert "renderMultipaneAssurance" in js
    assert ".assurance-card" in css


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
        ".surface-card-meta strong.boundary-read",
        ".command-card-meta strong.boundary-write",
    ]:
        assert selector in css


def test_ui_console_responsive_accessibility_polish_contract(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    for selector in [
        ".tab:focus-visible",
        ".task-card:focus-visible",
        ".agent-card:focus-visible",
        ".command-card:focus-visible",
        ".audit-card:focus-visible",
        ".surface-card:focus-visible",
    ]:
        assert selector in css

    assert "outline: 2px solid var(--primary-hover)" in css
    assert "outline-offset: 2px" in css

    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    for selector in [
        ".topbar",
        ".toolbar",
        ".tabs",
        ".task-card-header",
        ".agent-card-header",
        ".command-card-header",
        ".audit-card-header",
        ".surface-card-header",
        ".state-chip",
        ".pill",
    ]:
        assert selector in mobile_css

    for marker in [
        "overflow-x: auto",
        "scroll-snap-type: x proximity",
        "flex-wrap: wrap",
        "max-width: 100%",
        "overflow-wrap: anywhere",
    ]:
        assert marker in mobile_css


def _write_work_classification(root: Path) -> None:
    records = [
        {
            "key": "initiative:INIT-AR-WORK-METADATA-ANALYTICS",
            "level": "initiative",
            "number": "1",
            "label": "Initiative 1",
            "id": "INIT-AR-WORK-METADATA-ANALYTICS",
            "title": "Work Metadata Analytics Initiative",
            "path": "agents/project/initiatives/INIT-AR-WORK-METADATA-ANALYTICS.md",
            "parent_id": "",
            "status": "planned",
        },
        {
            "key": "taskset:TASKSET-AR-WORK-METADATA-ANALYTICS",
            "level": "taskset",
            "number": "1.1",
            "label": "Taskset 1.1",
            "id": "TASKSET-AR-WORK-METADATA-ANALYTICS",
            "title": "Work Metadata Analyst",
            "path": "BACKLOG-BOARD.md",
            "parent_id": "INIT-AR-WORK-METADATA-ANALYTICS",
            "status": "active",
        },
        {
            "key": "task:TASK-AR-514",
            "level": "task",
            "number": "1.1.1",
            "label": "Task 1.1.1",
            "id": "TASK-AR-514",
            "title": "Work metadata schema",
            "path": "agents/lead_engineer/tasks/TASK-AR-514.md",
            "parent_id": "TASKSET-AR-WORK-METADATA-ANALYTICS",
            "status": "completed",
        },
        {
            "key": "task:TASK-AR-516",
            "level": "task",
            "number": "1.1.2",
            "label": "Task 1.1.2",
            "id": "TASK-AR-516",
            "title": "Work Explorer tree",
            "path": "agents/lead_engineer/tasks/TASK-AR-516.md",
            "parent_id": "TASKSET-AR-WORK-METADATA-ANALYTICS",
            "status": "planned",
        },
    ]
    _write(
        root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json",
        json.dumps(
            {
                "schema": "agent-runtime-work-item-classification/v1",
                "generated_at": "2026-06-13T02:56:29+09:00",
                "record_count": len(records),
                "finding_count": 0,
                "findings": [],
                "records": records,
            },
            ensure_ascii=False,
        ),
    )


def test_ui_console_work_explorer_route_serves_tree_resource(tmp_path):
    _write_work_classification(tmp_path)
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-514.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-514",
                "status: completed",
                "owner: lead_engineer",
                "priority: P1",
                "task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS",
                "evidence_refs:",
                "  - reviews/VERIFY-2026-06-12-task-ar-514.json",
                "---",
                "",
                "## Goal",
                "",
                "Define the work metadata schema.",
                "",
            ]
        ),
    )

    response = ui_console.build_response("/api/work_explorer", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))
    alias = json.loads(ui_console.build_response("/api/work-explorer", tmp_path).body.decode("utf-8"))

    assert response.status == 200
    assert payload["resource"] == "work_explorer"
    assert alias["resource"] == "work_explorer"
    nodes = {node["id"]: node for node in payload["items"]["nodes"]}
    taskset = nodes["TASKSET-AR-WORK-METADATA-ANALYTICS"]
    assert taskset["children"] == ["TASK-AR-514", "TASK-AR-516"]
    assert taskset["rollup"]["total"] == 2
    assert taskset["rollup"]["completed"] == 1
    assert taskset["rollup"]["pct"] == 50
    assert "reviews/VERIFY-2026-06-12-task-ar-514.json" in taskset["descendant_evidence_refs"]
    assert payload["items"]["roots"] == ["INIT-AR-WORK-METADATA-ANALYTICS"]
    assert payload["items"]["staleness_note"]


def test_ui_console_work_explorer_tab_tree_and_facet_anchors(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert 'data-view="work"' in html
    assert "Work Explorer" in html
    for host_id in [
        "view-work",
        "work-search",
        "work-depth-filter",
        "work-expand-all",
        "work-collapse-all",
        "work-staleness",
        "work-facets",
        "work-tree",
        "work-node-detail",
    ]:
        assert host_id in html

    for marker in [
        "renderWorkExplorer",
        "renderWorkTree",
        "renderWorkFacets",
        "renderWorkNodeDetail",
        "workNodeMatchesFacets",
        "workNodeMatchesSearch",
        "workRollupBadge",
        "collapsedWorkNodes",
        "workFacetSelections",
        "descendant_evidence_refs",
        "staleness_note",
        "data-work-toggle",
        "data-work-node",
        "work_explorer",
    ]:
        assert marker in js

    for selector in [
        ".work-toolbar",
        ".work-staleness",
        ".work-facets",
        ".facet-group",
        ".facet-option",
        ".work-grid",
        ".work-tree",
        ".work-node-row",
        ".work-node-children",
        ".rollup-badge",
        ".evidence-badge",
        ".work-node-detail",
        ".evidence-ref",
        ".work-node-row.bucket-completed",
        ".work-node-row.is-selected",
    ]:
        assert selector in css

    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    assert ".work-toolbar" in mobile_css
    assert ".work-grid" in mobile_css


def test_ui_console_tasksets_board_route_serves_grouped_cards(tmp_path):
    _write_work_classification(tmp_path)

    response = ui_console.build_response("/api/tasksets_board", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))
    alias = json.loads(ui_console.build_response("/api/tasksets-board", tmp_path).body.decode("utf-8"))

    assert response.status == 200
    assert payload["resource"] == "tasksets_board"
    assert alias["resource"] == "tasksets_board"
    assert payload["items"]["schema"] == "agent-runtime-tasksets-board/v1"
    assert payload["items"]["create_command"] == "task.create"

    card = next(c for c in payload["items"]["cards"] if c["id"] == "TASKSET-AR-WORK-METADATA-ANALYTICS")
    # Computed progress: 1 completed of 2 child tasks.
    assert card["progress"] == {"done": 1, "total": 2}
    assert card["progress_pct"] == 50
    assert {child["id"] for child in card["children"]} == {"TASK-AR-514", "TASK-AR-516"}


def test_ui_console_tasksets_board_tab_panel_and_css_anchors(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert 'data-view="tsboard"' in html
    for host_id in [
        "view-tsboard",
        "tsboard-filter",
        "tsboard-swimlane-toggle",
        "tsboard-expand-all",
        "tsboard-collapse-all",
        "tsboard-staleness",
        "tsboard-cards",
        "tsboard-swimlanes",
    ]:
        assert host_id in html

    for marker in [
        "renderTasksetBoard",
        "tasksetsBoardData",
        "tasksetBoardCards",
        "tasksetSwimlanes",
        "expandedTasksetCards",
        "tasksetSwimlaneMode",
        "queueTasksetAddTask",
        "tasksets_board",
        "data-tsboard-toggle",
        "data-tsboard-add",
    ]:
        assert marker in js

    for selector in [
        ".tsboard-toolbar",
        ".tsboard-cards",
        ".tsboard-card",
        ".tsboard-card.bucket-completed",
        ".phase-chip",
        ".dist-chip",
        ".agent-avatar",
        ".tsboard-children",
        ".tsboard-swimlane",
        ".tsboard-swim-card",
    ]:
        assert selector in css

    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    assert ".tsboard-cards" in mobile_css


def test_ui_console_tasksets_board_add_task_uses_command_path_not_file_write(tmp_path):
    # The add-task affordance must route through the task.create command path
    # (proposal-only) rather than mutating a task file directly.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    add_block = js.split("async function queueTasksetAddTask", 1)[1].split("\n}", 1)[0]
    assert '"/api/tasks"' in add_block
    assert 'type: "task.create"' in add_block
    assert "writeFile" not in add_block
    assert "fs." not in add_block


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


def test_ui_console_stream_and_replay_snapshot_routes(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "events" / "qa.jsonl",
        json.dumps(
            {
                "ts": "2026-06-10T12:00:00+09:00",
                "role": "qa",
                "event": "agent.error",
                "task_id": "TASK-UI-231",
                "goal_id": "goal-231",
            }
        )
        + "\n",
    )

    stream = ui_console.build_response("/api/stream", tmp_path)
    snapshot = ui_console.build_response("/api/replay/snapshot?at=2026-06-10T12:00:00%2B09:00", tmp_path)
    payload = json.loads(snapshot.body.decode("utf-8"))

    assert stream.status == 200
    assert stream.content_type == "text/event-stream; charset=utf-8"
    assert stream.body.startswith(b"event: state\n")
    assert payload["resource"] == "replay_snapshot"
    assert payload["task_ids"] == ["TASK-UI-231"]


def test_ui_console_planner_decision_routes_write_audit_record_without_apply(tmp_path):
    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {
                "type": "planning.approve",
                "payload": {
                    "actor": "owner",
                    "proposal_id": "PLAN-1",
                    "reason": "accept bounded proposal",
                    "apply": False,
                },
            }
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))
    decisions = list((tmp_path / "agents" / "planning" / "decisions").glob("*.json"))
    decision = json.loads(decisions[0].read_text(encoding="utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert decision["proposal_id"] == "PLAN-1"
    assert decision["canonical_mutation_allowed"] is False


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


def test_ui_console_roadmap_timeline_panel_and_routes(tmp_path):
    _write(
        tmp_path / "agents" / "project" / "VISION.md",
        "# Vision\n\n## Problem\n\nDrift.\n\n## Vision\n\nStandardize overlays.\n\n## Success metric\n\nMatches.\n",
    )
    _write(
        tmp_path / "agents" / "project" / "ROADMAP.md",
        "# Roadmap\n\n## Current Phase\n\n- phase: UI console\n\n## Milestones\n\n- [ ] 2026-06-20: `TASK-AR-516` ready\n",
    )
    _write(
        tmp_path / "agents" / "project" / "release" / "RELEASE-DECISION-v0.2.0.yml",
        "schema: agent-runtime-release-decision/v1\ntarget_version: 0.2.0\ntarget_tag: v0.2.0\nstatus: agent_council_approved\nowner_required: true\ndecision_date: 2026-06-13\n",
    )

    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Tab + view host anchors
    for anchor in ['data-view="roadmap"', 'id="view-roadmap"', 'id="roadmap-timeline"', 'id="roadmap-timeline-summary"']:
        assert anchor in html

    # JS render function and escaping wired in
    for marker in ["renderRoadmapTimeline", "roadmap_timeline", "roadmap-tl-milestone", "roadmap-tl-release", "escapeHtml(milestone.title"]:
        assert marker in js

    # CSS timeline anchors
    for selector in [".roadmap-timeline", ".roadmap-tl-marker", ".roadmap-tl-links", ".roadmap-tl-marker.is-release"]:
        assert selector in css

    # Routes: underscore + hyphen alias both return the resource with HTTP 200
    underscore = ui_console.build_response("/api/roadmap_timeline", tmp_path)
    hyphen = ui_console.build_response("/api/roadmap-timeline", tmp_path)
    assert underscore.status == 200
    assert hyphen.status == 200
    payload = json.loads(hyphen.body.decode("utf-8"))
    assert payload["resource"] == "roadmap_timeline"
    timeline = payload["items"]
    assert timeline["schema"] == "agent-runtime-roadmap-timeline/v1"
    assert timeline["vision"]["statement"]
    assert timeline["milestones"][0]["linked_work"][0]["id"] == "TASK-AR-516"
    assert timeline["releases"][0]["owner_required"] is True


# --- Team / Agent RPG presence (TASK-AR-324) -------------------------------


def _write_team_instance(root: Path, instance_id: str, **overrides) -> None:
    record = {
        "schema": "agent-runtime-agent-instance/v1",
        "agent_instance_id": instance_id,
        "callsign": f"claude/{instance_id}",
        "display_name": f"claude/{instance_id}",
        "role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "model": "claude-opus",
        "skill_versions": {"lead_engineer": "1.0.0"},
        "spawned_at": "2026-06-13T10:00:00+09:00",
    }
    record.update(overrides)
    _write(root / "agents" / "runtime" / "instances" / f"{instance_id}.json", json.dumps(record))


def test_ui_console_team_agents_route_serves_team_hierarchy(tmp_path):
    _write_team_instance(tmp_path, "inst-le-01", role="lead-engineer", team_id="agent-runtime-core")
    _write_team_instance(tmp_path, "inst-mp-02", role="managing-partner", team_id="governance-loop")

    response = ui_console.build_response("/api/team_agents", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))
    alias = json.loads(ui_console.build_response("/api/team-agents", tmp_path).body.decode("utf-8"))

    assert response.status == 200
    assert payload["resource"] == "team_agents"
    assert alias["resource"] == "team_agents"
    assert payload["items"]["schema"] == "agent-runtime-team-agents/v1"

    teams = {team["team_id"]: team for team in payload["items"]["teams"]}
    assert set(teams) == {"agent-runtime-core", "governance-loop"}
    card = teams["agent-runtime-core"]["agents"][0]
    assert card["id"] == "inst-le-01"
    assert card["role"] == "lead-engineer"
    assert card["level"] >= 1
    assert "xp_pct" in card


def test_ui_console_team_agents_tab_panel_and_css_anchors(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert 'data-view="team"' in html
    for host_id in [
        "view-team",
        "team-filter",
        "team-online-toggle",
        "team-summary",
        "team-org",
    ]:
        assert host_id in html

    for marker in [
        "renderTeamAgents",
        "teamAgentsData",
        "agentCharacterCard",
        "teamGroupBlock",
        "agentLevelBar",
        "teamOnlineOnly",
        "team_agents",
    ]:
        assert marker in js

    for selector in [
        ".team-org",
        ".team-group",
        ".team-cards",
        ".agent-character-card",
        ".agent-character-card.presence-working",
        ".agent-character-avatar",
        ".presence-ring",
        ".agent-character-meta",
    ]:
        assert selector in css

    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    assert ".team-cards" in mobile_css


def test_ui_console_team_agents_card_fields_are_escaped(tmp_path):
    # All rendered agent-card fields must flow through escapeHtml.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    card_block = js.split("function agentCharacterCard", 1)[1].split("\n}", 1)[0]
    for field in ["card.avatar", "card.callsign", "card.role", "card.model"]:
        assert f"escapeHtml({field}" in card_block
