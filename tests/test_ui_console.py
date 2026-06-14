import base64
import json
import re
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import ui_console
from agent_runtime import ui_state


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


# --- Workload heatmap + team assignment view (TASK-AR-337) ------------------


def test_ui_console_workload_view_registered_in_agents_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # New Workload view lives in the AGENTS group with a data-view + data-route.
    assert 'data-view="workload"' in html
    assert 'data-route="agents/workload"' in html
    for host_id in ["view-workload", "workload-grid", "workload-summary", "workload-legend"]:
        assert host_id in html
    # Scope toggle (by agent / by team).
    assert 'id="workload-scope-agents"' in html
    assert 'id="workload-scope-teams"' in html


def test_ui_console_workload_and_teams_api_routes(tmp_path):
    workload = ui_console.build_response("/api/workload", tmp_path)
    teams = ui_console.build_response("/api/teams", tmp_path)
    assert workload.status == 200
    assert teams.status == 200
    wl = json.loads(workload.body.decode("utf-8"))
    tm = json.loads(teams.body.decode("utf-8"))
    assert wl["resource"] == "workload"
    assert wl["items"]["schema"] == "agent-runtime-workload-heatmap/v1"
    assert tm["resource"] == "teams"
    assert tm["items"]["schema"] == "agent-runtime-teams/v1"


def test_ui_console_workload_render_markers_and_drilldown(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    for marker in [
        "renderWorkloadHeatmap",
        "workloadData",
        "workloadRow",
        "workloadCell",
        "setWorkloadScope",
        "renderWorkloadHeatmap()",  # wired into renderAll
        # Org-chart / heatmap drill-down filters the board by team/role.
        "drillToTeamTasks",
        "setBoardTeamFilter",
        "taskMatchesTeamFilter",
        "data-drill-team",
        "data-drill-role",
    ]:
        assert marker in js


def test_ui_console_workload_cell_fields_are_escaped(tmp_path):
    # Heatmap cell render must escape every interpolated field.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    cell_block = js.split("function workloadCell", 1)[1].split("\nfunction workloadRow", 1)[0]
    for field in ["band", "count", "cell.period", "rowId"]:
        assert f"escapeHtml({field}" in cell_block


def test_ui_console_workload_heatmap_intensity_uses_tokens_not_raw_rgba(tmp_path):
    # (TASK-AR-337 tokenization guard) Heatmap intensity must be opacity over a
    # token color; NO raw hex/rgba in any .workload / .heat- / heatmap CSS rule.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    heat_lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".workload", ".heat-", "--heat", "board-team-filter"))
    ]
    assert heat_lines, "expected workload heatmap CSS rules to exist"
    for line in heat_lines:
        assert not hex_pattern.search(line), f"raw hex in heatmap CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in heatmap CSS: {line.strip()}"

    # The heat tokens are declared in BOTH theme blocks.
    assert "--heat-base:" in _root_token_block(css)
    assert "--heat-base:" in _dark_theme_block(css)
    # Intensity is applied ONLY as opacity via --cell-intensity (no raw rgba in JS).
    assert "--cell-intensity" in js
    assert "opacity: var(--cell-intensity" in css
    # The fill consumes a single token color, not a per-cell computed color.
    assert "background: var(--heat-base)" in css
    # JS must not inject raw rgba(...) for intensity.
    assert "rgba(" not in js.split("function workloadCell", 1)[1].split("\nfunction workloadRow", 1)[0]


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


# ----- TASK-AR-327: Channels view (agent conversation + meeting/seminar) -----


def test_ui_console_channels_view_registered_in_comms_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # New Channels view lives in the COMMS group with a data-view + data-route.
    assert 'data-view="channels"' in html
    assert 'data-route="comms/channels"' in html
    # And a dedicated view container (not the old horizontal tabs / list view).
    assert 'id="view-channels"' in html
    assert 'id="channels-list"' in html
    assert 'id="channels-threads"' in html
    # Owner directive input box + slash-command affordance.
    assert 'id="channels-input-form"' in html
    assert 'id="channels-input-box"' in html
    assert "/meeting" in html and "/seminar" in html


def test_ui_console_channels_role_colors_use_tokens_via_var(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Role colors are applied as var(--token); no raw hex injected from JS.
    assert "function channelRoleColorVar" in js
    assert "var(--${safe" in js
    # Avatar + sender consume the --role-color custom property in the stylesheet.
    assert ".channel-avatar" in css
    assert "var(--role-color, var(--primary))" in css
    assert "--role-color:" in js  # inline binding to the semantic token


def test_ui_console_channels_slash_command_parsing(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    # The parser recognises /meeting and /seminar and maps them to the
    # meeting.start / seminar.start command types (proposal-only).
    assert "function parseChannelInput" in js
    assert "meeting.start" in js
    assert "seminar.start" in js
    assert "/(meeting|seminar)" in js
    # @role mention extraction for participants.
    assert "@[\\w.-]+" in js
    # A plain directive falls back to runtime.call_agent.
    assert "runtime.call_agent" in js
    # The channel form is wired to the command API.
    assert 'channels-input-form' in js
    assert "renderChannels" in js


def test_ui_console_channels_messages_escape_html(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    # Every rendered message/sender/avatar field passes through escapeHtml (XSS).
    assert "function channelMessageTemplate" in js
    assert "escapeHtml(message.body" in js
    assert "escapeHtml(message.from" in js
    assert "escapeHtml(message.avatar" in js
    assert "function channelThreadTemplate" in js
    assert "escapeHtml(thread.title" in js


def test_ui_console_channels_input_wraps_command_for_sendjson(tmp_path):
    # Regression (W4b): sendJson transmits options.payload as the HTTP body, so
    # the channels submit handler MUST wrap the full command under `payload`
    # (matching every other /api/commands caller). Passing parsed.command
    # directly would drop the top-level `type` and the server would reject it.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert 'sendJson("/api/commands", parsed.command)' not in js
    assert 'sendJson("/api/commands", { type: parsed.command.type, payload: parsed.command })' in js


def _send_json_body(call_payload):
    """Mirror the JS sendJson contract: the HTTP body is `options.payload`."""
    return json.dumps(call_payload["payload"]).encode("utf-8")


def test_ui_console_channels_meeting_command_reaches_server_end_to_end(tmp_path):
    # End-to-end through the exact body shape the channels form sends. The fixed
    # call site wraps the full command, so submit_command sees a top-level type
    # and records a proposal-only meeting request -> HTTP 202.
    parsed_command = {
        "type": "meeting.start",
        "payload": {
            "actor": "owner",
            "topic": "Release readiness sync",
            "participants": ["lead-engineer", "qa"],
            "channel": "general",
            "rounds": 3,
        },
    }
    call_payload = {"type": parsed_command["type"], "payload": parsed_command}

    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=_send_json_body(call_payload),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert payload["type"] == "meeting.start"
    assert payload["result"]["mutation_boundary"] == "proposal_only"
    # Proposal written, reviews/ left untouched (console never writes it).
    assert list((tmp_path / ".ui_outbox" / "meetings").glob("MEETREQ-*.json"))
    assert not (tmp_path / "reviews").exists()


def test_ui_console_channels_directive_reaches_server_end_to_end(tmp_path):
    _write_task(tmp_path, "TASK-UI-950")
    # Plain directive -> runtime.call_agent, wrapped the same way.
    parsed_command = {
        "type": "runtime.call_agent",
        "target": "qa",
        "payload": {
            "actor": "owner",
            "instruction": "Please look at TASK-UI-950.",
            "reason": "Owner directive in #general",
            "channel": "general",
        },
    }
    call_payload = {"type": parsed_command["type"], "payload": parsed_command}

    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=_send_json_body(call_payload),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert payload["type"] == "runtime.call_agent"


def test_ui_console_channels_unwrapped_command_would_be_rejected(tmp_path):
    # Documents the W4b failure mode: if the inner payload (no top-level type) is
    # sent as the body, the server rejects it. This is what the old buggy call
    # site produced.
    inner_payload = {
        "actor": "owner",
        "topic": "Release readiness sync",
        "participants": ["lead-engineer", "qa"],
        "rounds": 3,
    }
    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(inner_payload).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))
    assert response.status == 400
    assert payload["status"] == "failed"


# ----- TASK-AR-330: timeline (Gantt) + dependency graph views -----

def test_ui_console_timeline_view_registered_in_work_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # New WORK-group sidebar link + hash route + view container (no horizontal tabs).
    assert 'data-view="timeline"' in html
    assert 'data-route="work/timeline"' in html
    assert 'id="view-timeline"' in html
    assert ">Timeline<" in html
    # Timeline render hosts: grid for bars + cycle warning host.
    assert 'id="timeline-grid"' in html
    assert 'id="timeline-cycle-warning"' in html


def test_ui_console_dependency_graph_view_registered_in_work_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    assert 'data-view="deps"' in html
    assert 'data-route="work/dependencies"' in html
    assert 'id="view-deps"' in html
    assert ">Dependencies<" in html
    assert 'id="dep-graph-svg"' in html
    assert 'id="dep-cycle-warning"' in html


def test_ui_console_timeline_and_dependency_js_render_bars_arrows_and_cycle(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    # Render functions exist and are wired into the periodic render loop.
    assert "function renderTimeline(" in js
    assert "function renderDependencyGraph(" in js
    assert "renderTimeline();" in js
    assert "renderDependencyGraph();" in js
    # Timeline draws bars + dependency arrows; both share the cycle warning path.
    assert "timeline-bar" in js
    assert "timeline-arrow" in js
    assert "function renderCycleWarning(" in js
    assert "Dependency cycle detected" in js
    # Dependency graph reuses the SVG node/edge primitives (like the live map).
    assert "dep-edge" in js
    assert "dep-node" in js
    # Dynamic fields are escaped.
    assert "escapeHtml(bar.id)" in js
    assert "escapeHtml(arrow.from)" in js


def test_ui_console_timeline_and_dependency_css_uses_tokens_not_raw_hex(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    dep_lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".timeline", ".dep-graph", ".dep-edge", ".dep-node", ".dep-cycle-warning"))
    ]
    assert dep_lines, "expected timeline/dependency CSS rules to exist"
    for line in dep_lines:
        assert not hex_pattern.search(line), f"raw hex in dependency CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in dependency CSS: {line.strip()}"
    # Spot-check semantic token consumption.
    assert ".timeline-bar.status-completed { border-color: var(--success-line)" in css
    assert ".dep-edge.is-cycle {" in css
    assert "stroke: var(--danger);" in css


