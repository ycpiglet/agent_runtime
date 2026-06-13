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


def test_ui_state_enriches_tasks_with_task_set_and_evidence_count(tmp_path):
    root = tmp_path
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-279.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-279",
                "status: in_progress",
                "owner: lead-engineer",
                "priority: P1",
                "task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
                "---",
                "",
                "## Goal",
                "",
                "Apply visual hierarchy to backlog cards.",
                "",
            ]
        ),
    )
    _write(
        root / "agents" / "runtime" / "events" / "lead-engineer-2026-06-11.jsonl",
        json.dumps(
            {
                "ts": "2026-06-11T04:55:00+09:00",
                "role": "lead-engineer",
                "event": "verification",
                "task_id": "TASK-AR-279",
                "evidence": ["tests/test_ui_console.py", "reviews/REVIEW-279.md"],
            }
        )
        + "\n",
    )

    state = ui_state.build_state(root, now="2026-06-11T04:56:00+09:00")

    assert state["tasks"][0]["task_set_id"] == "TASKSET-AR-UI-DESIGN-IMPLEMENTATION"
    assert state["tasks"][0]["evidence_count"] == 2
    assert state["tasks"][0]["evidence_label"] == "2 evidence"


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


def test_ui_state_exposes_agent_score_label_from_task_claim(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-score.json",
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-score",
                "task_id": "TASK-AR-280",
                "task_set_id": "TASKSET-AR-UI-DESIGN-IMPLEMENTATION",
                "agent_role": "lead-engineer",
                "team_id": "agent-runtime-core",
                "agent_instance_id": "le-score",
                "display_name": "lead_engineer@score-01",
                "callsite_id": "terminal:wt-task-ar-280:tab-01",
                "pane_id": "terminal:wt-task-ar-280:tab-01",
                "status": "working",
                "phase": "implement",
                "progress_pct": 64,
                "score": 91,
                "status_text": "Designing command hierarchy",
                "worktree_path": ".worktrees/TASK-AR-280",
                "branch": "codex/task-ar-280-ui",
                "claimed_at": "2026-06-11T08:42:47+09:00",
                "last_heartbeat": "2026-06-11T08:50:00+09:00",
            }
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-11T08:51:00+09:00")

    assert state["agents"][0]["score"] == 91
    assert state["agents"][0]["score_label"] == "91/100"


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


