import json
import re
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
    assert b'id="primary-sidebar"' in html.body
    assert b">Home<" in html.body
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
        ".sidebar-toggle",
        ".sidebar.is-open",
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
        "translateX(-100%)",
        "translateX(0)",
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


# ----- TASK-AR-326: realtime presence + live map -----


def test_ui_console_live_map_route_serves_typed_graph(tmp_path):
    _write_task(tmp_path, "TASK-UI-326")
    _write(
        tmp_path / "agents" / "messages" / "inbox" / "MSG-20260613-live.md",
        "\n".join(
            [
                "---",
                "id: MSG-20260613-live",
                "from: owner",
                "to: lead-engineer",
                "type: instruction",
                "status: queued",
                "ts: 2026-06-13T10:00:00+09:00",
                "task_id: TASK-UI-326",
                "---",
                "",
                "Live map check.",
                "",
            ]
        ),
    )

    underscore = ui_console.build_response("/api/live_map", tmp_path)
    hyphen = ui_console.build_response("/api/live-map", tmp_path)
    assert underscore.status == 200 and hyphen.status == 200
    payload = json.loads(underscore.body.decode("utf-8"))
    assert payload["resource"] == "live_map"
    live_map = payload["items"]
    assert live_map["schema"] == "agent-runtime-live-map/v1"
    assert {"nodes", "edges", "presence", "totals"} <= set(live_map.keys())
    assert any(node["kind"] == "owner" for node in live_map["nodes"])
    assert any(edge["kind"] == "message" for edge in live_map["edges"])


def test_ui_console_live_map_view_renders_graph_presence_and_activity_feed(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # The live map enhances the existing map view (no brand-new top-level view).
    assert 'id="view-map"' in html
    assert 'id="live-map-graph"' in html       # SVG node/edge stage
    assert 'id="live-map-presence"' in html     # presence summary line
    assert 'id="activity-feed"' in html         # activity-feed toast host

    # JS: live-map render + SSE pulse wiring + activity toast feed present.
    assert "function renderLiveMap(" in js
    assert "function reconcileLiveMap(" in js
    assert "function pulseLiveEdge(" in js
    assert "function pushActivityToast(" in js
    assert "reconcileLiveMap(previous, runtimeState)" in js  # wired into the SSE stream
    assert "renderLiveMap()" in js  # invoked from renderMap (periodic + live refresh)

    # CSS styles the graph + pulse highlight + toast.
    assert ".live-map-edge" in css
    assert ".is-pulsing" in css
    assert ".activity-toast" in css


def test_ui_console_live_map_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-326 tokenization guard) Every color the live-map CSS introduces
    # must flow through var(--token); no raw hex/rgba outside the token blocks.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    live_lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".live-map", ".activity-feed", ".activity-toast", "--pulse"))
    ]
    assert live_lines, "expected live-map CSS rules to exist"
    for line in live_lines:
        assert not hex_pattern.search(line), f"raw hex in live-map CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in live-map CSS: {line.strip()}"

    # The new pulse tokens are defined in BOTH theme blocks.
    assert "--pulse:" in _root_token_block(css)
    assert "--pulse:" in _dark_theme_block(css)
    # And the live-map consumes semantic tokens.
    assert "stroke: var(--pulse)" in css
    assert "background: var(--surface-grad)" in css


def test_ui_console_unknown_path_returns_404(tmp_path):
    response = ui_console.build_response("/missing", tmp_path)

    assert response.status == 404
    assert response.content_type == "text/plain; charset=utf-8"


def test_ui_console_favicon_route_is_quiet_for_browser_probe(tmp_path):
    response = ui_console.build_response("/favicon.ico", tmp_path)

    assert response.status == 204
    assert response.content_type == "image/x-icon"
    assert response.body == b""