# ----- TASK-AR-329: taskset lifecycle UI (create/rename/archive/move/bulk/undo/templates) -----


def test_ui_console_taskset_lifecycle_surfaces_create_bulk_and_undo(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    # Create form, template buttons, bulk-edit bar, and an undo toast region.
    for marker in [
        "taskset-create-form",
        "taskset-new-name",
        "taskset-template-buttons",
        "taskset-bulk-bar",
        "taskset-bulk-status",
        "taskset-bulk-priority",
        "taskset-bulk-owner",
        "taskset-bulk-move",
        "undo-toast-region",
    ]:
        assert marker in html

    for marker in [
        "submitTasksetCreate",
        "submitTasksetLifecycle",
        "instantiateTasksetTemplate",
        "applyBulkEdit",
        "pushUndoToast",
        "runUndo",
        "toggleBulkTask",
        "taskset.create",
        "taskset.rename",
        "taskset.archive",
        "taskset.template",
        "task.move",
        "task.bulk_edit",
    ]:
        assert marker in js

    for selector in [
        ".taskset-create",
        ".taskset-template-btn",
        ".taskset-bulk-bar",
        ".taskset-task-row",
        ".undo-toast",
    ]:
        assert selector in css


def test_ui_console_taskset_create_post_is_proposal_only(tmp_path):
    # End-to-end: post the exact body the UI sends through build_response and
    # confirm the console emits a proposal but never writes the registry.
    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {"type": "taskset.create", "payload": {"actor": "owner", "display_name": "Console Set", "summary": "from ui"}}
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert payload["result"]["task_set_id"] == "TASKSET-CONSOLE-SET"
    assert payload["result"]["mutation_boundary"] == "proposal_only"
    assert not (tmp_path / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json").exists()
    assert list((tmp_path / ".ui_outbox" / "tasksets").glob("TASKSETREQ-*.json"))


def test_ui_console_bulk_edit_post_applies_and_returns_undo(tmp_path):
    _write_backlog_board_script(tmp_path)
    _write_task(tmp_path, "TASK-AR-960")
    _write_task(tmp_path, "TASK-AR-961")

    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {"type": "task.bulk_edit", "payload": {"task_ids": ["TASK-AR-960", "TASK-AR-961"], "status": "blocked"}}
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "accepted"
    assert payload["result"]["count"] == 2
    assert payload["result"]["undo"]["type"] == "task.bulk_edit"
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))
    statuses = {task["id"]: task["status"] for task in state["tasks"]}
    assert statuses["TASK-AR-960"] == "blocked"
    assert statuses["TASK-AR-961"] == "blocked"


def test_ui_console_task_move_post_changes_taskset(tmp_path):
    _write_backlog_board_script(tmp_path)
    _write_task(tmp_path, "TASK-AR-962")

    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {"type": "task.move", "target": "TASK-AR-962", "payload": {"task_set_id": "TASKSET-AR-OTHER"}}
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "accepted"
    moved = (tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-962-console.md").read_text(encoding="utf-8")
    assert "task_set_id: TASKSET-AR-OTHER" in moved


# ----- TASK-AR-332: file attachments (upload/download/preview + evidence) -----


def _upload(tmp_path, *, filename, content_type, data, task_id=None):
    body = {
        "filename": filename,
        "content_type": content_type,
        "content_b64": base64.b64encode(data).decode("ascii"),
    }
    if task_id:
        body["task_id"] = task_id
    return ui_console.build_response(
        "/api/attachments",
        tmp_path,
        method="POST",
        body=json.dumps(body).encode("utf-8"),
    )


def test_attachment_upload_roundtrip_lists_on_task_and_downloads_bytes(tmp_path):
    _write_task(tmp_path, "TASK-AR-332A")
    png = b"\x89PNG\r\n\x1a\nhello-bytes"

    upload = _upload(tmp_path, filename="shot.png", content_type="image/png", data=png, task_id="TASK-AR-332A")
    created = json.loads(upload.body.decode("utf-8"))
    attachment_id = created["attachment"]["id"]

    # Stored under the attachments dir only.
    blob_rel = created["attachment"]["blob_rel"]
    assert blob_rel.startswith("agents/project/evidence/attachments/")
    assert (tmp_path / blob_rel).read_bytes() == png

    # Listed on task detail (enrich_tasks_with_attachments).
    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))
    task = next(item for item in state["tasks"] if item["id"] == "TASK-AR-332A")
    assert task["attachment_count"] == 1
    assert task["attachments"][0]["filename"] == "shot.png"

    # Download returns the original bytes with the stored content-type.
    download = ui_console.build_response(f"/api/attachments/{attachment_id}/download", tmp_path)

    assert upload.status == 201
    assert created["status"] == "accepted"
    assert download.status == 200
    assert download.body == png
    assert download.content_type == "image/png"