def test_ui_state_exposes_taskset_numeric_letter_aliases_and_commands(tmp_path):
    _write(
        tmp_path / "scripts" / "backlog_board.py",
        "\n".join(
            [
                "from dataclasses import dataclass",
                "@dataclass(frozen=True)",
                "class TaskSetInfo:",
                "    task_set_id: str",
                "    display_name: str",
                "    summary: str",
                "    order: int",
                "TASK_SET_DEFINITIONS = [",
                "    TaskSetInfo('TASKSET-AR-CONTEXT-KNOWLEDGE', 'Context Cartographer', 'Context work.', 10),",
                "    TaskSetInfo('TASKSET-AR-QUALITY-LOOP', 'Quality Sentinel', 'Quality work.', 20),",
                "]",
                "UNCLASSIFIED_TASK_SET = TaskSetInfo('TASKSET-AR-UNCLASSIFIED', 'Unclassified', 'No task set.', 999)",
                "",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-901",
                "status: completed",
                "owner: lead-engineer",
                "priority: P0",
                "task_set_id: TASKSET-AR-QUALITY-LOOP",
                "---",
                "",
                "## Goal",
                "",
                "Completed quality task.",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-902",
                "status: planned",
                "owner: lead-engineer",
                "priority: P0",
                "task_set_id: TASKSET-AR-QUALITY-LOOP",
                "---",
                "",
                "## Goal",
                "",
                "Next quality task.",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-11T18:30:00+09:00")
    task_set = state["task_sets"][0]

    assert task_set["id"] == "TASKSET-AR-QUALITY-LOOP"
    assert task_set["display_name"] == "Quality Sentinel"
    assert task_set["alias_number"] == 2
    assert task_set["alias_letter"] == "B"
    assert "taskset 2" in task_set["aliases"]
    assert "taskset B" in task_set["aliases"]
    assert "quality-loop" in task_set["aliases"]
    assert task_set["primary_alias"] == "taskset 2"
    assert task_set["letter_alias"] == "taskset B"
    assert task_set["next_task_id"] == "TASK-AR-902"
    assert task_set["tasks_total"] == 2
    assert task_set["tasks_done"] == 1
    assert task_set["progress_pct"] == 50
    assert task_set["commands"]["plan"] == "python scripts/taskset_dispatcher.py plan 2 --json"
    assert task_set["commands"]["start"] == "python scripts/taskset_dispatcher.py start 2 --json"
    assert task_set["commands"]["gate"] == "python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-QUALITY-LOOP --check"


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


def test_ui_state_exposes_multipane_assurance_summary(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-assurance.json",
        json.dumps(
            {
                "claim_id": "CLAIM-assurance",
                "task_id": "TASK-AR-285",
                "task_set_id": "TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE",
                "agent_role": "lead-engineer",
                "status": "working",
                "phase": "implement",
                "progress_pct": 50,
                "worktree_path": ".worktrees/TASK-AR-285",
            }
        ),
    )
    _write(
        tmp_path / "agents" / "project" / "MULTIPANE-PROCESS-POLICY.yml",
        "required_artifacts:\n  - REVIEW\nrequired_roles:\n  - lead-engineer\n",
    )
    _write(tmp_path / "reviews" / "REVIEW-assurance.md", "# Review\n")

    state = ui_state.build_state(tmp_path, now="2026-06-11T12:05:00+09:00")

    assurance = state["multipane_assurance"]
    assert assurance["census"]["active_claims"] == 1
    assert assurance["process"]["status"] in {"pass", "watch"}
    assert "role_coverage" in assurance
    assert "drift" in assurance
    assert "event_summary" in assurance
    assert any(source["id"] == "multipane_assurance" for source in state["sources"])


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
    snapshot = ui_state.build_replay_snapshot(state["replay"], "2026-06-10T12:00:00+09:00")
    assert snapshot["resource"] == "replay_snapshot"
    assert snapshot["task_ids"] == ["TASK-UI-231"]


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


def _write_work_classification(root: Path, records: list[dict]) -> None:
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


def _work_explorer_records() -> list[dict]:
    return [
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
            "progress_pct": 95,
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
            "key": "task:TASK-AR-515",
            "level": "task",
            "number": "1.1.2",
            "label": "Task 1.1.2",
            "id": "TASK-AR-515",
            "title": "Work metadata ingestion",
            "path": "agents/lead_engineer/tasks/TASK-AR-515.md",
            "parent_id": "TASKSET-AR-WORK-METADATA-ANALYTICS",
            "status": "in_progress",
        },
        {
            "key": "task:TASK-AR-516",
            "level": "task",
            "number": "1.1.3",
            "label": "Task 1.1.3",
            "id": "TASK-AR-516",
            "title": "Work Explorer tree",
            "path": "agents/lead_engineer/tasks/TASK-AR-516.md",
            "parent_id": "TASKSET-AR-WORK-METADATA-ANALYTICS",
            "status": "planned",
        },
        {
            "key": "unit:UNIT-TASK-AR-514-001",
            "level": "unit",
            "number": "1.1.1.1",
            "label": "Unit 1.1.1.1",
            "id": "UNIT-TASK-AR-514-001",
            "title": "Schema catalog unit",
            "path": "agents/lead_engineer/tasks/units/TASK-AR-514/UNIT-TASK-AR-514-001.md",
            "parent_id": "TASK-AR-514",
            "status": "completed",
        },
    ]


def _write_work_explorer_task_markdown(root: Path) -> None:
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-514.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-514",
                "status: completed",
                "owner: lead_engineer",
                "priority: P1",
                "difficulty: M",
                "team: agent-runtime-core",
                "worker_model_tier: worker_standard",
                "origin_type: owner_request",
                "verification_status: passed",
                "task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS",
                "evidence_refs:",
                "  - reviews/VERIFY-2026-06-12-task-ar-514.json",
                "audit_log:",
                "  - reviews/MEETING-2026-06-12-work-metadata.md",
                "---",
                "",
                "## Goal",
                "",
                "Define the work metadata schema.",
                "",
            ]
        ),
    )


def _work_explorer_node(state: dict, node_id: str) -> dict:
    return next(node for node in state["work_explorer"]["nodes"] if node["id"] == node_id)