def test_ui_console_board_card_exposes_peek_dnd_and_quick_action_anchors(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Shell hosts for peek popover and DnD live region.
    for host_id in ["board-peek", "board-dnd-status"]:
        assert host_id in html
    assert 'role="tooltip"' in html

    # Card markup carries peek, drag, and quick-action affordances.
    for marker in [
        'draggable="true"',
        "data-peek-task",
        "data-task-lane",
        "data-task-order",
        'data-quick-action="claim"',
        'data-quick-action="verify"',
        'data-quick-action="close"',
        "buildPeekMarkup",
        "showPeek",
        "schedulePeek",
        "hidePeek",
        "wireLaneDropTarget",
        "wireBoardCard",
        "handleBoardKeyboardDnd",
        "commitTaskMove",
        "quickAction",
    ]:
        assert marker in js

    for selector in [
        ".board-peek",
        ".board-dnd-status",
        ".lane.is-drop-target",
        ".lane-body.is-dragover",
        ".task-card.is-dragging",
        ".task-card.is-lifted",
        ".task-card-actions",
    ]:
        assert selector in css


def test_ui_console_board_dnd_has_keyboard_equivalents(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    handler = js.split("function handleBoardKeyboardDnd", 1)[1].split("\nfunction renderKanban", 1)[0]

    # Lift (Ctrl/Cmd+D), move (arrows), drop (Space/Enter), cancel (Esc).
    assert '"d"' in handler and "ctrlKey" in handler and "metaKey" in handler
    assert '"Escape"' in handler
    assert '" "' in handler
    assert "ArrowLeft" in handler and "ArrowRight" in handler
    assert "ArrowUp" in handler and "ArrowDown" in handler
    # Keyboard drop routes through the same proposal command path.
    assert "commitTaskMove" in handler


def test_ui_console_board_dnd_and_quick_actions_use_command_path_not_file_write(tmp_path):
    # Drag-drop reorder and quick actions must emit proposals through the
    # command endpoints, never mutate task files directly from the console.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    move_block = js.split("async function commitTaskMove", 1)[1].split("\n}", 1)[0]
    assert "/api/tasks/" in move_block and "/reorder" in move_block
    assert 'type: "task.reorder"' in move_block
    assert "writeFile" not in move_block and "fs." not in move_block

    action_block = js.split("async function quickAction", 1)[1].split("\nfunction laneTasksFor", 1)[0]
    assert "/api/commands" in action_block
    assert "/archive" in action_block
    assert 'type: "task.update"' in action_block
    assert 'type: "runtime.request_review"' in action_block
    assert 'type: "task.archive"' in action_block
    assert "writeFile" not in action_block and "fs." not in action_block


def test_ui_console_board_reorder_move_emits_proposal_command(tmp_path):
    # A cross-lane move sends order + the new lane status through the reorder
    # command route, producing an accepted (proposal) command record.
    _write_backlog_board_script(tmp_path)
    _write_task(tmp_path, "TASK-UI-362")

    response = ui_console.build_response(
        "/api/tasks/TASK-UI-362/reorder",
        tmp_path,
        method="POST",
        body=json.dumps({"order": 0, "status": "review"}).encode("utf-8"),
    )
    record = json.loads(response.body.decode("utf-8"))
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))

    assert response.status == 202
    assert record["status"] == "accepted"
    assert record["type"] == "task.reorder"
    moved = next(task for task in state["tasks"] if task["id"] == "TASK-UI-362")
    assert moved["status"] == "review"
    assert moved["lane"] == "Review"


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


# --- Theme system: Notion-style light default + dark toggle (TASK-AR-320) ----


def _root_token_block(css: str) -> str:
    # Isolate the :root { ... } declaration block (the default light theme).
    start = css.index(":root {")
    return css[start : css.index("}", start)]


def _dark_theme_block(css: str) -> str:
    # Isolate the [data-theme="dark"] { ... } override block.
    start = css.index('[data-theme="dark"] {')
    return css[start : css.index("}", start)]