def test_attachment_upload_rejects_path_traversal_filenames(tmp_path):
    base = ui_state.attachments_dir(tmp_path)
    for evil in ["../../../etc/passwd", "..\\..\\windows\\system32\\evil.png", "/abs/secret.png", "C:\\Windows\\x.png"]:
        upload = _upload(tmp_path, filename=evil, content_type="image/png", data=b"\x89PNGdata")
        created = json.loads(upload.body.decode("utf-8"))
        assert upload.status == 201, evil
        blob = (tmp_path / created["attachment"]["blob_rel"]).resolve()
        # The resolved blob never escapes the attachments dir, and the basename
        # carries no separators / parent refs.
        assert base.resolve() in blob.parents, f"escaped for {evil}: {blob}"
        assert ".." not in created["attachment"]["filename"]
        assert "/" not in created["attachment"]["filename"]
        assert "\\" not in created["attachment"]["filename"]
    # Nothing was written outside the attachments dir.
    assert not (tmp_path / "etc" / "passwd").exists()


def test_attachment_upload_enforces_size_and_type_limits(tmp_path):
    too_big = b"x" * (ui_state.ATTACHMENT_MAX_BYTES + 1)
    size_resp = _upload(tmp_path, filename="big.txt", content_type="text/plain", data=too_big)
    size_payload = json.loads(size_resp.body.decode("utf-8"))

    type_resp = _upload(tmp_path, filename="evil.svg", content_type="image/svg+xml", data=b"<svg/>")
    type_payload = json.loads(type_resp.body.decode("utf-8"))

    assert size_resp.status == 400
    assert size_payload["status"] == "failed"
    assert "size limit" in " ".join(size_payload["errors"])
    assert type_resp.status == 400
    assert "unsupported content type" in " ".join(type_payload["errors"])


def test_attachment_upload_creates_evidence_record_and_link(tmp_path):
    _write_task(tmp_path, "TASK-AR-332E")
    _upload(tmp_path, filename="proof.md", content_type="text/markdown", data=b"# closeout\n", task_id="TASK-AR-332E")

    state = json.loads(ui_console.build_response("/api/state", tmp_path).body.decode("utf-8"))
    attach_evidence = [item for item in state["evidence"] if item.get("source_type") == "attachment"]
    assert len(attach_evidence) == 1
    assert attach_evidence[0]["task_id"] == "TASK-AR-332E"
    assert attach_evidence[0]["download_url"].startswith("/api/attachments/")

    # The sidecar record IS the evidence record (markdown sidecar on disk).
    records = list((ui_state.attachments_dir(tmp_path)).glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["task_id"] == "TASK-AR-332E"
    assert record["evidence"].startswith("attachment:")


def test_attachment_link_command_is_proposal_only(tmp_path):
    _write_task(tmp_path, "TASK-AR-332L")
    response = ui_console.build_response(
        "/api/commands",
        tmp_path,
        method="POST",
        body=json.dumps(
            {
                "type": "attachment.link",
                "target": "TASK-AR-332L",
                "payload": {"attachment_id": "att-20260612-abcd"},
            }
        ).encode("utf-8"),
    )
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status == 202
    assert payload["status"] == "queued"
    assert payload["result"]["mutation_boundary"] == "proposal_only"
    proposals = list((tmp_path / ".ui_outbox" / "attachments").glob("ATTACHREQ-*.json"))
    assert len(proposals) == 1


def test_attachment_filename_rendering_is_xss_safe(tmp_path):
    _write_task(tmp_path, "TASK-AR-332X")
    upload = _upload(
        tmp_path,
        filename='<img src=x onerror=alert(1)>.png',
        content_type="image/png",
        data=b"\x89PNGdata",
        task_id="TASK-AR-332X",
    )
    created = json.loads(upload.body.decode("utf-8"))
    # The stored filename is normalized to a safe charset (angle brackets and
    # the script payload stripped), so no markup survives to the DOM.
    stored = created["attachment"]["filename"]
    assert "<" not in stored
    assert ">" not in stored
    assert "onerror" not in stored or "=" not in stored
    # The JS renderer escapes every filename it prints.
    assert "escapeHtml(item.filename" in ui_console.JS


def test_attachment_download_unknown_id_returns_404(tmp_path):
    bad = ui_console.build_response("/api/attachments/not-a-real-id/download", tmp_path)
    traversal = ui_console.build_response("/api/attachments/..%2f..%2fsecret/download", tmp_path)
    assert bad.status == 404
    assert traversal.status == 404


def test_attachment_css_uses_tokens_not_raw_hex(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    # Pull just the attachment block and assert no raw hex/rgba leaked in.
    start = css.index(".attachments {")
    end = css.index("@media (max-width: 1200px)", start)
    block = css[start:end]
    assert "var(--" in block
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", block)
    assert not re.search(r"rgba?\(", block)


# --------------------------------------------------------------------------- #
# Import/Export console routes (TASK-AR-333)
# --------------------------------------------------------------------------- #
def test_ui_console_registers_import_export_view_in_ops_group(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # Sidebar link registered in the OPS group.
    ops_start = html.index('data-group="ops"')
    ops_block = html[ops_start : html.index("</div>", ops_start) + 6]
    assert 'data-view="portability"' in ops_block
    assert "Import/Export" in ops_block
    # View container exists with the export anchors + import form.
    assert 'id="view-portability"' in html
    assert 'href="/api/export/board.csv"' in html
    assert 'href="/api/export/backup.zip"' in html
    assert 'id="import-form"' in html


def test_ui_console_export_board_csv_route(tmp_path):
    _write_task(tmp_path, "TASK-AR-963")
    response = ui_console.build_response("/api/export/board.csv", tmp_path)
    assert response.status == 200
    assert response.content_type == "text/csv; charset=utf-8"
    body = response.body.decode("utf-8")
    assert body.splitlines()[0].startswith("id,display_id,title,")
    assert "TASK-AR-963" in body


def test_ui_console_export_taskset_md_route(tmp_path):
    _write_task(tmp_path, "TASK-AR-964")
    response = ui_console.build_response("/api/export/taskset.md", tmp_path)
    assert response.status == 200
    assert response.content_type == "text/markdown; charset=utf-8"
    assert response.body.decode("utf-8").startswith("# Taskset Export Package")


def test_ui_console_export_status_json_route(tmp_path):
    _write_task(tmp_path, "TASK-AR-965")
    response = ui_console.build_response("/api/export/status.json", tmp_path)
    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "status_snapshot"
    assert payload["totals"]["tasks"] == 1


def test_ui_console_export_backup_zip_route(tmp_path):
    import io
    import zipfile

    _write_task(tmp_path, "TASK-AR-966")
    response = ui_console.build_response("/api/export/backup.zip", tmp_path)
    assert response.status == 200
    assert response.content_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        assert "manifest.json" in archive.namelist()
        assert "board.csv" in archive.namelist()


def test_ui_console_export_unknown_format_404(tmp_path):
    response = ui_console.build_response("/api/export/bogus.xml", tmp_path)
    assert response.status == 404


def test_ui_console_import_preview_route_detects_duplicates(tmp_path):
    _write_task(tmp_path, "TASK-AR-967")
    body = json.dumps(
        {
            "format": "csv",
            "content": "id,title,status,priority\r\nTASK-AR-967,Existing,in_progress,P0\r\nTASK-AR-968,Fresh,planned,P1\r\n",
        }
    ).encode("utf-8")
    response = ui_console.build_response("/api/import/preview", tmp_path, method="POST", body=body)
    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "import_preview"
    assert payload["counts"]["total"] == 2
    assert payload["counts"]["duplicate"] == 1
    assert payload["counts"]["new"] == 1


def test_ui_console_import_commit_creates_task_create_proposals_not_direct_writes(tmp_path):
    _write_backlog_board_script(tmp_path)
    body = json.dumps(
        {
            "format": "csv",
            "content": "id,title,status,priority\r\nTASK-AR-969,Imported task,planned,P1\r\n",
        }
    ).encode("utf-8")
    response = ui_console.build_response("/api/import/commit", tmp_path, method="POST", body=body)
    assert response.status == 202
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "import_commit"
    assert payload["counts"]["created"] == 1
    # A task.create command proposal was recorded in the outbox (the only writer).
    outbox = list((tmp_path / ".ui_outbox").glob("COMMAND-*.json"))
    assert outbox, "expected a task.create command proposal in .ui_outbox"
    record = json.loads(outbox[0].read_text(encoding="utf-8"))
    assert record["type"] == "task.create"
    assert record["status"] == "accepted"


def test_ui_console_import_commit_skips_duplicate(tmp_path):
    _write_backlog_board_script(tmp_path)
    _write_task(tmp_path, "TASK-AR-970")
    body = json.dumps(
        {
            "format": "csv",
            "content": "id,title,status,priority\r\nTASK-AR-970,Existing,in_progress,P0\r\n",
        }
    ).encode("utf-8")
    response = ui_console.build_response("/api/import/commit", tmp_path, method="POST", body=body)
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["counts"]["created"] == 0
    assert payload["counts"]["skipped"] == 1


def test_ui_console_import_preview_rejects_unknown_format(tmp_path):
    body = json.dumps({"format": "xml", "content": "<x/>"}).encode("utf-8")
    response = ui_console.build_response("/api/import/preview", tmp_path, method="POST", body=body)
    assert response.status == 400


def test_ui_console_csv_round_trip_through_console_no_loss(tmp_path):
    # Acceptance: export a board to CSV, then re-import it; the round-trip is
    # lossless (every exported row maps back to a candidate with the same
    # fields and is correctly detected as an existing duplicate).
    _write_backlog_board_script(tmp_path)
    _write_task(tmp_path, "TASK-AR-971")
    _write_task(tmp_path, "TASK-AR-972")

    exported = ui_console.build_response("/api/export/board.csv", tmp_path).body.decode("utf-8")
    body = json.dumps({"format": "csv", "content": exported}).encode("utf-8")
    preview = json.loads(
        ui_console.build_response("/api/import/preview", tmp_path, method="POST", body=body).body.decode("utf-8")
    )
    assert preview["counts"]["total"] == 2
    assert preview["counts"]["duplicate"] == 2
    assert preview["counts"]["new"] == 0


def test_ui_console_portability_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-333 tokenization guard) Every color the portability CSS
    # introduces must flow through var(--token); no raw hex/rgba.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    portability_lines = [
        line
        for line in body_css.splitlines()
        if ".portability" in line or line.strip().startswith("#import-")
    ]
    assert portability_lines, "expected portability CSS rules to exist"
    for line in portability_lines:
        assert not hex_pattern.search(line), f"raw hex in portability CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in portability CSS: {line.strip()}"


# ---------------------------------------------------------------------------
# Global search + quick open (TASK-AR-334)
# ---------------------------------------------------------------------------


def _seed_console_search_corpus(root: Path) -> None:
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-334.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-334",
                "title: Global search and quick open",
                "status: blocked",
                "owner: lead-engineer",
                "task_set_id: TASKSET-AR-SEARCH",
                "updated_at: 2026-06-12T10:00:00+09:00",
                "---",
                "",
                "## Goal",
                "",
                "Full-text search across entities.",
                "",
            ]
        ),
    )
    _write(
        root / "agents" / "runtime" / "events" / "qa.jsonl",
        json.dumps({"ts": "2026-06-12T11:00:00+09:00", "role": "qa", "event": "search.indexed", "task_id": "TASK-AR-334", "evidence": ["reviews/search-evidence.md"]}) + "\n",
    )
    _write(
        root / "agents" / "messages" / "inbox" / "MSG-search.md",
        "\n".join(["---", "id: MSG-search", "from: qa", "to: lead", "type: review", "status: queued", "ts: 2026-06-12T11:05:00+09:00", "intent: search", "task_id: TASK-AR-334", "---", "", "search body", ""]),
    )
    _write(
        root / "reviews" / "MEETING-search.md",
        "\n".join(["---", "type: meeting", "id: MEETING-search", "title: Search review", "status: pass", "---", "", "# Search Review", "", "search design"]),
    )