def test_ui_state_work_explorer_builds_tree_with_computed_rollups_and_facets(tmp_path):
    _write_work_classification(tmp_path, _work_explorer_records())
    _write_work_explorer_task_markdown(tmp_path)

    state = ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00")
    explorer = state["work_explorer"]

    assert explorer["schema"] == "agent-runtime-work-explorer/v1"
    assert explorer["freshness"] == "present"
    assert explorer["record_count"] == 6
    assert explorer["source_path"] == "agents/project/work-items/WORK-ITEM-CLASSIFICATION.json"
    assert explorer["source_last_updated"] is not None
    assert "work_item_classifier" in explorer["staleness_note"]
    assert explorer["roots"] == ["INIT-AR-WORK-METADATA-ANALYTICS"]

    initiative = _work_explorer_node(state, "INIT-AR-WORK-METADATA-ANALYTICS")
    taskset = _work_explorer_node(state, "TASKSET-AR-WORK-METADATA-ANALYTICS")
    completed_task = _work_explorer_node(state, "TASK-AR-514")
    planned_task = _work_explorer_node(state, "TASK-AR-516")
    unit = _work_explorer_node(state, "UNIT-TASK-AR-514-001")

    assert initiative["children"] == ["TASKSET-AR-WORK-METADATA-ANALYTICS"]
    assert taskset["children"] == ["TASK-AR-514", "TASK-AR-515", "TASK-AR-516"]
    assert completed_task["children"] == ["UNIT-TASK-AR-514-001"]
    assert (initiative["depth"], taskset["depth"], completed_task["depth"], unit["depth"]) == (0, 1, 2, 3)
    assert unit["taskset_id"] == "TASKSET-AR-WORK-METADATA-ANALYTICS"

    assert taskset["rollup"] == {"total": 3, "completed": 1, "in_progress": 1, "planned": 1, "pct": 33}
    assert completed_task["rollup"] == {"total": 1, "completed": 1, "in_progress": 0, "planned": 0, "pct": 100}
    assert planned_task["rollup"] == {"total": 0, "completed": 0, "in_progress": 0, "planned": 0, "pct": None}
    assert initiative["rollup"] == {"total": 1, "completed": 0, "in_progress": 1, "planned": 0, "pct": 0}

    assert completed_task["facets"]["owner"] == "lead_engineer"
    assert completed_task["facets"]["priority"] == "P1"
    assert completed_task["facets"]["difficulty"] == "M"
    assert completed_task["facets"]["team"] == "agent-runtime-core"
    assert completed_task["facets"]["model_tier"] == "worker_standard"
    assert completed_task["facets"]["origin"] == "owner_request"
    assert completed_task["facets"]["verification"] == "passed"
    assert completed_task["facets"]["taskset"] == "TASKSET-AR-WORK-METADATA-ANALYTICS"
    assert explorer["facets"]["owner"] == ["lead_engineer"]
    assert explorer["facets"]["priority"] == ["P1"]
    assert explorer["facets"]["difficulty"] == ["M"]
    assert explorer["facets"]["team"] == ["agent-runtime-core"]
    assert explorer["facets"]["verification"] == ["passed"]
    assert "TASKSET-AR-WORK-METADATA-ANALYTICS" in explorer["facets"]["taskset"]
    assert {"planned", "active", "completed", "in_progress"}.issubset(set(explorer["facets"]["status"]))
    assert {"initiative", "taskset", "task", "unit"}.issubset(set(explorer["facets"]["kind"]))

    assert "reviews/VERIFY-2026-06-12-task-ar-514.json" in completed_task["evidence_refs"]
    assert "reviews/MEETING-2026-06-12-work-metadata.md" in completed_task["evidence_refs"]
    assert "reviews/VERIFY-2026-06-12-task-ar-514.json" in taskset["descendant_evidence_refs"]
    assert "reviews/VERIFY-2026-06-12-task-ar-514.json" in initiative["descendant_evidence_refs"]

    payload = ui_state.build_resource(tmp_path, "work_explorer", now="2026-06-13T03:00:00+09:00")
    assert payload["resource"] == "work_explorer"
    assert payload["items"]["record_count"] == 6


def test_ui_state_work_explorer_rollups_change_only_from_child_state(tmp_path):
    records = _work_explorer_records()
    _write_work_classification(tmp_path, records)
    baseline = ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00")
    baseline_rollup = _work_explorer_node(baseline, "TASKSET-AR-WORK-METADATA-ANALYTICS")["rollup"]
    assert baseline_rollup["completed"] == 1
    assert baseline_rollup["pct"] == 33

    # Mutating stored parent progress alone never moves the computed roll-up.
    records[1]["progress_pct"] = 5
    _write_work_classification(tmp_path, records)
    unchanged = ui_state.build_state(tmp_path, now="2026-06-13T03:01:00+09:00")
    assert _work_explorer_node(unchanged, "TASKSET-AR-WORK-METADATA-ANALYTICS")["rollup"] == baseline_rollup

    # Mutating a child record's status is the only thing that moves it.
    records[4]["status"] = "completed"
    _write_work_classification(tmp_path, records)
    mutated = ui_state.build_state(tmp_path, now="2026-06-13T03:02:00+09:00")
    mutated_rollup = _work_explorer_node(mutated, "TASKSET-AR-WORK-METADATA-ANALYTICS")["rollup"]
    assert mutated_rollup == {"total": 3, "completed": 2, "in_progress": 1, "planned": 0, "pct": 67}


