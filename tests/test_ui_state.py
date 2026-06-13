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


def test_ui_state_task_exposes_peek_summary_for_board_hover(tmp_path):
    root = tmp_path
    _write(root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-362-peek.md", _task_text("TASK-AR-362"))

    state = ui_state.build_state(root, now="2026-06-13T12:05:00+09:00")
    task = state["tasks"][0]

    # peek_summary is a derived, additive field that folds the blocked reason
    # into the goal sentence for a single hover-peek line.
    assert task["peek_summary"] == "Blocked: waiting on sample data. Expose a safe read-only state API."

    # Without a blocked reason it falls back to the goal description.
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-363-peek.md",
        _task_text("TASK-AR-363").replace("blocked_reason: waiting on sample data\n", ""),
    )
    refreshed = ui_state.build_state(root, now="2026-06-13T12:06:00+09:00")
    unblocked = next(item for item in refreshed["tasks"] if item["id"] == "TASK-AR-363")
    assert unblocked["peek_summary"] == "Expose a safe read-only state API."


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


# ----- TASK-AR-326: realtime presence + live map -----


def test_ui_state_live_map_resource_shape_and_safe_degrade(tmp_path):
    # Empty root -> well-formed, owner-only live map with no crash.
    payload = ui_state.build_resource(tmp_path, "live_map", now="2026-06-13T11:00:00+09:00")
    assert payload["resource"] == "live_map"
    live_map = payload["items"]
    assert live_map["schema"] == "agent-runtime-live-map/v1"
    assert set(live_map.keys()) >= {"schema", "generated_at", "presence", "nodes", "edges", "totals"}
    assert live_map["presence"] == {"counts": {}, "online": 0, "agents": []}
    # Owner is always the apex node even when nothing else exists.
    assert [node["kind"] for node in live_map["nodes"]] == ["owner"]
    assert live_map["totals"]["node_kinds"] == {"owner": 1}
    assert live_map["edges"] == []


def test_ui_state_live_map_derives_typed_nodes_and_edges(tmp_path):
    # A review task + a message produce taskset/gate nodes and typed edges.
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-700-review.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-700",
                "status: review",
                "owner: lead-engineer",
                "task_set_id: TASKSET-AR-LIVE",
                "priority: P1",
                "---",
                "",
                "## Goal",
                "",
                "Review the live map.",
                "",
            ]
        ),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-701-blocked.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-701",
                "status: blocked",
                "owner: qa",
                "task_set_id: TASKSET-AR-LIVE",
                "priority: P1",
                "blocked_reason: waiting on data",
                "---",
                "",
                "## Goal",
                "",
                "Blocked work.",
                "",
            ]
        ),
    )
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
                "task_id: TASK-AR-700",
                "---",
                "",
                "Ship the live map.",
                "",
            ]
        ),
    )
    _write_instance(tmp_path, "inst-le-01", role="lead-engineer", team_id="agent-runtime-core")
    _write_team_claim(tmp_path, "CLAIM-live", "inst-le-01", status="in_progress", task_id="TASK-AR-700")

    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    live_map = state["live_map"]

    node_kinds = {node["id"]: node["kind"] for node in live_map["nodes"]}
    assert node_kinds.get("owner") == "owner"
    assert node_kinds.get("TASKSET-AR-LIVE") == "taskset"
    assert node_kinds.get("lead-engineer") == "agent"
    # Gate node derived from the review/blocked work.
    assert any(kind == "gate" for kind in node_kinds.values())

    edge_kinds = {edge["kind"] for edge in live_map["edges"]}
    assert "message" in edge_kinds       # owner -> lead-engineer message
    assert "assignment" in edge_kinds    # owner -> taskset assignment
    assert "review" in edge_kinds        # review-state task -> gate
    assert "block" in edge_kinds         # blocked task -> gate

    # Edges carry stable ids and endpoints so the front-end can pulse them.
    msg_edge = next(edge for edge in live_map["edges"] if edge["kind"] == "message")
    assert msg_edge["from"] == "owner" and msg_edge["to"] == "lead-engineer"
    assert msg_edge["id"] == "message:MSG-20260613-live"

    # Presence roll-up reflects the team_agents view (lead-engineer is working).
    presence = live_map["presence"]
    assert presence["online"] >= 1
    assert presence["counts"].get("working", 0) >= 1
    roles = {agent["role"]: agent["presence"] for agent in presence["agents"]}
    assert roles.get("lead-engineer") == "working"

    assert live_map["totals"]["edges"] == len(live_map["edges"])
    assert live_map["totals"]["nodes"] == len(live_map["nodes"])


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