def test_ui_console_search_route_returns_five_plus_entity_types(tmp_path):
    _seed_console_search_corpus(tmp_path)
    response = ui_console.build_response("/api/search?q=search", tmp_path)
    assert response.status == 200
    payload = json.loads(response.body)
    assert payload["resource"] == "search"
    assert payload["query"] == "search"
    types = {item["entity_type"] for item in payload["items"]}
    assert len(types) >= 5, f"expected >=5 entity types, got {types}"
    # Each result deep-links via an AR-321 hash route (data-view / data-route).
    for item in payload["items"]:
        assert item["deep_link"].startswith("#/")
    # Empty query -> no items but still a well-formed envelope.
    empty = json.loads(ui_console.build_response("/api/search", tmp_path).body)
    assert empty["items"] == [] and empty["total"] == 0


def test_ui_console_search_route_parses_operators(tmp_path):
    _seed_console_search_corpus(tmp_path)
    payload = json.loads(
        ui_console.build_response("/api/search?q=type%3Atask%20status%3Ablocked%20search", tmp_path).body
    )
    assert payload["operators"] == {"type": "task", "status": "blocked"}
    assert payload["terms"] == ["search"]
    assert payload["items"] and all(item["entity_type"] == "task" for item in payload["items"])


def test_ui_console_search_route_query_is_xss_safe_in_echo(tmp_path):
    _seed_console_search_corpus(tmp_path)
    # The API echoes the raw query (JSON, so inert), and the JS escapeHtml's it
    # before rendering. Here we assert the API does not crash on hostile input
    # and the JS guards the echo with escapeHtml.
    hostile = "<script>alert(1)</script>"
    from urllib.parse import quote

    payload = json.loads(ui_console.build_response(f"/api/search?q={quote(hostile)}", tmp_path).body)
    assert payload["query"] == hostile  # raw in JSON (not HTML), inert
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # The "no matches" echo path runs the user query through escapeHtml.
    assert "No matches for" in js
    assert "escapeHtml(query)" in js