def test_ui_state_work_explorer_missing_or_malformed_snapshot_degrades_safely(tmp_path):
    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    state = ui_state.build_state(missing_root, now="2026-06-13T03:00:00+09:00")
    explorer = state["work_explorer"]
    assert explorer["freshness"] == "missing"
    assert explorer["nodes"] == []
    assert explorer["record_count"] == 0
    assert "work_item_classifier" in explorer["staleness_note"]
    assert any(warning["kind"] == "work-explorer-source-missing" for warning in state["warnings"])
    assert any(gap["path"] == "agents/project/work-items/WORK-ITEM-CLASSIFICATION.json" for gap in state["gaps"])

    malformed_root = tmp_path / "malformed"
    _write(malformed_root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json", "{not-json")
    state = ui_state.build_state(malformed_root, now="2026-06-13T03:00:00+09:00")
    assert state["work_explorer"]["freshness"] == "missing"
    assert state["work_explorer"]["error"]
    assert any(warning["kind"] == "work-explorer-source-error" for warning in state["warnings"])


def _tasksets_board_card(state: dict, taskset_id: str) -> dict:
    return next(card for card in state["tasksets_board"]["cards"] if card["id"] == taskset_id)


def test_ui_state_tasksets_board_groups_tasks_with_computed_progress(tmp_path):
    _write_work_classification(tmp_path, _work_explorer_records())
    _write_work_explorer_task_markdown(tmp_path)
    # A live task record that should be joined into the board child by id.
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-515.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-515",
                "status: in_progress",
                "owner: worker-ui1",
                "priority: P2",
                "task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS",
                "---",
                "",
                "## Goal",
                "",
                "Ingest work metadata.",
                "",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00")
    board = state["tasksets_board"]

    assert board["schema"] == "agent-runtime-tasksets-board/v1"
    assert board["freshness"] == "present"
    assert board["create_command"] == "task.create"
    assert board["source_path"] == "agents/project/work-items/WORK-ITEM-CLASSIFICATION.json"

    card = _tasksets_board_card(state, "TASKSET-AR-WORK-METADATA-ANALYTICS")
    # Progress is computed from child status only (1 of 3 complete -> 33%).
    assert card["progress"] == {"done": 1, "total": 3}
    assert card["progress_pct"] == 33
    assert card["status_distribution"] == {"completed": 1, "in_progress": 1, "planned": 1}
    assert "worker-ui1" in card["assigned_agents"]

    children = {child["id"]: child for child in card["children"]}
    assert set(children) == {"TASK-AR-514", "TASK-AR-515", "TASK-AR-516"}
    assert children["TASK-AR-514"]["phase"] == "done"
    assert children["TASK-AR-515"]["phase"] == "work"
    assert children["TASK-AR-516"]["phase"] == "plan"
    # Live record wins for owner/priority on the joined child.
    assert children["TASK-AR-515"]["owner"] == "worker-ui1"
    assert children["TASK-AR-515"]["priority"] == "P2"

    payload = ui_state.build_resource(tmp_path, "tasksets_board", now="2026-06-13T03:00:00+09:00")
    assert payload["resource"] == "tasksets_board"
    assert payload["items"]["totals"]["tasksets"] >= 1


def test_ui_state_tasksets_board_progress_changes_only_from_child_state(tmp_path):
    records = _work_explorer_records()
    _write_work_classification(tmp_path, records)
    baseline = _tasksets_board_card(
        ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00"),
        "TASKSET-AR-WORK-METADATA-ANALYTICS",
    )
    assert baseline["progress"] == {"done": 1, "total": 3}
    assert baseline["progress_pct"] == 33

    # Stored snapshot progress field must never move the computed board card.
    records[1]["progress_pct"] = 5
    _write_work_classification(tmp_path, records)
    unchanged = _tasksets_board_card(
        ui_state.build_state(tmp_path, now="2026-06-13T03:01:00+09:00"),
        "TASKSET-AR-WORK-METADATA-ANALYTICS",
    )
    assert unchanged["progress"] == baseline["progress"]
    assert unchanged["progress_pct"] == baseline["progress_pct"]

    # Flipping a child status is the only thing that moves the board.
    records[4]["status"] = "completed"
    _write_work_classification(tmp_path, records)
    mutated = _tasksets_board_card(
        ui_state.build_state(tmp_path, now="2026-06-13T03:02:00+09:00"),
        "TASKSET-AR-WORK-METADATA-ANALYTICS",
    )
    assert mutated["progress"] == {"done": 2, "total": 3}
    assert mutated["progress_pct"] == 67


def test_ui_state_tasksets_board_degrades_safely_when_snapshot_missing(tmp_path):
    missing_root = tmp_path / "missing"
    missing_root.mkdir()
    state = ui_state.build_state(missing_root, now="2026-06-13T03:00:00+09:00")
    board = state["tasksets_board"]
    assert board["freshness"] == "missing"
    assert board["cards"] == []
    assert board["totals"]["tasksets"] == 0
    assert board["create_command"] == "task.create"


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