def _write_release_decision(root: Path, version: str, *, status: str = "agent_council_approved", owner_required: bool = False) -> None:
    _write(
        root / "agents" / "project" / "release" / f"RELEASE-DECISION-v{version}.yml",
        "\n".join(
            [
                "schema: agent-runtime-release-decision/v1",
                f"target_version: {version}",
                f"target_tag: v{version}",
                f"status: {status}",
                "criticality: noncritical",
                f"owner_required: {'true' if owner_required else 'false'}",
                "approved_by: agent-release-council",
                "decision_date: 2026-06-13",
                "",
            ]
        ),
    )


def test_ui_state_roadmap_timeline_links_milestones_and_orders_tiers(tmp_path):
    _write_work_classification(tmp_path, _work_explorer_records())
    _write_work_explorer_task_markdown(tmp_path)
    _write(
        tmp_path / "agents" / "project" / "VISION.md",
        "\n".join(
            [
                "# Vision",
                "",
                "## Problem",
                "",
                "Context drift across projects.",
                "",
                "## Vision",
                "",
                "Standardize project overlays while keeping the runtime shared.",
                "",
                "## Success metric",
                "",
                "Required context matches without runtime edits.",
                "",
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
                "- phase: metadata analytics",
                "- next_milestone: ship explorer",
                "",
                "## Milestones",
                "",
                "- [x] 2026-06-10: kickoff prep with no linked ids",
                "- [ ] 2026-06-20: `TASKSET-AR-WORK-METADATA-ANALYTICS` rollup and `TASK-AR-516` proof",
                "- [ ] 2026-06-15: `TASK-AR-514` schema landed",
                "",
            ]
        ),
    )
    _write_release_decision(tmp_path, "0.1.8")
    _write_release_decision(tmp_path, "0.2.0", owner_required=True)

    state = ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00")
    timeline = state["roadmap_timeline"]

    # Resource shape
    assert timeline["schema"] == "agent-runtime-roadmap-timeline/v1"
    assert timeline["phase"] == "metadata analytics"
    assert {"vision", "milestones", "releases", "summary"}.issubset(timeline.keys())

    # Vision tier parsed from VISION.md
    assert timeline["vision"]["tier"] == "vision"
    assert "overlays" in (timeline["vision"]["statement"] or "")
    assert timeline["vision"]["success_metric"]

    # Timeline ordering: milestones ascending by date.
    dates = [m["date"] for m in timeline["milestones"]]
    assert dates == ["2026-06-10", "2026-06-15", "2026-06-20"]

    # Milestone -> taskset/task linkage joined to the work-explorer hierarchy.
    by_date = {m["date"]: m for m in timeline["milestones"]}
    rollup_ms = by_date["2026-06-20"]
    linked_ids = {link["id"] for link in rollup_ms["linked_work"]}
    assert "TASKSET-AR-WORK-METADATA-ANALYTICS" in linked_ids
    assert "TASK-AR-516" in linked_ids
    taskset_link = next(link for link in rollup_ms["linked_work"] if link["id"] == "TASKSET-AR-WORK-METADATA-ANALYTICS")
    assert taskset_link["level"] == "taskset"
    assert taskset_link["resolved"] is True
    # Roll-up pct is computed from joined task state, never a stored field.
    assert rollup_ms["rollup"]["pct"] is not None

    # A milestone with no recognizable ids resolves to zero linked work.
    assert by_date["2026-06-10"]["rollup"]["linked"] == 0

    # Release tier parsed from release-decision YAMLs, ordered by version.
    versions = [r["version"] for r in timeline["releases"]]
    assert versions == ["0.1.8", "0.2.0"]
    assert timeline["releases"][1]["owner_required"] is True
    assert all(r["tier"] == "release" for r in timeline["releases"])

    assert timeline["summary"]["releases"] == 2
    assert timeline["summary"]["milestones"] == 3