def test_ui_console_search_box_and_quick_open_anchors_served(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Topbar search box + results dropdown.
    assert 'id="global-search-input"' in html
    assert 'id="global-search-results"' in html
    # Ctrl+P quick-open overlay (distinct element from the Ctrl+K palette).
    assert 'id="quick-open"' in html
    assert 'id="quick-open-input"' in html
    assert 'id="command-palette"' in html  # palette still present, separate.
    # JS wiring exists for fetch + deep-link selection.
    assert "/api/search?q=" in js
    assert "selectEntityFromHash" in js
    assert "data-deep-link" in js


def test_ui_console_quick_open_ctrl_p_gated_and_distinct_from_ctrl_k(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Ctrl+K opens the command palette; Ctrl+P opens quick-open — two handlers.
    assert 'event.key === "k" || event.key === "K"' in js
    assert 'event.key === "p" || event.key === "P"' in js
    assert "openCommandPalette" in js
    assert "openQuickOpen" in js
    # Both require a modifier so a plain "p" never hijacks typing; the shared
    # text-input guard helper must be DEFINED and actually INVOKED (not dead
    # code) so single-key (j/k) nav cannot fire while typing in a field.
    assert "function eventTargetIsTextInput(event)" in js
    nav_fn = js.split("function handleListKeyboardNav(event)", 1)[1].split("\n}", 1)[0]
    assert "eventTargetIsTextInput(event)" in nav_fn, "text-input guard must be wired into list keyboard nav"
    assert "isContentEditable" in js  # guard also covers contentEditable targets
    # The two overlays are coordinated: opening one closes the other.
    assert "closeQuickOpen" in js
    assert "closeCommandPalette" in js


def test_ui_console_search_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-334 tokenization guard) Search + quick-open CSS introduces no raw
    # hex/rgba; every color flows through var(--token).
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    search_lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".global-search", ".search-result", ".search-empty", ".quick-open", ".topbar-search", ".is-deeplinked"))
    ]
    assert search_lines, "expected search/quick-open CSS rules to exist"
    for line in search_lines:
        assert not hex_pattern.search(line), f"raw hex in search CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in search CSS: {line.strip()}"
    # Consumes existing semantic tokens.
    assert "background: var(--primary-soft-strong)" in css
    assert "outline: 2px solid var(--primary)" in css


# ----- TASK-AR-336: interactive state-machine viewer -----


def _write_state_machines(root: Path) -> None:
    _write(
        root / "agents" / "project" / "STATE-MACHINES.yml",
        "\n".join(
            [
                "schema: agent-runtime-state-machines/v1",
                "machines:",
                "  - id: task",
                "    scope: backlog_task",
                "    initial: planned",
                "    states:",
                "      - id: planned",
                "        signal: watch",
                "        score: 70",
                "      - id: in_progress",
                "        signal: watch",
                "        score: 80",
                "      - id: completed",
                "        signal: pass",
                "        score: 95",
                "    transitions:",
                "      - from: planned",
                "        to: in_progress",
                "        trigger: agent_claimed",
                "      - from: in_progress",
                "        to: completed",
                "        trigger: done_criteria_met",
            ]
        ),
    )


def test_ui_console_state_machine_view_registered_in_records_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # New State Machines view lives in the RECORDS group with view + route.
    assert 'data-view="statemachines"' in html
    assert 'data-route="records/state-machines"' in html
    # Dedicated view container + interactive graph stage + selectors.
    assert 'id="view-statemachines"' in html
    assert 'id="state-machine-svg"' in html
    assert 'id="state-machine-select"' in html
    assert 'id="state-machine-task-select"' in html
    assert 'id="state-machine-legend"' in html


def test_ui_console_state_machine_resource_route_serves_graph(tmp_path):
    _write_state_machines(tmp_path)
    _write_task(tmp_path, "TASK-AR-336")
    machines = json.loads(ui_console.build_response("/api/state-machines", tmp_path).body.decode("utf-8"))
    assert machines["resource"] == "state_machines"
    task = next(item for item in machines["items"] if item["id"] == "task")
    # Every machine renders nodes + edges (acceptance criterion).
    assert task["state_nodes"], "task machine should render state nodes"
    assert task["transition_edges"], "task machine should render transition edges"
    # An arbitrary task's current state is identifiable in the graph.
    assert "TASK-AR-336" in task["task_states"]
    info = task["task_states"]["TASK-AR-336"]
    assert info["current_state"] in {node["id"] for node in task["state_nodes"]}


def test_ui_console_state_machine_deep_link_from_task_detail(tmp_path):
    # The task detail panel exposes a "view in state machine" affordance that
    # routes into the viewer with the task highlighted (read-only deep link).
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # The button + handler are rendered into the task detail panel by JS.
    assert 'id="view-state-machine"' in js
    assert "function viewTaskInStateMachine" in js
    assert "viewTaskInStateMachine(task.id)" in js
    # The deep link selects the task machine and activates the viewer view.
    assert 'selectedStateMachineId = "task"' in js
    assert 'activateView("statemachines")' in js


def test_ui_console_state_machine_render_escapes_labels_and_renders(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function renderStateMachineViewer" in js
    # The render path is wired into renderAll so it refreshes with the state.
    assert "renderStateMachineViewer();" in js
    # State / transition labels are escaped before injection into the DOM.
    assert "escapeHtml(machine.id)" in js
    # Traversed-path + current-state highlighting consumes the derived fields.
    assert "transition_path" in js
    assert "current_state" in js
    assert "is-traversed" in js
    assert "is-current" in js


def test_ui_console_state_machine_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-336 tokenization guard) Every color the state-machine CSS
    # introduces must flow through var(--token); no raw hex/rgba outside the
    # token blocks.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    sm_lines = [
        line for line in body_css.splitlines()
        if ".state-machine" in line or "--sm-" in line
    ]
    assert sm_lines, "expected state-machine CSS rules to exist"
    for line in sm_lines:
        assert not hex_pattern.search(line), f"raw hex in state-machine CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in state-machine CSS: {line.strip()}"
    # The new highlight tokens are defined in BOTH theme blocks.
    assert "--sm-current:" in _root_token_block(css)
    assert "--sm-current:" in _dark_theme_block(css)
    assert "--sm-path:" in _root_token_block(css)
    assert "--sm-path:" in _dark_theme_block(css)


def test_ui_console_state_machine_app_js_ascii_only_and_node_check(tmp_path):
    # The state-machine JS must be ASCII-only (cp949 node-check guard) and the
    # generated bundle must remain syntactically valid JavaScript.
    import shutil
    import subprocess

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Isolate the new render function and assert it carries no non-ASCII bytes.
    start = js.index("function renderStateMachineViewer")
    end = js.index("function renderRoadmapTimeline", start)
    sm_block = js[start:end]
    non_ascii = [ch for ch in sm_block if ord(ch) > 127]
    assert not non_ascii, f"state-machine JS must be ASCII-only, found: {non_ascii[:5]}"

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_ui_console_state_machine_graceful_when_yaml_missing(tmp_path):
    # No STATE-MACHINES.yml -> the route still serves a well-formed empty graph.
    machines = json.loads(ui_console.build_response("/api/state-machines", tmp_path).body.decode("utf-8"))
    assert machines["resource"] == "state_machines"
    assert machines["items"] == []
    # The shell still serves the view container so the UI degrades gracefully.
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    assert 'id="view-statemachines"' in html


# ----- TASK-AR-339: ops dashboard view + tokenized charts -----