def test_ui_console_theme_light_tokens_default_on_root(tmp_path):
    # (a) The default :root block carries the Notion-style LIGHT palette.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    root = _root_token_block(css)

    # Light-theme draft values from the V2 plan §2.1.
    for token, value in [
        ("--canvas", "#ffffff"),
        ("--panel", "#f7f7f5"),
        ("--panel-strong", "#f1f1ef"),
        ("--ink", "#37352f"),
        ("--muted", "#787774"),
        ("--subtle", "#9b9a97"),
        ("--line", "#e9e9e7"),
        ("--line-strong", "#d3d1cb"),
        ("--primary", "#2e6fdb"),
        ("--success", "#0f7b55"),
        ("--warning", "#cb7509"),
        ("--danger", "#e03e3e"),
    ]:
        assert f"{token}: {value};" in root, f"missing light token {token}: {value}"

    # color-scheme hint so native form controls match the light surface.
    assert "color-scheme: light;" in root


def test_ui_console_theme_dark_override_block_preserves_linear_palette(tmp_path):
    # (b) A dark-theme override block restores the original Linear dark tokens.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    assert '[data-theme="dark"] {' in css
    dark = _dark_theme_block(css)

    for token, value in [
        ("--canvas", "#010102"),
        ("--panel", "#0f1011"),
        ("--ink", "#f7f8f8"),
        ("--muted", "#a2a8b3"),
        ("--line", "#23252a"),
        ("--primary", "#5e6ad2"),
        ("--success", "#27a644"),
        ("--warning", "#d99a2b"),
        ("--danger", "#f04438"),
    ]:
        assert f"{token}: {value};" in dark, f"dark token {token} not preserved"

    assert "color-scheme: dark;" in dark


def test_ui_console_theme_status_colors_consistent_across_themes(tmp_path):
    # Status semantic tokens (green/amber/red/blue/purple) exist in both themes
    # so meaning stays stable; labels (not color) remain the primary signal.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    root = _root_token_block(css)
    dark = _dark_theme_block(css)
    for token in ["--success", "--warning", "--danger", "--info", "--purple"]:
        assert token in root, f"{token} missing from light theme"
        assert token in dark, f"{token} missing from dark theme"


def test_ui_console_theme_toggle_control_and_bootstrap_served(tmp_path):
    # (c) Toggle control in served HTML; localStorage + prefers-color-scheme
    #     bootstrap present in both the no-flash head script and app.js.
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    # Header toggle button shipped in the served shell.
    assert 'id="theme-toggle"' in html
    assert 'id="theme-toggle-label"' in html
    assert 'aria-pressed' in html

    # No-flash inline bootstrap in <head> reads storage + OS preference.
    assert "agent-runtime-theme" in html
    assert "prefers-color-scheme: dark" in html
    assert 'setAttribute("data-theme"' in html

    # app.js wires the toggle, persistence, and auto-detection.
    for marker in [
        "THEME_STORAGE_KEY",
        "prefers-color-scheme: dark",
        "localStorage",
        "toggleTheme",
        "initTheme",
        "systemPrefersDark",
        'setAttribute("data-theme"',
    ]:
        assert marker in js, f"theme bootstrap marker missing from app.js: {marker}"


def test_ui_console_theme_key_panels_use_tokens_not_raw_hex(tmp_path):
    # (d) The themed selectors converted in this task must reference var(--...)
    #     and carry no raw hex/rgba literals (those live only in token blocks).
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Strip the two token-definition blocks; the rest of the stylesheet should
    # be literal-color free (the brand glyph keeps deliberate white strokes).
    root = _root_token_block(css)
    dark = _dark_theme_block(css)
    body_css = css.replace(root, "").replace(dark, "")

    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in body_css.splitlines():
        if ".brand-mark" in line:
            continue
        # The brand-mark rect/stroke rules span a few lines; skip the literal
        # white values that intentionally sit on the colored brand gradient.
        if "stroke: #ffffff;" in line or "rgba(255, 255, 255, 0.14)" in line or "rgba(255, 255, 255, 0.72)" in line:
            continue
        assert not hex_pattern.search(line), f"raw hex outside token blocks: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba outside token blocks: {line.strip()}"

    # Spot-check that key panels consume tokens.
    for needle in [
        ".work-surface,",  # surface uses var(--surface-grad)
        "background: var(--surface-grad);",
        "background: var(--raise);",
        "background: var(--tile);",
        "background: var(--progress-fill);",
    ]:
        assert needle in css