def test_ui_state_roadmap_timeline_resource_shape_when_sources_missing(tmp_path):
    state = ui_state.build_state(tmp_path, now="2026-06-13T03:00:00+09:00")
    timeline = state["roadmap_timeline"]
    assert timeline["schema"] == "agent-runtime-roadmap-timeline/v1"
    assert timeline["milestones"] == []
    assert timeline["releases"] == []
    assert timeline["vision"]["freshness"] == "missing"

    resource = ui_state.build_resource(tmp_path, "roadmap_timeline", now="2026-06-13T03:00:00+09:00")
    assert resource["resource"] == "roadmap_timeline"
    assert resource["items"]["schema"] == "agent-runtime-roadmap-timeline/v1"


# --- Team / Agent RPG presence (TASK-AR-324) -------------------------------


def _write_instance(root: Path, instance_id: str, **overrides) -> None:
    record = {
        "schema": "agent-runtime-agent-instance/v1",
        "agent_instance_id": instance_id,
        "callsign": f"claude/{instance_id}",
        "display_name": f"claude/{instance_id}",
        "role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "model": "claude-opus",
        "model_tier": "opus",
        "provider": "anthropic",
        "skill_versions": {"lead_engineer": "1.0.0"},
        "task_id": "TASK-AR-900",
        "task_set_id": "TASKSET-AR-DEMO",
        "spawned_at": "2026-06-13T10:00:00+09:00",
    }
    record.update(overrides)
    _write(root / "agents" / "runtime" / "instances" / f"{instance_id}.json", json.dumps(record))


def _write_team_claim(root: Path, claim_id: str, instance_id: str, *, status: str, **overrides) -> None:
    record = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": overrides.pop("task_id", "TASK-AR-901"),
        "agent_role": "lead-engineer",
        "team_id": "agent-runtime-core",
        "agent_instance_id": instance_id,
        "display_name": f"claude/{instance_id}",
        "status": status,
        "phase": "implement",
        "progress_pct": 40,
        "claimed_at": "2026-06-13T10:30:00+09:00",
        "last_heartbeat": "2026-06-13T10:40:00+09:00",
    }
    record.update(overrides)
    _write(root / "agents" / "runtime" / "task_claims" / f"{claim_id}.json", json.dumps(record))


def _team_agent_card(state: dict, instance_id: str) -> dict:
    for team in state["team_agents"]["teams"]:
        for card in team["agents"]:
            if card["id"] == instance_id:
                return card
    raise AssertionError(f"agent card not found: {instance_id}")


def test_ui_state_team_agents_groups_instances_into_team_hierarchy_with_cards(tmp_path):
    _write_instance(tmp_path, "inst-le-01", role="lead-engineer", team_id="agent-runtime-core")
    _write_instance(tmp_path, "inst-qa-02", role="qa", team_id="agent-runtime-core")
    _write_instance(tmp_path, "inst-mp-03", role="managing-partner", team_id="governance-loop")
    _write_team_claim(tmp_path, "CLAIM-active", "inst-le-01", status="in_progress", task_id="TASK-AR-910")

    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    team_agents = state["team_agents"]

    assert team_agents["schema"] == "agent-runtime-team-agents/v1"
    assert team_agents["totals"] == {"teams": 2, "agents": 3, "online": 1}
    team_ids = [team["team_id"] for team in team_agents["teams"]]
    assert team_ids == ["agent-runtime-core", "governance-loop"]

    core = next(team for team in team_agents["teams"] if team["team_id"] == "agent-runtime-core")
    assert core["agent_count"] == 2
    assert core["online_count"] == 1
    assert core["role_distribution"] == {"lead-engineer": 1, "qa": 1}

    card = _team_agent_card(state, "inst-le-01")
    assert card["role"] == "lead-engineer"
    assert card["callsign"] == "claude/inst-le-01"
    assert card["model"] == "claude-opus"
    assert card["skill_versions"] == {"lead_engineer": "1.0.0"}
    assert card["presence"] == "working"
    assert card["online"] is True
    assert card["current_claim"]["task_id"] == "TASK-AR-910"
    assert card["avatar"] == "LE"

    offline = _team_agent_card(state, "inst-qa-02")
    assert offline["presence"] == "offline"
    assert offline["online"] is False
    assert offline["current_claim"] is None