def test_ui_console_ops_dashboard_view_registered_in_ops_group(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # Sidebar link in the OPS group + hash route + view container, reusing the
    # established data-view/data-route/view-* convention.
    assert 'data-view="dashboard"' in html
    assert 'data-route="ops/dashboard"' in html
    assert 'id="view-dashboard"' in html
    # The four metric widgets each have a mount point.
    for mount in ["opsdash-tokens", "opsdash-eval", "opsdash-gates", "opsdash-burndown", "opsdash-velocity"]:
        assert f'id="{mount}"' in html


def test_ui_console_ops_dashboard_render_wired(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function renderOpsDashboard" in js
    assert "renderOpsDashboard();" in js  # called from renderAll
    assert "runtimeState && runtimeState.ops_metrics" in js


def test_ui_console_ops_dashboard_css_uses_tokens_not_raw_color(tmp_path):
    # Tokenization guard: every color in the ops-dashboard CSS (bars, gate
    # pass/watch/block pills, chart strokes, velocity bars) flows through
    # var(--token); no raw hex/rgba outside the token blocks.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    ops_lines = [line for line in body_css.splitlines() if ".opsdash" in line]
    assert ops_lines, "expected ops-dashboard CSS rules to exist"
    for line in ops_lines:
        assert not hex_pattern.search(line), f"raw hex in ops-dashboard CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in ops-dashboard CSS: {line.strip()}"
    # Gate pass/watch/block map onto the semantic success/warning/danger tokens.
    assert ".opsdash-gate-count.is-pass" in css and "var(--success" in css
    assert ".opsdash-gate-count.is-watch" in css and "var(--warning" in css
    assert ".opsdash-gate-count.is-block" in css and "var(--danger" in css
    # Chart lines/dots stroke/fill via tokens.
    assert "stroke: var(--primary)" in css
    assert "fill: var(--primary)" in css


def test_ui_console_ops_dashboard_charts_tokenized_no_raw_color_in_js(tmp_path):
    # The inline-SVG chart builders must NOT inject literal colors from JS; color
    # comes only from token-backed CSS classes (opsdash-line / opsdash-dot etc.).
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("TASK-AR-339: ops dashboard")
    end = js.index("TASK-AR-332: file attachments", start)
    block = js[start:end]
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    assert not hex_pattern.search(block), "raw hex literal in ops-dashboard JS"
    assert not rgba_pattern.search(block), "raw rgba literal in ops-dashboard JS"
    # SVG charts reference the token-styled classes only.
    assert 'class="opsdash-line"' in block
    assert 'class="opsdash-dot' in block


def test_ui_console_ops_dashboard_app_js_ascii_only_and_node_check(tmp_path):
    import shutil
    import subprocess

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("TASK-AR-339: ops dashboard")
    end = js.index("TASK-AR-332: file attachments", start)
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"ops-dashboard JS must be ASCII-only, found: {non_ascii[:5]}"
    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


# ----- TASK-AR-338: notification center + @mentions + daily brief -----


def test_ui_console_inbox_view_registered_in_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # Inbox view container + sidebar link with a hash route in the COMMS group.
    assert 'id="view-inbox"' in html
    assert 'data-view="inbox"' in html
    assert 'data-route="comms/inbox"' in html
    # Daily-brief card + subscription forms live inside the inbox view.
    assert 'id="daily-brief-body"' in html
    assert 'id="inbox-subscribe-form"' in html
    assert 'id="inbox-list"' in html


def test_ui_console_inbox_and_daily_brief_resources(tmp_path):
    for path, resource in [
        ("/api/notifications", "notifications"),
        ("/api/daily_brief", "daily_brief"),
        ("/api/daily-brief", "daily_brief"),
    ]:
        payload = json.loads(ui_console.build_response(path, tmp_path).body.decode("utf-8"))
        assert payload["resource"] == resource


def test_ui_console_inbox_css_uses_tokens_not_raw_color(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    # Pull only the inbox/daily-brief rules (after the AR-338 marker) so we test
    # the new CSS independent of the global token-block guard.
    marker = "/* ===== TASK-AR-338: notification center + daily brief ===== */"
    assert marker in css
    inbox_css = css[css.index(marker):css.index(".triage-summary", css.index(marker))]
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in inbox_css.splitlines():
        assert not hex_pattern.search(line), f"raw hex in inbox CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in inbox CSS: {line.strip()}"
    # Severity colors map to the existing status tokens.
    assert "var(--danger)" in inbox_css
    assert "var(--warning)" in inbox_css
    assert "var(--primary)" in inbox_css


def test_ui_console_inbox_app_js_ascii_only_and_node_check(tmp_path):
    import shutil
    import subprocess

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("function renderInbox")
    end = js.index("// Parse the owner input box")
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"inbox JS must be ASCII-only, found: {non_ascii[:5]}"
    assert "function renderDailyBrief" in block
    assert "markNotificationRead" in block

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_ui_console_ops_dashboard_escapes_rendered_fields(tmp_path):
    # The render helpers must escapeHtml every field they emit (taskset names,
    # gate ids/refs, status). Spot-check that the helpers wrap fields in escapeHtml.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("function renderOpsGateBoard")
    block = js[start:js.index("function renderOpsBurndown", start)]
    # task_ref, id, kind, status are all escaped.
    assert "escapeHtml(gate.task_ref)" in block
    assert "escapeHtml(gate.id)" in block
    assert "escapeHtml(gate.status)" in block


def test_ui_console_inbox_notification_fields_are_escaped(tmp_path):
    # A blocked task with markup in its reason flows into a notification body;
    # the rendered shell must not inline that markup unescaped.
    (tmp_path / "agents" / "lead_engineer" / "tasks").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-950-x.md").write_text(
        "\n".join(
            [
                "---",
                "id: TASK-AR-950",
                "status: blocked",
                "owner: lead-engineer",
                "priority: P0",
                "blocked_reason: <script>alert(1)</script>",
                "created: 2026-06-14",
                "---",
                "",
                "## Goal",
                "",
                "x",
                "",
            ]
        ),
        encoding="utf-8",
    )
    payload = json.loads(ui_console.build_response("/api/notifications", tmp_path).body.decode("utf-8"))
    bodies = [item["body"] for item in payload["items"]["notifications"]]
    assert any("<script>alert(1)</script>" in body for body in bodies)
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    assert "<script>alert(1)</script>" not in html


# ----- TASK-AR-364: 2D office map view -----


def _write_office_instance(root: Path, instance_id: str, *, role: str, team_id: str = "agent-runtime-core") -> None:
    record = {
        "schema": "agent-runtime-agent-instance/v1",
        "agent_instance_id": instance_id,
        "callsign": f"claude/{instance_id}",
        "display_name": f"claude/{instance_id}",
        "role": role,
        "team_id": team_id,
        "model": "claude-opus",
        "spawned_at": "2026-06-14T10:00:00+09:00",
    }
    _write(root / "agents" / "runtime" / "instances" / f"{instance_id}.json", json.dumps(record))


def _write_office_claim(root: Path, claim_id: str, instance_id: str, *, status: str, mode: str | None = None) -> None:
    record = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": "TASK-AR-950",
        "agent_instance_id": instance_id,
        "status": status,
        "claimed_at": "2026-06-14T10:30:00+09:00",
        "last_heartbeat": "2026-06-14T10:40:00+09:00",
    }
    if mode is not None:
        record["mode"] = mode
    _write(root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json", json.dumps(record))


def test_ui_console_office_map_view_registered_in_agents_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")

    # New Office Map view lives in the AGENTS group with a data-view + data-route.
    assert 'data-view="office"' in html
    assert 'data-route="agents/office"' in html
    # And a dedicated view container with the floor-plan grid + legend anchors.
    assert 'id="view-office"' in html
    assert 'id="office-map-grid"' in html
    assert 'id="office-map-summary"' in html
    assert 'id="office-map-legend"' in html


def test_ui_console_office_map_route_serves_world_areas_and_agents(tmp_path):
    _write_office_instance(tmp_path, "inst-le", role="lead-engineer")
    _write_office_claim(tmp_path, "CLAIM-le", "inst-le", status="in_progress")

    underscore = ui_console.build_response("/api/office_map", tmp_path)
    hyphen = ui_console.build_response("/api/office-map", tmp_path)
    assert underscore.status == 200 and hyphen.status == 200
    payload = json.loads(underscore.body.decode("utf-8"))
    assert payload["resource"] == "office_map"
    office = payload["items"]
    assert office["schema"] == "agent-runtime-office-map/v1"
    # World -> areas tree (rooms per team) and a placed agent in the dev room.
    assert office["world"]["areas"] == ["planning", "dev", "qa", "release", "meeting"]
    placed = {agent["role"]: agent["room_id"] for agent in office["agents"]}
    assert placed["lead-engineer"] == "dev"


def test_ui_console_office_map_render_function_is_ascii_only_and_node_check(tmp_path):
    # The office-map JS must be ASCII-only (cp949 node-check guard) -- emoji are
    # served from the Python payload (agent.glyph / action_glyphs), never inlined.
    import shutil
    import subprocess

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function renderOfficeMap(" in js
    assert "renderOfficeMap()" in js  # wired into renderAll
    start = js.index("function renderOfficeMap")
    end = js.index("function renderStateMachineViewer", start)
    office_block = js[start:end]
    non_ascii = [ch for ch in office_block if ord(ch) > 127]
    assert not non_ascii, f"office-map JS must be ASCII-only, found: {non_ascii[:5]}"
    # The glyph is rendered from server data, not a literal emoji in the JS.
    assert "agent.glyph" in office_block

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_ui_console_office_map_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-364 tokenization guard) Every color the office-map CSS introduces
    # must flow through var(--token); no raw hex/rgba outside the token blocks.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    office_lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".office-map", ".office-room", ".office-agent"))
    ]
    assert office_lines, "expected office-map CSS rules to exist"
    for line in office_lines:
        assert not hex_pattern.search(line), f"raw hex in office-map CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in office-map CSS: {line.strip()}"

    # The new office tokens are defined in BOTH theme blocks.
    assert "--office-room-bg:" in _root_token_block(css)
    assert "--office-room-bg:" in _dark_theme_block(css)
    # Rooms consume semantic accent tokens (no per-room raw color).
    assert ".office-room.token-blue { border-top-color: var(--blue); }" in css


def test_ui_console_office_map_in_meeting_agents_render_in_meeting_room(tmp_path):
    # TASK-AR-361 integration through the route: a meeting-mode claim relocates
    # the agent to the meeting room and carries the meeting glyph.
    _write_office_instance(tmp_path, "inst-le", role="lead-engineer")
    _write_office_claim(tmp_path, "CLAIM-meet", "inst-le", status="in_progress", mode="meeting")

    payload = json.loads(ui_console.build_response("/api/office_map", tmp_path).body.decode("utf-8"))
    office = payload["items"]
    le = next(agent for agent in office["agents"] if agent["role"] == "lead-engineer")
    assert le["room_id"] == "meeting"
    assert le["action"] == "meeting"
    assert office["totals"]["in_meeting"] == 1


def test_ui_console_office_map_graceful_when_no_agents(tmp_path):
    # No instances -> the route still serves the static rooms with zero agents,
    # and the shell renders the view container.
    payload = json.loads(ui_console.build_response("/api/office_map", tmp_path).body.decode("utf-8"))
    office = payload["items"]
    assert office["agents"] == []
    assert {room["id"] for room in office["rooms"]} == {"planning", "dev", "qa", "release", "meeting"}
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    assert 'id="view-office"' in html


# --- Growth system view (TASK-AR-363) ---------------------------------------


def test_ui_console_growth_view_registered_in_agents_sidebar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # New Growth view lives in the AGENTS group with a data-view + data-route.
    assert 'data-view="growth"' in html
    assert 'data-route="agents/growth"' in html
    for host_id in [
        "view-growth",
        "growth-hero",
        "growth-formula",
        "growth-efficiency",
        "growth-teams",
        "growth-agents",
        "growth-enabled-toggle",
        "growth-disabled",
    ]:
        assert host_id in html


def test_ui_console_growth_api_route_serves_resource(tmp_path):
    response = ui_console.build_response("/api/growth", tmp_path)
    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["resource"] == "growth"
    assert payload["items"]["schema"] == "agent-runtime-growth/v1"
    # The XP formula carries no token term (anti-waste) and reports the flag.
    assert payload["items"]["xp_formula"]["token_spend_excluded"] is True
    assert "token" not in str(payload["items"]["xp_formula"]["weights"]).lower()


def test_ui_console_growth_render_markers_and_toggle_wired(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    for marker in [
        "renderGrowth",
        "growthData",
        "growthHero",
        "growthFormula",
        "growthEfficiency",
        "growthAgents",
        "wireGrowthToggle",
        "renderGrowth()",  # wired into renderAll
        "wireGrowthToggle();",  # wired at setup
    ]:
        assert marker in js
    # The toggle gates display on growth.enabled (global toggle, self-contained).
    growth_block = js.split("function renderGrowth", 1)[1].split("function wireGrowthToggle", 1)[0]
    assert "data.enabled" in growth_block


def test_ui_console_growth_fields_are_escaped(tmp_path):
    # Every interpolated growth field must flow through escapeHtml.
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    for fn, fields in [
        ("function growthHero", ["project.level", "project.cumulative_xp", "stage.label_ko"]),
        ("function growthEfficiency", ["stat[0]", "stat[1]"]),
        ("function growthAgents", ["agent.role"]),
    ]:
        block = js.split(fn, 1)[1].split("\nfunction ", 1)[0]
        for field in fields:
            assert f"escapeHtml({field}" in block, f"{field} not escaped in {fn}"


def test_ui_console_growth_css_uses_tokens_not_raw_color(tmp_path):
    # (TASK-AR-363 tokenization guard) Every color the growth CSS introduces must
    # be a var(--token); NO raw hex/rgba in any .growth-* rule.
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    growth_rules = [line for line in body_css.splitlines() if ".growth" in line or "--growth" in line]
    assert growth_rules, "expected growth CSS rules"
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in growth_rules:
        assert not hex_pattern.search(line), f"raw hex in growth CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in growth CSS: {line.strip()}"
    # The new growth tokens are defined in BOTH theme blocks.
    assert "--growth-xp:" in _root_token_block(css)
    assert "--growth-xp:" in _dark_theme_block(css)
    assert "--growth-stage:" in _root_token_block(css)
    assert "--growth-stage:" in _dark_theme_block(css)


def test_ui_console_growth_app_js_ascii_only_and_node_check(tmp_path):
    # The growth JS must be ASCII-only (cp949 node-check guard) and the bundle
    # must remain syntactically valid JavaScript.
    import shutil
    import subprocess

    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("function growthData")
    end = js.index("let workloadScope", start)
    growth_block = js[start:end]
    non_ascii = [ch for ch in growth_block if ord(ch) > 127]
    assert not non_ascii, f"growth JS must be ASCII-only, found: {non_ascii[:5]}"
    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


# ----- TASK-AR-341: workspace switcher + widget extension points + i18n -----


def test_ui_console_workspace_switcher_control_in_topbar(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    # Topbar carries the workspace switcher toggle + menu container.
    assert 'id="workspace-switcher-toggle"' in html
    assert 'id="workspace-switcher-menu"' in html
    assert 'class="workspace-switcher"' in html


def test_ui_console_workspaces_route_lists_current_root_safely(tmp_path):
    response = ui_console.build_response("/api/workspaces", tmp_path)
    payload = json.loads(response.body.decode("utf-8"))
    assert response.status == 200
    assert payload["resource"] == "workspaces"
    items = payload["items"]["items"]
    # The current root is always present and marked current.
    current = [item for item in items if item["current"]]
    assert len(current) == 1
    # Switching is navigation-only: a relaunch command, never an exec/file write.
    assert current[0]["relaunch_command"].startswith("agent-runtime ui-console --root ")
    # Recent-state preview is read-only metadata (no task bodies / commands).
    assert "recent_state" in current[0]


def test_ui_console_workspace_switch_js_is_navigation_not_exec(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function switchWorkspace" in js
    assert "function renderWorkspaces" in js
    # Safe switch: self-reload for current, clipboard-copy of relaunch command for
    # others. It must NOT spawn/exec/eval an arbitrary root.
    assert "window.location.reload()" in js
    assert "navigator.clipboard" in js
    start = js.index("function switchWorkspace")
    end = js.index("function renderWidgetCard", start)
    block = js[start:end]
    for forbidden in ("eval(", "child_process", "exec(", "spawn(", "new Function"):
        assert forbidden not in block, f"workspace switch must not {forbidden}"


def test_ui_console_widget_host_present_on_home(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    assert 'id="home-widgets"' in html
    assert 'id="home-widgets-grid"' in html


def test_ui_console_widgets_route_loads_declarative_definition(tmp_path):
    # A declarative widget dropped as JSON renders with no code, only data.
    _write(
        tmp_path / "agents" / "runtime" / "widgets" / "custom.json",
        json.dumps(
            {
                "id": "team-metric",
                "kind": "metric",
                "title": "Open PRs",
                "value": 7,
                "caption": "needs review",
            }
        ),
    )
    payload = json.loads(ui_console.build_response("/api/widgets", tmp_path).body.decode("utf-8"))
    assert payload["resource"] == "widgets"
    items = payload["items"]["items"]
    ids = {widget["id"] for widget in items}
    assert "team-metric" in ids
    # Built-in samples are also present so the host renders out of the box.
    assert any(widget.get("builtin") for widget in items)


def test_ui_console_widget_render_escapes_html_no_injection(tmp_path):
    # A widget whose fields carry markup must be rendered escaped (no injection).
    _write(
        tmp_path / "agents" / "runtime" / "widgets" / "evil.json",
        json.dumps(
            {
                "id": "xss-widget",
                "kind": "note",
                "title": "<img src=x onerror=alert(1)>",
                "body": "<script>alert('xss')</script>",
            }
        ),
    )
    payload = json.loads(ui_console.build_response("/api/widgets", tmp_path).body.decode("utf-8"))
    items = payload["items"]["items"]
    evil = next(widget for widget in items if widget["id"] == "xss-widget")
    # The server stores the raw text as DATA (string); the JS renderer escapes it.
    assert evil["title"] == "<img src=x onerror=alert(1)>"
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("function renderWidgetCard")
    end = js.index("function renderWidgets", start)
    block = js[start:end]
    # Every interpolated widget field flows through escapeHtml; nothing is raw.
    assert "escapeHtml(widget.title" in block
    assert "escapeHtml(widget.body" in block
    # The widget renderer carries no eval / Function / dangerous sink.
    for forbidden in ("eval(", "new Function", "outerHTML"):
        assert forbidden not in block


def test_ui_console_i18n_route_has_kr_en_for_key_strings_default_kr(tmp_path):
    payload = json.loads(ui_console.build_response("/api/i18n", tmp_path).body.decode("utf-8"))
    table = payload["items"]
    assert table["default_language"] == "ko"
    assert "ko" in table["languages"] and "en" in table["languages"]
    strings = table["strings"]
    # Key shell strings carry both KR and EN.
    for key in ("nav.group.work", "view.board.title", "button.refresh", "workspace.title"):
        assert key in strings, f"missing i18n key {key}"
        assert strings[key]["ko"], f"missing KR for {key}"
        assert strings[key]["en"], f"missing EN for {key}"
    # KR is genuine Korean text (non-ASCII), proving the table is resourced.
    assert any(ord(ch) > 127 for ch in strings["button.refresh"]["ko"])


def test_ui_console_i18n_t_helper_and_language_toggle_present(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    # Settings toggle for language lives in the topbar.
    assert 'id="lang-toggle"' in html
    assert 'value="ko"' in html and 'value="en"' in html
    # data-i18n anchors mark high-traffic strings for translation.
    assert 'data-i18n="nav.group.work"' in html
    assert 'data-i18n="button.refresh"' in html
    # t() lookup helper + default-KR mechanism + escape-safe application.
    assert "function t(key)" in js
    assert 'const DEFAULT_LANGUAGE = "ko";' in js
    assert "function applyTranslations" in js
    # Translations are applied via textContent (never innerHTML) -> escape-safe.
    start = js.index("function applyTranslations")
    end = js.index("function setLanguage", start)
    block = js[start:end]
    assert "textContent" in block
    assert "innerHTML" not in block


def test_ui_console_i18n_kr_strings_not_inlined_in_ar341_app_js(tmp_path):
    # KR string VALUES must be served via JSON (state / /api/i18n), NOT inlined in
    # app.js by this task. (Pre-existing KR literals from older tasks may remain;
    # this guard checks the i18n/workspace/widget code blocks introduced here.)
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    start = js.index("// ----- TASK-AR-341: i18n")
    end = js.index("async function loadState()", start)
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"AR-341 JS must be ASCII-only, found: {non_ascii[:5]}"


def test_ui_console_ar341_css_uses_tokens_not_raw_color(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    body_css = css.replace(_root_token_block(css), "").replace(_dark_theme_block(css), "")
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    lines = [
        line for line in body_css.splitlines()
        if any(token in line for token in (".workspace-switcher", ".workspace-item", ".lang-toggle", ".home-widget"))
    ]
    assert lines, "expected AR-341 CSS rules to exist"
    for line in lines:
        assert not hex_pattern.search(line), f"raw hex in AR-341 CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in AR-341 CSS: {line.strip()}"


def test_ui_console_ar341_app_js_node_check(tmp_path):
    import shutil
    import subprocess

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_ui_console_knowledge_graph_view_present(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")
    # sidebar + panel
    assert 'data-view="knowledge-graph"' in html
    assert 'data-route="records/knowledge-graph"' in html
    assert 'id="view-knowledge-graph"' in html
    assert 'id="kg-graph-svg"' in html
    # render + on-demand load + activation hook
    assert "function renderKnowledgeGraph" in js
    assert "loadKnowledgeGraph" in js
    assert 'view === "knowledge-graph") loadKnowledgeGraph' in js
    assert ".kg-graph-svg" in css


def test_ui_console_api_knowledge_graph_returns_bounded_subgraph(tmp_path):
    wi = tmp_path / "agents" / "project" / "work-items"
    wi.mkdir(parents=True)
    (wi / "WORK-ITEM-CLASSIFICATION.json").write_text(
        json.dumps({"records": [
            {"id": "TASKSET-A", "level": "taskset", "title": "Set A"},
            {"id": "TASK-AR-1", "level": "task", "title": "One", "parent_id": "TASKSET-A"},
            {"id": "TASK-AR-2", "level": "task", "title": "Two", "parent_id": "TASKSET-A"},
        ]}),
        encoding="utf-8",
    )
    response = ui_console.build_response("/api/knowledge-graph?limit=50", tmp_path)
    assert response.status == 200
    payload = json.loads(response.body.decode("utf-8"))
    ids = {n["id"] for n in payload["nodes"]}
    assert {"TASKSET-A", "TASK-AR-1", "TASK-AR-2"} <= ids
    # partOf edges among the kept nodes are present
    assert any(e["type"] == "partOf" and e["to"] == "TASKSET-A" for e in payload["edges"])
    assert payload["totals"]["shown"] <= 50
    # each node carries a kind + degree for colouring/sizing
    assert all("kind" in n and "degree" in n for n in payload["nodes"])