# ----- TASK-AR-321: sidebar IA + hash routing -----

ALL_VIEW_IDS = [
    "board",
    "work",
    "meeting",
    "tasksets",
    "tsboard",
    "team",
    "agents",
    "messages",
    "events",
    "evidence",
    "planner",
    "roadmap",
    "map",
    "sources",
    "writes",
]

SIDEBAR_GROUPS = ["home", "work", "agents", "comms", "records", "ops"]


def test_ui_console_sidebar_replaces_horizontal_tabs(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # Collapsible left sidebar nav is present and the old horizontal tabs nav is gone.
    assert 'id="primary-sidebar"' in html
    assert 'class="sidebar"' in html
    assert '<nav class="tabs"' not in html
    assert 'class="tab "' not in html
    assert 'class="tab is-active"' not in html

    # Grouped nav sections from plan section 2.2.
    for group in SIDEBAR_GROUPS:
        assert f'data-group="{group}"' in html
    for label in ["WORK", "AGENTS", "COMMS", "RECORDS", "OPS"]:
        assert f">{label}<" in html


def test_ui_console_sidebar_keeps_all_nine_plus_views_reachable(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # Every existing view id must stay rendered AND reachable from a sidebar link.
    for view in ALL_VIEW_IDS:
        assert f'id="view-{view}"' in html
        assert f'data-view="{view}"' in html


def test_ui_console_sidebar_links_carry_hash_routes(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    for route in [
        "home/board",
        "work/tasksets",
        "work/board",
        "agents/team",
        "agents/map",
        "comms/channels",
        "comms/meetings",
        "records/events",
        "ops/writes",
    ]:
        assert f'data-route="{route}"' in html


def test_ui_console_hash_routing_wiring_present(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    # hashchange handler + initial-hash bootstrap.
    assert 'addEventListener("hashchange"' in js
    assert "applyHashRoute" in js
    assert "window.location.hash" in js
    assert "function activateView" in js
    assert "function viewForRoute" in js
    assert "function routeForView" in js
    # Pinned active-taskset progress is always rendered.
    assert "renderSidebarActiveTaskset" in js


def test_ui_console_collapsed_rail_and_mobile_overlay_css(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Collapsed icon-rail anchors.
    assert ".sidebar" in css
    assert '.sidebar[data-collapsed="true"]' in css
    assert "--sidebar-rail" in css
    assert ".sidebar-icon" in css
    assert ".sidebar-active-taskset" in css

    # Mobile overlay drawer anchors.
    mobile_css = css.split("@media (max-width: 760px)", 1)[1]
    assert ".sidebar" in mobile_css
    assert "translateX(-100%)" in mobile_css
    assert ".sidebar.is-open" in mobile_css
    assert ".sidebar-toggle" in mobile_css
    assert ".sidebar-scrim" in css


# ---- TASK-AR-322: common list pattern (sort/filter/group/search + density) ----


def test_ui_console_list_toolbar_mounts_present_in_html(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # The shared toolbar must mount into >=3 existing list views without
    # disturbing the existing list container ids/render entry points.
    for mount in [
        'id="list-toolbar-agents"',
        'id="list-toolbar-messages"',
        'id="list-toolbar-events"',
    ]:
        assert mount in html
    # Existing list ids must be preserved.
    for preserved in ['id="agents-list"', 'id="messages-list"', 'id="events-list"']:
        assert preserved in html
    # Command palette dialog groundwork is present in the shell.
    assert 'id="command-palette"' in html
    assert 'id="command-palette-input"' in html


def test_ui_console_list_toolbar_controls_render(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Toolbar render helper plus the filter/sort/group/density control classes.
    for marker in [
        "function renderListToolbar",
        "function applyListControls",
        "list-search",
        "list-filter",
        "list-sort",
        "list-group",
        "list-density-btn",
        "list-saved-views",
        "list-save-view",
    ]:
        assert marker in js

    # Filters: status / priority / owner / taskset / tag / date.
    for facet in ['"status"', '"priority"', '"owner"', '"taskset"', '"tag"', '"date"']:
        assert facet in js
    assert "LIST_FILTER_KEYS" in js

    # Grouping options: taskset (default) / status / owner.
    assert "LIST_GROUP_OPTIONS" in js
    assert 'group: "taskset"' in js  # default group

    # Sorting: priority / updated-time / progress.
    assert "LIST_SORT_OPTIONS" in js
    for sort in ['value: "priority"', 'value: "updated"', 'value: "progress"']:
        assert sort in js

    # Density toggle: compact / cozy / detail (3 levels).
    assert 'LIST_DENSITY_LEVELS = ["compact", "cozy", "detail"]' in js

    # Toolbar + density CSS targets the served DOM classes.
    for selector in [
        ".list-toolbar",
        ".list-density-btn",
        ".list-density-btn.is-active",
        ".list-panel.density-compact",
        ".list-panel.density-cozy",
        ".list-panel.density-detail",
        ".command-palette",
    ]:
        assert selector in css


def test_ui_console_list_component_reused_in_at_least_three_views(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # The SAME component (renderGroupedList -> renderListToolbar/applyListControls)
    # must be wired into at least 3 list views.
    wired = [
        view
        for view in ("agents", "messages", "events", "evidence")
        if f'renderGroupedList("{view}"' in js
    ]
    assert len(wired) >= 3, wired
    assert {"agents", "messages", "events"}.issubset(set(wired))


def test_ui_console_list_controls_persist_to_url_and_localstorage(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Persistence wiring: URL query params + localStorage, plus named saved views.
    for marker in [
        "function persistListControls",
        "function loadListControls",
        "window.localStorage.setItem",
        "window.localStorage.getItem",
        "window.history.replaceState",
        "URLSearchParams",
        "function saveNamedView",
        "function applyNamedView",
        "readUrlListControls",
    ]:
        assert marker in js


def test_ui_console_command_palette_and_keyboard_nav_handlers_present(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Command palette (Ctrl+K) groundwork.
    assert "function openCommandPalette" in js
    assert "function closeCommandPalette" in js
    assert 'event.key === "k"' in js
    assert "event.ctrlKey || event.metaKey" in js
    # Keyboard navigation (j / k / Enter) over list rows.
    assert "function handleListKeyboardNav" in js
    assert 'event.key === "j"' in js
    assert 'event.key === "k"' in js
    assert "function moveListCursor" in js
    assert "function activateListCursor" in js


def test_ui_console_taskset_completion_banner_anchors_and_route(tmp_path):
    # TASK-AR-328: completion banner + next-taskset suggestion on the Tasksets view.
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Banner host lives inside the tasksets view, hidden until a completion event.
    assert 'id="taskset-completion-banner"' in html

    for marker in [
        "function renderTasksetCompletion",
        "taskset_completion",
        "next_suggestion",
        "awaiting approval",
        "stop &amp; report",
    ]:
        assert marker in js
    # renderTasksetCompletion is wired into the render loop.
    assert "renderTasksetCompletion();" in js

    for selector in [
        ".taskset-completion",
        ".taskset-completion-head",
        ".taskset-completion-badge",
        ".taskset-completion-next",
    ]:
        assert selector in css

    # API route serves the resource.
    underscore = ui_console.build_response("/api/taskset_completion", tmp_path)
    hyphen = ui_console.build_response("/api/taskset-completion", tmp_path)
    assert underscore.status == 200
    assert hyphen.status == 200
    payload = json.loads(hyphen.body.decode("utf-8"))
    assert payload["resource"] == "taskset_completion"


def test_ui_console_list_app_js_node_check(tmp_path):
    # Guard: the generated app.js must remain syntactically valid JavaScript.
    import shutil
    import subprocess

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    proc = subprocess.run(
        ["node", "--check", "-"],
        input=js,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