def test_ui_state_team_agents_level_xp_derived_from_completed_claim_counts(tmp_path):
    _write_instance(tmp_path, "inst-le-01")

    baseline = _team_agent_card(
        ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00"),
        "inst-le-01",
    )
    # No completed work -> level 1, zero XP.
    assert baseline["level"] == 1
    assert baseline["xp"] == 0
    assert baseline["lifetime"]["completed_tasks"] == 0

    # Mutating a STORED field (instance progress) must not move level/XP.
    _write_instance(tmp_path, "inst-le-01", progress_pct=99, level=42, xp=99999)
    unchanged = _team_agent_card(
        ui_state.build_state(tmp_path, now="2026-06-13T11:01:00+09:00"),
        "inst-le-01",
    )
    assert unchanged["level"] == baseline["level"]
    assert unchanged["xp"] == baseline["xp"]

    # Adding completed claims (the work count) is what moves the XP bar.
    _write_team_claim(tmp_path, "CLAIM-done-1", "inst-le-01", status="completed", task_id="TASK-AR-801")
    _write_team_claim(tmp_path, "CLAIM-done-2", "inst-le-01", status="completed", task_id="TASK-AR-802")
    grown = _team_agent_card(
        ui_state.build_state(tmp_path, now="2026-06-13T11:02:00+09:00"),
        "inst-le-01",
    )
    assert grown["lifetime"]["completed_tasks"] == 2
    assert grown["xp"] == 200  # 2 tasks * 100 XP
    assert grown["xp"] > baseline["xp"]
    assert grown["level"] >= baseline["level"]
    # Completed-unit claims add their own XP increment.
    _write_team_claim(
        tmp_path, "CLAIM-done-3", "inst-le-01", status="completed", task_id="TASK-AR-803", unit_id="UNIT-1"
    )
    with_unit = _team_agent_card(
        ui_state.build_state(tmp_path, now="2026-06-13T11:03:00+09:00"),
        "inst-le-01",
    )
    assert with_unit["lifetime"]["completed_units"] == 1
    assert with_unit["xp"] == 320  # 3 tasks * 100 + 1 unit * 20


def test_ui_state_team_agents_resource_payload_and_safe_degrade(tmp_path):
    payload = ui_state.build_resource(tmp_path, "team_agents", now="2026-06-13T11:00:00+09:00")
    assert payload["resource"] == "team_agents"
    assert payload["items"]["schema"] == "agent-runtime-team-agents/v1"
    # No instances present -> empty, well-formed payload (no crash).
    assert payload["items"]["teams"] == []
    assert payload["items"]["totals"] == {"teams": 0, "agents": 0, "online": 0}


def _write_taskset_task(root: Path, task_id: str, task_set_id: str, status: str) -> None:
    _write(
        root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md",
        "\n".join(
            [
                "---",
                f"id: {task_id}",
                f"status: {status}",
                "owner: lead-engineer",
                "priority: P0",
                f"task_set_id: {task_set_id}",
                "tags: []",
                "---",
                "",
                "## Goal",
                "",
                "Sample.",
                "",
            ]
        ),
    )


def test_ui_state_taskset_completion_inactive_without_event(tmp_path):
    _write_taskset_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", "in_progress")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    completion = state["taskset_completion"]
    assert completion["schema"] == "agent-runtime-taskset-completion/v1"
    assert completion["active"] is False


def test_ui_state_taskset_completion_banner_and_next_suggestion(tmp_path):
    # Completed taskset (all tasks done) plus a second taskset with open work.
    _write_taskset_task(tmp_path, "TASK-AR-901", "TASKSET-AR-QUALITY-LOOP", "completed")
    _write_taskset_task(tmp_path, "TASK-AR-911", "TASKSET-AR-UI-UX-V2", "planned")
    _write(
        tmp_path / "agents" / "runtime" / "pane_events" / "pane-events.jsonl",
        json.dumps(
            {
                "schema": "agent-runtime-pane-event/v1",
                "seq": 1,
                "ts": "2026-06-13T10:30:00+09:00",
                "event": "taskset.completed",
                "actor": "le-1",
                "task_set_id": "TASKSET-AR-QUALITY-LOOP",
                "claim_id": "CLAIM-DONE",
                "message": "Taskset TASKSET-AR-QUALITY-LOOP completed; stop and report.",
            }
        )
        + "\n",
    )

    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    completion = state["taskset_completion"]

    assert completion["active"] is True
    assert completion["completed_task_set_id"] == "TASKSET-AR-QUALITY-LOOP"
    assert completion["policy"] == "stop_and_report"
    assert "stop and report" in completion["message"]
    nxt = completion["next_suggestion"]
    assert nxt is not None
    assert nxt["id"] == "TASKSET-AR-UI-UX-V2"
    assert nxt["approval_state"] == "awaiting_approval"
    assert nxt["start_command"]

    payload = ui_state.build_resource(tmp_path, "taskset_completion", now="2026-06-13T11:00:00+09:00")
    assert payload["resource"] == "taskset_completion"
    assert payload["items"]["active"] is True


