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
    assert state["tasks"][0]["display_id"] == "TASK-AR-227"
    assert state["tasks"][0]["metadata"]["registered_at"] == "2026-06-10"
    assert state["tasks"][0]["metadata"]["created_at"] == "2026-06-10"
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


def test_ui_state_exposes_task_identity_and_lifecycle_metadata(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-901",
                "display_id: TASK-AR-901",
                "task_uid: 11111111-1111-4111-8111-111111111111",
                "status: completed",
                "owner: lead-engineer",
                "priority: P0",
                "registered_at: 2026-06-10T12:00:00+09:00",
                "started_at: 2026-06-10T12:05:00+09:00",
                "updated_at: 2026-06-10T12:20:00+09:00",
                "completed_at: 2026-06-10T12:30:00+09:00",
                "---",
                "",
                "## Goal",
                "",
                "Expose lifecycle metadata.",
                "",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:35:00+09:00")

    task = state["tasks"][0]
    assert task["id"] == "TASK-AR-901"
    assert task["task_uid"] == "11111111-1111-4111-8111-111111111111"
    assert task["display_id"] == "TASK-AR-901"
    assert task["metadata"]["registered_at"] == "2026-06-10T12:00:00+09:00"
    assert task["metadata"]["started_at"] == "2026-06-10T12:05:00+09:00"
    assert task["metadata"]["updated_at"] == "2026-06-10T12:20:00+09:00"
    assert task["metadata"]["completed_at"] == "2026-06-10T12:30:00+09:00"
    assert task["registered_at"] == "2026-06-10T12:00:00+09:00"
    assert task["started_at"] == "2026-06-10T12:05:00+09:00"
    assert task["completed_at"] == "2026-06-10T12:30:00+09:00"


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


def test_ui_state_exposes_active_task_claims_as_readable_agent_instances(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-20260610-143012-task-ar-246-a7f3.json",
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-20260610-143012-task-ar-246-a7f3",
                "task_id": "TASK-AR-246",
                "agent_role": "lead-engineer",
                "team_id": "agent-runtime-core",
                "agent_instance_id": "le-20260610-143012-kst-a7f3",
                "display_name": "lead_engineer@design-01",
                "callsite_id": "terminal:wt-task-ar-246:tab-01",
                "pane_id": "terminal:wt-task-ar-246:tab-01",
                "mode": "design",
                "status": "working",
                "phase": "implementation",
                "progress_pct": 45,
                "worktree_path": ".worktrees/TASK-AR-246",
                "branch": "codex/task-ar-246-design-01",
                "claimed_at": "2026-06-10T14:30:12+09:00",
                "last_heartbeat": "2026-06-10T14:30:12+09:00",
                "handoff_path": "agents/runtime/task_claims/CLAIM-20260610-143012-task-ar-246-a7f3.handoff.md",
                "log_path": "agents/runtime/task_claims/CLAIM-20260610-143012-task-ar-246-a7f3.log.md",
                "tags": ["planning", "no-ssot-write"],
            }
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T14:31:00+09:00")

    assert state["agents"][0]["id"] == "le-20260610-143012-kst-a7f3"
    assert state["agents"][0]["role"] == "lead-engineer"
    assert state["agents"][0]["team_id"] == "agent-runtime-core"
    assert state["agents"][0]["display_name"] == "lead_engineer@design-01"
    assert state["agents"][0]["current_task_id"] == "TASK-AR-246"
    assert state["agents"][0]["pane_id"] == "terminal:wt-task-ar-246:tab-01"
    assert state["agents"][0]["mode"] == "design"
    assert state["agents"][0]["phase"] == "implementation"
    assert state["agents"][0]["progress_pct"] == 45
    assert state["agents"][0]["tags"] == ["planning", "no-ssot-write"]
    assert state["agents"][0]["source_kind"] == "task_claim_json"


def test_ui_state_exposes_task_set_progress_and_status_text(tmp_path):
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

    state = ui_state.build_state(tmp_path, now="2026-06-10T18:06:00+09:00")

    assert state["agents"][0]["task_set_id"] == "TASKSET-AR-PROGRESS"
    assert state["agents"][0]["step_index"] == 3
    assert state["agents"][0]["step_total"] == 6
    assert state["agents"][0]["status_text"] == "Rendering task-set progress cards"
    assert state["task_sets"][0]["id"] == "TASKSET-AR-PROGRESS"
    assert state["task_sets"][0]["progress_pct"] == 48
    assert state["task_sets"][0]["active"] == 1


def test_ui_state_cli_emits_task_sets_resource_json(tmp_path, capsys):
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
                "status": "working",
                "phase": "implement",
                "step_index": 3,
                "step_total": 6,
                "progress_pct": 48,
                "status_text": "Rendering task-set progress cards",
            }
        ),
    )

    assert cli_module.main(["ui-state", "--root", str(tmp_path), "--resource", "task_sets", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["resource"] == "task_sets"
    assert payload["items"][0]["id"] == "TASKSET-AR-PROGRESS"
    assert payload["items"][0]["progress_pct"] == 48


def test_ui_state_exposes_collaboration_concurrency_summary(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl",
        json.dumps(
            {
                "schema": "agent-runtime-pane-event/v1",
                "seq": 1,
                "ts": "2026-06-10T23:00:00+09:00",
                "event": "claim_created",
                "actor": "lead-engineer",
                "task_id": "TASK-AR-251",
                "task_set_id": "TASKSET-AR-COLLAB-CONCURRENCY",
                "claim_id": "CLAIM-1",
                "worktree_path": ".worktrees/TASK-AR-251",
            }
        )
        + "\n",
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T23:05:00+09:00")

    assert state["collaboration"]["summary"]["event_count"] == 1
    assert state["collaboration"]["task_sets"][0]["task_set_id"] == "TASKSET-AR-COLLAB-CONCURRENCY"
    assert state["collaboration"]["task_sets"][0]["active_claim_ids"] == ["CLAIM-1"]
    assert any(source["id"] == "pane_events" for source in state["sources"])


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


def test_ui_state_builds_graph_state_machine_and_roadmap_views(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-UI-232-graph.md",
        _task_text("TASK-UI-232", status="in_progress", owner="lead-engineer"),
    )
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
                "Check the graph view.",
                "",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "runtime" / "sessions" / "qa.json",
        json.dumps({"agent_id": "agent-qa", "role": "qa", "status": "active", "task_id": "TASK-UI-232"}),
    )
    _write(
        tmp_path / "agents" / "project" / "STATE-MACHINES.yml",
        "\n".join(
            [
                "schema: test",
                "machines:",
                "  - id: task",
                "    scope: backlog_task",
                "    owner: lead-engineer",
                "    initial: planned",
                "    states:",
                "      - id: planned",
                "      - id: in_progress",
                "      - id: completed",
                "  - id: agent_job",
                "    scope: agent_execution",
                "    owner: agent-runtime-core",
                "    initial: idle",
                "    states:",
                "      - id: idle",
                "      - id: working",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "project" / "ROADMAP.md",
        "\n".join(
            [
                "# Roadmap",
                "",
                "## Current Phase",
                "",
                "- phase: UI console",
                "- next_milestone: Graph view",
                "",
                "## Milestones",
                "",
                "- [ ] 2026-06-20: Graph view ready",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T12:15:00+09:00")

    assert {"owner", "qa"}.issubset({node["id"] for node in state["graph"]["nodes"]})
    assert any(edge["from"] == "owner" and edge["to"] == "qa" and edge["kind"] == "message" for edge in state["graph"]["edges"])
    task_machine = next(machine for machine in state["state_machines"] if machine["id"] == "task")
    assert "in_progress" in task_machine["states"]
    assert task_machine["current_state"] == "in_progress"
    assert state["roadmap"]["phase"] == "UI console"
    assert state["roadmap"]["milestones"][0]["title"] == "Graph view ready"
    assert state["roadmap"]["milestones"][0]["done"] is False


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