# ----- TASK-AR-327: Channels resource (spectate agent conversations) -----


def _channel_message(root: Path, msg_id: str, *, sender: str, to: str, intent: str, task_id: str | None) -> None:
    lines = [
        "---",
        f"id: {msg_id}",
        f"from: {sender}",
        f"to: {to}",
        "type: instruction",
        "status: queued",
        "ts: 2026-06-12T10:00:00+09:00",
        f"intent: {intent}",
    ]
    if task_id:
        lines.append(f"task_id: {task_id}")
    lines.extend(["---", "", "Hello <b>there</b>", ""])
    _write(root / "agents" / "messages" / "inbox" / f"{msg_id}.md", "\n".join(lines))


def test_ui_state_channels_resource_shape(tmp_path):
    root = tmp_path
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900-demo.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-900",
                "title: Demo task",
                "status: in_progress",
                "owner: lead-engineer",
                "priority: P1",
                "task_set_id: TASKSET-AR-DEMO",
                "---",
                "",
                "## Goal",
                "",
                "Demo.",
                "",
            ]
        ),
    )
    _channel_message(root, "MSG-1", sender="lead-engineer", to="qa", intent="build", task_id="TASK-AR-900")
    _channel_message(root, "MSG-2", sender="planner", to="governance", intent="governance review", task_id=None)
    _channel_message(root, "MSG-3", sender="qa", to="lead-engineer", intent="chat", task_id=None)

    channels = ui_state.build_resource(root, "channels", now="2026-06-12T12:00:00+09:00")["items"]
    assert channels["schema"] == "agent-runtime-channels/v1"
    by_id = {channel["id"]: channel for channel in channels["channels"]}

    # Auto channels: #general + #governance always present.
    assert "general" in by_id and by_id["general"]["kind"] == "general"
    assert "governance" in by_id and by_id["governance"]["kind"] == "governance"
    # One auto channel per taskset.
    assert "demo" in by_id and by_id["demo"]["kind"] == "taskset"
    assert by_id["demo"]["task_set_id"] == "TASKSET-AR-DEMO"

    # Threads are per-task inside the taskset channel.
    demo_threads = {thread["id"]: thread for thread in by_id["demo"]["threads"]}
    assert "TASK-AR-900" in demo_threads
    assert demo_threads["TASK-AR-900"]["task_id"] == "TASK-AR-900"
    assert len(demo_threads["TASK-AR-900"]["messages"]) == 1

    # Governance-intent message lands in #governance; chat lands in #general.
    assert by_id["governance"]["message_count"] == 1
    assert by_id["general"]["message_count"] == 1

    # Owner input affordances expose meeting/seminar slash commands.
    slash = {entry["command"]: entry["type"] for entry in channels["owner_input"]["slash_commands"]}
    assert slash["/meeting"] == "meeting.start"
    assert slash["/seminar"] == "seminar.start"
    assert channels["owner_input"]["mutation_boundary"] == "proposal_only"


def test_ui_state_channels_messages_carry_role_color_and_avatar(tmp_path):
    root = tmp_path
    _channel_message(root, "MSG-9", sender="lead-engineer", to="qa", intent="chat", task_id=None)
    channels = ui_state.build_resource(root, "channels", now="2026-06-12T12:00:00+09:00")["items"]
    general = next(channel for channel in channels["channels"] if channel["id"] == "general")
    message = general["threads"][0]["messages"][0]
    # Role color maps to a known semantic token (no raw hex).
    assert message["role_color"] in channels["role_color_tokens"] or message["role_color"] == "subtle"
    assert message["avatar"]  # avatar initials present
    # Raw body is preserved unescaped here; escaping happens at render time.
    assert message["body"] == "Hello <b>there</b>"


def test_ui_state_channels_empty_repo_is_well_formed(tmp_path):
    channels = ui_state.build_resource(tmp_path, "channels", now="2026-06-12T12:00:00+09:00")["items"]
    by_id = {channel["id"] for channel in channels["channels"]}
    # Even with no messages, #general + #governance exist and the payload is sane.
    assert {"general", "governance"} <= by_id
    assert channels["message_count"] == 0
