import json
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import ui_console
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


def test_ui_state_surfaces_registry_defined_taskset(tmp_path):
    # TASK-AR-329: a UI-created taskset is registered into TASKSET-DEFINITIONS.json
    # via backlog_board.sync_taskset_registry. The console adapter must surface it
    # (display name + summary) exactly as the generated board does, so the UI and
    # the board agree. Use the real backlog_board so _task_set_info_map runs.
    import shutil

    repo_root = Path(__file__).resolve().parents[1]
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(repo_root / "scripts" / "backlog_board.py", tmp_path / "scripts" / "backlog_board.py")

    registry = tmp_path / "agents" / "project" / "work-items" / "TASKSET-DEFINITIONS.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema": "agent-runtime-taskset-definitions/v1",
                "tasksets": [
                    {
                        "task_set_id": "TASKSET-UI-CONSOLE-MADE",
                        "display_name": "Console Made",
                        "summary": "Created from the console UI.",
                        "order": 700,
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-970.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-970",
                "status: planned",
                "owner: lead-engineer",
                "priority: P1",
                "task_set_id: TASKSET-UI-CONSOLE-MADE",
                "---",
                "",
                "## Goal",
                "",
                "Task inside a UI-created taskset.",
            ]
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-12T18:30:00+09:00")
    made = next(ts for ts in state["task_sets"] if ts["id"] == "TASKSET-UI-CONSOLE-MADE")
    assert made["display_name"] == "Console Made"
    assert made["summary"] == "Created from the console UI."


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


# --- Team/role assignment model + workload heatmap (TASK-AR-337) ------------


def _write_teams_md(root: Path) -> None:
    _write(
        root / ui_state.TEAMS_REL,
        "\n".join(
            [
                "# Teams (Host Overlay)",
                "",
                "- team_id: agent-runtime-core",
                "  purpose: runtime",
                "  lead: lead-engineer",
                "  roles:",
                "    - lead-engineer",
                "    - qa",
                "  canonical_context:",
                "    - agents/project/ROADMAP.md",
                "",
                "- team_id: governance-loop",
                "  purpose: governance",
                "  lead: managing-partner",
                "  roles:",
                "    - managing-partner",
                "    - scribe",
                "",
            ]
        ),
    )


def _write_assign_task(root: Path, task_id: str, **fields) -> None:
    lines = ["---", f"id: {task_id}", f"status: {fields.pop('status', 'in_progress')}", "priority: P1"]
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    lines += ["---", "", "## Goal", "", "x", ""]
    _write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md", "\n".join(lines))


def test_ui_state_loads_teams_registry_with_role_index(tmp_path):
    _write_teams_md(tmp_path)
    teams = ui_state.load_teams(tmp_path, "2026-06-13T11:00:00+09:00")
    assert teams["schema"] == ui_state.TEAMS_SCHEMA
    assert teams["freshness"] == "present"
    ids = [team["team_id"] for team in teams["teams"]]
    assert ids == ["agent-runtime-core", "governance-loop"]
    core = teams["teams"][0]
    assert core["lead"] == "lead-engineer"
    assert core["roles"] == ["lead-engineer", "qa"]
    # Reverse role->team index used to resolve assignment.
    assert teams["role_to_team"]["qa"] == "agent-runtime-core"
    assert teams["role_to_team"]["scribe"] == "governance-loop"


def test_ui_state_load_teams_degrades_when_file_missing(tmp_path):
    teams = ui_state.load_teams(tmp_path, "2026-06-13T11:00:00+09:00")
    assert teams["freshness"] == "missing"
    assert teams["teams"] == []
    assert teams["role_to_team"] == {}


def test_ui_state_task_resolves_team_from_explicit_field(tmp_path):
    _write_teams_md(tmp_path)
    _write_assign_task(tmp_path, "TASK-AR-001", team="governance-loop", owner="qa")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    task = state["tasks"][0]
    # Explicit team frontmatter wins over the role-derived team.
    assert task["assigned_team"] == "governance-loop"
    assert task["assignment_source"] == "task_team"


def test_ui_state_task_resolves_team_from_role(tmp_path):
    _write_teams_md(tmp_path)
    _write_assign_task(tmp_path, "TASK-AR-001", owner="qa")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    task = state["tasks"][0]
    assert task["assigned_role"] == "qa"
    assert task["assigned_team"] == "agent-runtime-core"
    assert task["assignment_source"] == "role"


def test_ui_state_taskset_team_default_inherited_by_unassigned_task(tmp_path):
    _write_teams_md(tmp_path)
    # One sibling names a role (qa -> agent-runtime-core); the other names no
    # team/role and must inherit the taskset's default team.
    _write_assign_task(tmp_path, "TASK-AR-001", task_set_id="TASKSET-AR-X", owner="qa")
    _write_assign_task(tmp_path, "TASK-AR-002", task_set_id="TASKSET-AR-X", owner="unknown-role")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    defaults = state["teams"]["taskset_defaults"]
    assert defaults["TASKSET-AR-X"] == "agent-runtime-core"
    inherited = next(t for t in state["tasks"] if t["id"] == "TASK-AR-002")
    assert inherited["assigned_team"] == "agent-runtime-core"
    assert inherited["assignment_source"] == "taskset_default"


def test_ui_state_workload_heatmap_aggregates_agent_and_team_load(tmp_path):
    _write_teams_md(tmp_path)
    # qa agent gets 4 open tasks in one period -> overload band (> busy_max=3).
    _write_assign_task(tmp_path, "TASK-AR-001", owner="qa", due="2026-06-10")
    _write_assign_task(tmp_path, "TASK-AR-002", owner="qa", due="2026-06-11")
    _write_assign_task(tmp_path, "TASK-AR-003", owner="qa", due="2026-06-12")
    _write_assign_task(tmp_path, "TASK-AR-005", owner="qa", due="2026-06-12")
    # A completed task must NOT count toward load.
    _write_assign_task(tmp_path, "TASK-AR-004", owner="qa", due="2026-06-12", status="completed")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    workload = state["workload"]
    assert workload["schema"] == ui_state.WORKLOAD_HEATMAP_SCHEMA
    assert workload["periods"] == ["2026-06"]
    qa_row = next(row for row in workload["agents"] if row["id"] == "qa")
    assert qa_row["open_total"] == 4
    cell = qa_row["cells"][0]
    assert cell["load"] == 4
    assert cell["band"] == "overload"
    assert "TASK-AR-004" not in cell["task_ids"]  # completed excluded
    # Intensity is a normalized 0..1 ratio (max_load drives it).
    assert cell["intensity"] == 1.0
    # Team rollup mirrors the agent load for the resolved team.
    team_row = next(row for row in workload["teams"] if row["id"] == "agent-runtime-core")
    assert team_row["open_total"] == 4
    assert workload["totals"]["overloaded"] >= 1


def test_ui_state_workload_idle_band_for_no_open_tasks(tmp_path):
    _write_teams_md(tmp_path)
    payload = ui_state.build_resource(tmp_path, "workload", now="2026-06-13T11:00:00+09:00")
    assert payload["resource"] == "workload"
    items = payload["items"]
    assert items["schema"] == ui_state.WORKLOAD_HEATMAP_SCHEMA
    assert items["agents"] == []
    assert items["totals"]["open_tasks"] == 0


def test_ui_state_assignment_consistent_across_heatmap_and_filter(tmp_path):
    # Acceptance: the team a task resolves to is the SAME in the task record
    # (board filter source) and in the workload heatmap aggregation.
    _write_teams_md(tmp_path)
    _write_assign_task(tmp_path, "TASK-AR-001", owner="qa", due="2026-06-12")
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    task = state["tasks"][0]
    team_rows = {row["id"] for row in state["workload"]["teams"]}
    assert task["assigned_team"] in team_rows


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


# ----- TASK-AR-330: subtask + dependency model, timeline, dependency graph -----

def _dep_task(
    task_id: str,
    *,
    status: str = "planned",
    parent_id: str | None = None,
    blocks: list[str] | None = None,
    blocked_by: list[str] | None = None,
) -> str:
    lines = ["---", f"id: {task_id}", f"status: {status}", "owner: lead-engineer"]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
    if blocks:
        lines.append("blocks:")
        lines.extend(f"  - {dep}" for dep in blocks)
    if blocked_by:
        lines.append("blocked_by:")
        lines.extend(f"  - {dep}" for dep in blocked_by)
    lines += ["---", "", "## Goal", "", f"Work {task_id}.", ""]
    return "\n".join(lines)


def test_ui_state_load_tasks_parses_parent_blocks_and_blocked_by(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md",
        _dep_task("TASK-AR-900", parent_id="TASKSET-AR-DEP", blocks=["TASK-AR-901"]),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        _dep_task("TASK-AR-901", parent_id="TASKSET-AR-DEP", blocked_by=["TASK-AR-900"]),
    )
    tasks = {t["id"]: t for t in ui_state.build_resource(tmp_path, "tasks", now="2026-06-13T00:00:00+09:00")["items"]}
    assert tasks["TASK-AR-900"]["parent_id"] == "TASKSET-AR-DEP"
    assert tasks["TASK-AR-900"]["blocks"] == ["TASK-AR-901"]
    assert tasks["TASK-AR-901"]["blocked_by"] == ["TASK-AR-900"]
    # Empty/missing keys degrade to empty lists, not None.
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902.md",
        _dep_task("TASK-AR-902"),
    )
    bare = next(
        t for t in ui_state.build_resource(tmp_path, "tasks", now="2026-06-13T00:00:00+09:00")["items"]
        if t["id"] == "TASK-AR-902"
    )
    assert bare["blocks"] == [] and bare["blocked_by"] == [] and bare["parent_id"] == ""


def test_ui_state_dependency_graph_derives_consistent_edges(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md",
        _dep_task("TASK-AR-900", parent_id="TASKSET-AR-DEP", blocks=["TASK-AR-901"]),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        _dep_task("TASK-AR-901", parent_id="TASKSET-AR-DEP", blocked_by=["TASK-AR-900"]),
    )
    payload = ui_state.build_resource(tmp_path, "dependency_graph", now="2026-06-13T00:00:00+09:00")
    graph = payload["items"]
    assert payload["resource"] == "dependency_graph"
    assert graph["schema"] == "agent-runtime-dependency-graph/v1"
    dep_edges = [e for e in graph["edges"] if e["kind"] == "dependency"]
    parent_edges = [e for e in graph["edges"] if e["kind"] == "parent"]
    # blocks + blocked_by both fold into a single deduped blocker->blocked edge.
    assert len(dep_edges) == 1
    assert dep_edges[0]["from"] == "TASK-AR-900" and dep_edges[0]["to"] == "TASK-AR-901"
    # Subtask hierarchy edges from parent_id.
    assert {(e["from"], e["to"]) for e in parent_edges} == {
        ("TASKSET-AR-DEP", "TASK-AR-900"),
        ("TASKSET-AR-DEP", "TASK-AR-901"),
    }
    assert graph["has_cycle"] is False
    assert graph["cycles"] == []


def test_ui_state_dependency_graph_and_timeline_flag_cycle(tmp_path):
    # A <- blocks - B <- blocks - C <- blocks - A  forms a 3-cycle.
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md",
           _dep_task("TASK-AR-900", blocks=["TASK-AR-901"]))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
           _dep_task("TASK-AR-901", blocks=["TASK-AR-902"]))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902.md",
           _dep_task("TASK-AR-902", blocks=["TASK-AR-900"]))
    state = ui_state.build_state(tmp_path, now="2026-06-13T00:00:00+09:00")
    graph = state["dependency_graph"]
    timeline = state["timeline"]
    assert graph["has_cycle"] is True
    assert timeline["has_cycle"] is True
    # Graph and timeline report the same cycle membership.
    cycle_nodes = {n for cycle in graph["cycles"] for n in cycle}
    assert {"TASK-AR-900", "TASK-AR-901", "TASK-AR-902"} <= cycle_nodes
    in_cycle_edges = [e for e in graph["edges"] if e.get("in_cycle")]
    assert len(in_cycle_edges) == 3
    # The pure cycle detector agrees and is empty on an empty edge set.
    assert ui_state.detect_dependency_cycles([]) == []


def test_ui_state_timeline_groups_bars_by_taskset_with_arrows(tmp_path):
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md",
        _dep_task("TASK-AR-900", status="completed", parent_id="TASKSET-AR-DEP", blocks=["TASK-AR-901"]),
    )
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901.md",
        _dep_task("TASK-AR-901", status="in_progress", parent_id="TASKSET-AR-DEP", blocked_by=["TASK-AR-900"]),
    )
    payload = ui_state.build_resource(tmp_path, "timeline", now="2026-06-13T00:00:00+09:00")
    timeline = payload["items"]
    assert payload["resource"] == "timeline"
    assert timeline["schema"] == "agent-runtime-timeline/v1"
    lanes = {lane["id"]: lane for lane in timeline["lanes"]}
    assert "TASKSET-AR-DEP" in lanes
    bars = {bar["id"]: bar for bar in lanes["TASKSET-AR-DEP"]["bars"]}
    assert set(bars) == {"TASK-AR-900", "TASK-AR-901"}
    assert bars["TASK-AR-900"]["status_bucket"] == "completed"
    assert bars["TASK-AR-901"]["status_bucket"] == "in_progress"
    # Bars carry distinct lane columns so they render as horizontal positions.
    assert bars["TASK-AR-900"]["start"] != bars["TASK-AR-901"]["start"]
    # Exactly one dependency arrow, matching the graph derivation.
    assert len(timeline["arrows"]) == 1
    arrow = timeline["arrows"][0]
    assert arrow["from"] == "TASK-AR-900" and arrow["to"] == "TASK-AR-901"


def test_ui_state_dependency_views_empty_when_no_deps(tmp_path):
    # No blocks/blocked_by anywhere -> no dependency edges, no cycle (no-op safe).
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900.md", _dep_task("TASK-AR-900"))
    state = ui_state.build_state(tmp_path, now="2026-06-13T00:00:00+09:00")
    assert state["dependency_graph"]["totals"]["dependency_edges"] == 0
    assert state["dependency_graph"]["has_cycle"] is False
    assert state["timeline"]["totals"]["arrows"] == 0
    assert state["timeline"]["has_cycle"] is False


# ---------------------------------------------------------------------------
# Global search + quick open (TASK-AR-334)
# ---------------------------------------------------------------------------


def _seed_search_corpus(root: Path) -> None:
    """Seed one of every searchable entity type so the index covers >=5 kinds."""
    _write(
        root / "agents" / "lead_engineer" / "tasks" / "TASK-AR-334.md",
        "\n".join(
            [
                "---",
                "id: TASK-AR-334",
                "title: Global search and quick open",
                "status: blocked",
                "owner: lead-engineer",
                "priority: P1",
                "task_set_id: TASKSET-AR-UI",
                "updated_at: 2026-06-12T10:00:00+09:00",
                "audit_log:",
                "  - commit 47d8e97 registered the overlay task",
                "tags:",
                "  - search",
                "---",
                "",
                "## Goal",
                "",
                "Full-text search across entities with operators.",
                "",
            ]
        ),
    )
    _write(
        root / "agents" / "runtime" / "events" / "qa-2026-06-12.jsonl",
        json.dumps(
            {
                "ts": "2026-06-12T11:00:00+09:00",
                "role": "qa",
                "event": "search.indexed",
                "task_id": "TASK-AR-334",
                "goal_id": "goal-334",
                "evidence": ["reviews/search-evidence.md"],
            }
        )
        + "\n",
    )
    _write(
        root / "agents" / "messages" / "inbox" / "MSG-20260612-search.md",
        "\n".join(
            [
                "---",
                "id: MSG-20260612-search",
                "from: qa",
                "to: lead-engineer",
                "type: review",
                "status: queued",
                "ts: 2026-06-12T11:05:00+09:00",
                "intent: search-review",
                "task_id: TASK-AR-334",
                "evidence: reviews/search-message.md",
                "---",
                "",
                "Please review the search index payload.",
                "",
            ]
        ),
    )
    _write(
        root / "reviews" / "MEETING-2026-06-12-search-design.md",
        "\n".join(
            [
                "---",
                "type: meeting",
                "id: MEETING-2026-06-12-search-design",
                "title: Search design review",
                "status: pass",
                "tags: [search, ui]",
                "generated_at: 2026-06-12T12:00:00+09:00",
                "---",
                "",
                "# Search Design Review",
                "",
                "## Bottom Line",
                "",
                "- Reviewed TASK-AR-334 search design; landed on commit 56c9c71.",
                "",
            ]
        ),
    )


def test_ui_state_search_index_covers_at_least_five_entity_types(tmp_path):
    _seed_search_corpus(tmp_path)
    state = ui_state.build_state(tmp_path, now="2026-06-12T12:30:00+09:00")
    index = state["search_index"]
    types = {entry["entity_type"] for entry in index}
    # >=5 entity types from a single corpus (acceptance criterion).
    expected = {"task", "taskset", "message", "event", "evidence", "review"}
    assert expected.issubset(types), f"missing entity types: {expected - types}"
    assert len(types) >= 5
    # search_index is exposed as a first-class resource.
    payload = ui_state.build_resource(tmp_path, "search_index", now="2026-06-12T12:30:00+09:00")
    assert payload["resource"] == "search_index"
    assert len(payload["items"]) == len(index)


def test_ui_state_run_search_returns_five_plus_types_for_single_query(tmp_path):
    _seed_search_corpus(tmp_path)
    state = ui_state.build_state(tmp_path, now="2026-06-12T12:30:00+09:00")
    # One query ("search") matches task/taskset?/message/event/evidence/review.
    results = ui_state.run_search(state["search_index"], "search")
    types = {r["entity_type"] for r in results}
    assert len(types) >= 5, f"single query returned too few types: {types}"
    # Every result carries an AR-321 hash deep-link target with a select param.
    for r in results:
        assert r["deep_link"].startswith("#/")
        assert r["route"] in ui_state.SEARCH_ENTITY_ROUTES.values()


def test_ui_state_parse_search_query_operators(tmp_path):
    parsed = ui_state.parse_search_query('type:task status:blocked owner:lead-engineer date:2026-06-12 quick open')
    assert parsed["operators"] == {
        "type": "task",
        "status": "blocked",
        "owner": "lead-engineer",
        "date": "2026-06-12",
    }
    assert parsed["terms"] == ["quick", "open"]
    # Quoted operator values keep spaces.
    quoted = ui_state.parse_search_query('owner:"lead engineer" hello')
    assert quoted["operators"]["owner"] == "lead engineer"
    assert quoted["terms"] == ["hello"]
    # Unknown key:value tokens stay as free text (still matched literally).
    unknown = ui_state.parse_search_query("foo:bar baz")
    assert unknown["operators"] == {}
    assert "foo:bar" in unknown["terms"]


def test_ui_state_run_search_applies_type_status_owner_date_operators(tmp_path):
    _seed_search_corpus(tmp_path)
    state = ui_state.build_state(tmp_path, now="2026-06-12T12:30:00+09:00")
    index = state["search_index"]

    by_type = ui_state.run_search(index, "type:task")
    assert by_type and all(r["entity_type"] == "task" for r in by_type)

    by_status = ui_state.run_search(index, "type:task status:blocked")
    assert by_status and all(r["status"] == "blocked" for r in by_status)
    assert any(r["id"] == "TASK-AR-334" for r in by_status)

    by_owner = ui_state.run_search(index, "type:task owner:lead-engineer")
    assert by_owner and all("lead-engineer" in (r["owner"] or "") for r in by_owner)

    by_date = ui_state.run_search(index, "date:2026-06-12")
    assert by_date and all((r["date"] or "").startswith("2026-06-12") for r in by_date)


def test_ui_state_search_results_surface_related_commit_and_review_links(tmp_path):
    _seed_search_corpus(tmp_path)
    state = ui_state.build_state(tmp_path, now="2026-06-12T12:30:00+09:00")
    index = state["search_index"]
    task = next(e for e in index if e["entity_type"] == "task" and e["id"] == "TASK-AR-334")
    labels = " ".join(str(rel) for rel in task["related"])
    # Related links surface the review doc mentioning the task and the commit SHA.
    assert any("path" in rel and "MEETING" in rel.get("path", "") for rel in task["related"]) or "MEETING" in labels
    assert any(rel.get("sha") == "47d8e97" for rel in task["related"])


def test_ui_state_run_search_query_is_tokenization_safe(tmp_path):
    _seed_search_corpus(tmp_path)
    state = ui_state.build_state(tmp_path, now="2026-06-12T12:30:00+09:00")
    index = state["search_index"]
    # Malicious / regex-special / unicode input must not raise and must filter.
    for hostile in ['<script>alert(1)</script>', 'a"b)(*&^', 'type:task ".*"', '한국어 검색', '   ']:
        results = ui_state.run_search(index, hostile)
        assert isinstance(results, list)


# ----- TASK-AR-336: interactive state-machine viewer (data layer) -----

# A trimmed STATE-MACHINES.yml that still carries the three lifecycle machines
# named in the task (task / claim / role), full state metadata and a wildcard
# transition, so the viewer derivation can be exercised end to end.
_STATE_MACHINES_FIXTURE = "\n".join(
    [
        "schema: agent-runtime-state-machines/v1",
        "version: 1",
        "machines:",
        "  - id: task",
        "    scope: backlog_task",
        "    owner: lead-engineer",
        "    initial: planned",
        "    states:",
        "      - id: planned",
        "        signal: watch",
        "        score: 70",
        "      - id: in_progress",
        "        signal: watch",
        "        score: 80",
        "      - id: blocked",
        "        signal: block",
        "        score: 30",
        "      - id: completed",
        "        signal: pass",
        "        score: 95",
        "      - id: archived",
        "        signal: pass",
        "        score: 100",
        "    transitions:",
        "      - from: planned",
        "        to: in_progress",
        "        trigger: agent_claimed",
        "      - from: in_progress",
        "        to: blocked",
        "        trigger: blocker_found",
        "      - from: in_progress",
        "        to: completed",
        "        trigger: done_criteria_met",
        "      - from: completed",
        "        to: archived",
        "        trigger: evidence_linked",
        "  - id: task_claim",
        "    scope: parallel_agent_task_lease",
        "    owner: agent-runtime-core",
        "    initial: unclaimed",
        "    states:",
        "      - id: unclaimed",
        "        signal: pass",
        "        score: 90",
        "      - id: claimed",
        "        signal: watch",
        "        score: 75",
        "      - id: stale",
        "        signal: watch",
        "        score: 55",
        "    transitions:",
        "      - from: unclaimed",
        "        to: claimed",
        "        trigger: task_claim_record_written",
        '      - from: "*"',
        "        to: stale",
        "        trigger: heartbeat_expired",
        "  - id: agent_job",
        "    scope: agent_execution",
        "    owner: agent-runtime-core",
        "    initial: idle",
        "    states:",
        "      - id: idle",
        "        signal: pass",
        "        score: 90",
        "      - id: working",
        "        signal: watch",
        "        score: 80",
        "    transitions:",
        "      - from: idle",
        "        to: working",
        "        trigger: scope_clear",
    ]
)


def _started_then_blocked_events():
    return [
        {"task_id": "TASK-AR-900", "event": "task_started", "ts": "2026-06-12T10:00:00+09:00"},
        {"task_id": "TASK-AR-900", "event": "task_blocked", "ts": "2026-06-12T11:00:00+09:00"},
        {"task_id": "TASK-AR-900", "event": "task_unblocked_resume", "ts": "2026-06-12T12:00:00+09:00"},
    ]


def test_state_machines_every_defined_machine_renders_nodes_and_edges(tmp_path):
    # Acceptance: every machine defined in STATE-MACHINES.yml renders nodes+edges.
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    assert {m["id"] for m in machines} == {"task", "task_claim", "agent_job"}
    for machine in machines:
        assert machine["state_nodes"], f"{machine['id']} must have state nodes"
        assert machine["transition_edges"], f"{machine['id']} must have transition edges"
        assert machine["totals"]["states"] == len(machine["state_nodes"])
        assert machine["totals"]["transitions"] == len(machine["transition_edges"])
        # The declared initial is flagged on exactly one node.
        initial_nodes = [n for n in machine["state_nodes"] if n["is_initial"]]
        assert len(initial_nodes) == 1
        assert initial_nodes[0]["id"] == machine["initial"]


def test_state_machines_canonical_file_all_machines_render(tmp_path):
    # Render the SHIPPED STATE-MACHINES.yml (SSoT) so a new machine added there
    # is guaranteed to render without code changes.
    repo_yaml = Path(__file__).resolve().parents[1] / "agents" / "project" / "STATE-MACHINES.yml"
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", repo_yaml.read_text(encoding="utf-8"))
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    assert len(machines) >= 3
    for machine in machines:
        assert machine["state_nodes"], f"{machine['id']} renders no states"
        assert machine["transition_edges"], f"{machine['id']} renders no transitions"


def test_state_machines_state_nodes_carry_signal_token_and_score(tmp_path):
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    task = next(m for m in machines if m["id"] == "task")
    by_id = {n["id"]: n for n in task["state_nodes"]}
    assert by_id["completed"]["signal"] == "pass"
    assert by_id["completed"]["signal_token"] == "success"
    assert by_id["completed"]["score"] == 95
    assert by_id["blocked"]["signal_token"] == "danger"
    assert by_id["planned"]["signal_token"] == "warning"


def test_state_machines_wildcard_transition_is_flagged_and_expanded(tmp_path):
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    claim = next(m for m in machines if m["id"] == "task_claim")
    wildcard_edges = [e for e in claim["transition_edges"] if e["wildcard"]]
    assert len(wildcard_edges) == 1
    edge = wildcard_edges[0]
    assert edge["to"] == "stale"
    assert edge["from"] == "*"
    # Wildcard sources are every state except the target itself.
    assert "stale" not in edge["wildcard_sources"]
    assert set(edge["wildcard_sources"]) == {"unclaimed", "claimed"}


def test_state_machines_task_current_state_identified_in_graph(tmp_path):
    # Acceptance: an arbitrary task's current state is identifiable in the graph.
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    tasks = [{"id": "TASK-AR-900", "status": "in_progress", "title": "demo", "source_path": "x.md"}]
    machines = ui_state.load_state_machines(tmp_path, tasks, [], now="2026-06-13T00:00:00+09:00", events=[])
    task = next(m for m in machines if m["id"] == "task")
    assert "TASK-AR-900" in task["task_states"]
    info = task["task_states"]["TASK-AR-900"]
    assert info["current_state"] == "in_progress"
    # The current state is a real node id in the rendered graph.
    assert info["current_state"] in {n["id"] for n in task["state_nodes"]}


def test_state_machines_traversed_path_derived_from_event_log(tmp_path):
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    tasks = [{"id": "TASK-AR-900", "status": "in_progress", "title": "demo", "source_path": "x.md"}]
    machines = ui_state.load_state_machines(
        tmp_path, tasks, [], now="2026-06-13T00:00:00+09:00", events=_started_then_blocked_events()
    )
    task = next(m for m in machines if m["id"] == "task")
    info = task["task_states"]["TASK-AR-900"]
    # Event log: started -> blocked -> resumed; status seeds in_progress current.
    assert info["state_sequence"][0] == "planned"  # initial seed
    assert "blocked" in info["state_sequence"]
    assert info["current_state"] == "in_progress"
    # The traversed transition path references real edge ids from the graph.
    edge_ids = {e["id"] for e in task["transition_edges"]}
    path_ids = [hop["id"] for hop in info["transition_path"]]
    assert path_ids, "expected a non-empty traversed path"
    for hop in info["transition_path"]:
        # Either an explicit edge in the graph or a wildcard fallback edge id.
        assert hop["id"] in edge_ids or hop["wildcard"]
    # The planned->in_progress claim hop is the first traversal.
    assert info["transition_path"][0]["from"] == "planned"
    assert info["transition_path"][0]["to"] == "in_progress"


def test_state_machines_missing_file_returns_empty_no_crash(tmp_path):
    # Graceful when STATE-MACHINES.yml is missing entirely.
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    assert machines == []
    payload = ui_state.build_resource(tmp_path, "state_machines", now="2026-06-13T00:00:00+09:00")
    assert payload["resource"] == "state_machines"
    assert payload["items"] == []


def test_state_machines_empty_file_returns_empty_no_crash(tmp_path):
    # Graceful when the file exists but defines no machines.
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", "schema: x\nversion: 1\nmachines:\n")
    machines = ui_state.load_state_machines(tmp_path, [], [], now="2026-06-13T00:00:00+09:00", events=[])
    assert machines == []


def test_state_machines_build_state_wires_events_into_task_states(tmp_path):
    # End-to-end through build_state: the task machine carries per-task overlays
    # derived from the event log without an explicit events argument.
    _write(tmp_path / "agents" / "project" / "STATE-MACHINES.yml", _STATE_MACHINES_FIXTURE)
    _write(
        tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900-demo.md",
        _task_text("TASK-AR-900", status="in_progress"),
    )
    _write(
        tmp_path / "agents" / "runtime" / "events" / "lead-engineer-2026-06-12.jsonl",
        "\n".join(json.dumps(ev) for ev in _started_then_blocked_events()) + "\n",
    )
    state = ui_state.build_state(tmp_path, now="2026-06-13T00:00:00+09:00")
    task = next(m for m in state["state_machines"] if m["id"] == "task")
    assert "TASK-AR-900" in task["task_states"]
    assert task["task_states"]["TASK-AR-900"]["current_state"] == "in_progress"
    assert any(hop["to"] == "blocked" for hop in task["task_states"]["TASK-AR-900"]["transition_path"])


# ----- TASK-AR-339: ops dashboard metrics -----


def _write_token_task(
    root: Path,
    task_id: str,
    *,
    task_set_id: str,
    est_tokens: int,
    status: str = "in_progress",
    actual_tokens: int | None = None,
    completed_at: str | None = None,
) -> None:
    lines = [
        "---",
        f"id: {task_id}",
        f"status: {status}",
        "owner: lead-engineer",
        "priority: P1",
        f"task_set_id: {task_set_id}",
        f"est_tokens: {est_tokens}",
    ]
    if actual_tokens is not None:
        lines.append(f"actual_tokens: {actual_tokens}")
    if completed_at is not None:
        lines.append(f"completed_at: {completed_at}")
    lines += ["tags: []", "---", "", "## Goal", "", "x", ""]
    _write(root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md", "\n".join(lines))


def _write_gate_json(root: Path, name: str, status: str, *, schema: str, task_ref: str = "") -> None:
    payload = {"schema": schema, "status": status, "score": 1.0, "findings": []}
    if task_ref:
        payload["task_ref"] = task_ref
    _write(root / "reviews" / name, json.dumps(payload))


def test_ui_state_ops_metrics_aggregates_tokens_est_vs_actual_and_budget(tmp_path):
    # est_tokens always counts; actual_tokens only when present. Per-taskset
    # budget == sum of member estimates; consumed% derives from actuals.
    _write_token_task(tmp_path, "TASK-AR-001", task_set_id="TASKSET-AR-X", est_tokens=4000, actual_tokens=2000)
    _write_token_task(tmp_path, "TASK-AR-002", task_set_id="TASKSET-AR-X", est_tokens=6000)
    _write_token_task(tmp_path, "TASK-AR-003", task_set_id="TASKSET-AR-Y", est_tokens=1000)
    state = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")
    ops = state["ops_metrics"]
    assert ops["schema"] == ui_state.OPS_METRICS_SCHEMA
    res = ops["resources"]
    assert res["est_tokens"] == 11000
    assert res["actual_tokens"] == 2000
    assert res["has_actuals"] is True
    assert res["actuals_label"] == "actual"
    # Cost is a transparent linear derivation, not billing actuals.
    assert res["est_cost"] == ui_state._ops_cost(11000)
    x_row = next(r for r in res["tasksets"] if r["task_set_id"] == "TASKSET-AR-X")
    assert x_row["est_tokens"] == 10000
    assert x_row["budget_tokens"] == 10000
    assert x_row["actual_tokens"] == 2000
    assert x_row["tasks_with_actual"] == 1
    # 2000 actual / 10000 budget => 20% consumed.
    assert x_row["consumed_pct"] == 20.0
    assert x_row["over_budget"] is False
    y_row = next(r for r in res["tasksets"] if r["task_set_id"] == "TASKSET-AR-Y")
    # No actuals in Y => est-only (consumed_pct None).
    assert y_row["consumed_pct"] is None


def test_ui_state_ops_metrics_est_only_label_when_no_actuals(tmp_path):
    _write_token_task(tmp_path, "TASK-AR-010", task_set_id="TASKSET-AR-Z", est_tokens=5000)
    ops = ui_state.build_resource(tmp_path, "ops_metrics", now="2026-06-13T11:00:00+09:00")["items"]
    res = ops["resources"]
    assert res["has_actuals"] is False
    assert res["actuals_label"] == "estimate-only"
    assert res["actual_tokens"] == 0


def test_ui_state_ops_metrics_eval_trend_from_evidence(tmp_path):
    # Two offline-eval reports + one live-reviewer gate => an ordered score trend.
    _write(
        tmp_path / "reviews" / "OFFLINE-EVAL-2026-06-09-task-ar-217.json",
        json.dumps({"schema": "agent-runtime-offline-eval-report/v1", "status": "pass",
                    "minimum_score_by_domain": 0.9, "score": 0.95,
                    "generated_at": "2026-06-09T10:00:00+00:00", "task_ref": "TASK-AR-217"}),
    )
    _write(
        tmp_path / "reviews" / "OFFLINE-EVAL-2026-06-10-task-ar-217.json",
        json.dumps({"schema": "agent-runtime-offline-eval-report/v1", "status": "pass",
                    "score": 1.0, "generated_at": "2026-06-10T10:00:00+00:00"}),
    )
    _write(
        tmp_path / "agents" / "project" / "evidence" / "evaluations" / "provider-live.json",
        json.dumps({"schema": "agent-runtime-provider-live-eval/v1", "status": "watch",
                    "metric_value": 0.8, "generated_at": "2026-06-11T10:00:00+00:00",
                    "task_ref": "TASK-AR-315"}),
    )
    ops = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")["ops_metrics"]
    trend = ops["eval_trend"]
    assert trend["available"] is True
    assert trend["count"] == 3
    # Ordered by generated_at; latest is the provider-live watch point.
    assert [round(p["score"], 2) for p in trend["points"]] == [0.95, 1.0, 0.8]
    assert trend["latest_score"] == 0.8
    assert trend["latest_status"] == "watch"
    assert trend["min_score"] == 0.8
    assert trend["max_score"] == 1.0


def test_ui_state_ops_metrics_eval_trend_graceful_when_absent(tmp_path):
    _write_token_task(tmp_path, "TASK-AR-020", task_set_id="TASKSET-AR-Z", est_tokens=100)
    ops = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")["ops_metrics"]
    trend = ops["eval_trend"]
    assert trend["available"] is False
    assert trend["points"] == []
    assert trend["latest_score"] is None


def test_ui_state_ops_metrics_gate_board_pass_watch_block(tmp_path):
    _write_gate_json(tmp_path, "CO-LOCATION-GATE-a.json", "pass", schema="agent-runtime-co-location-gate/v1")
    _write_gate_json(tmp_path, "LIVE-REVIEWER-GATE-b.json", "block", schema="agent-runtime-live-reviewer-gate/v1", task_ref="TASK-AR-207")
    _write_gate_json(tmp_path, "OFFLINE-EVAL-GATE-c.json", "watch", schema="agent-runtime-offline-eval-gate/v1")
    ops = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")["ops_metrics"]
    board = ops["gates"]
    assert board["total"] == 3
    assert board["counts"]["pass"] == 1
    assert board["counts"]["watch"] == 1
    assert board["counts"]["block"] == 1
    assert board["blocking"] == 1
    # Block sorts first so the operator sees failures at the top.
    assert board["gates"][0]["status"] == "block"
    assert board["gates"][0]["task_ref"] == "TASK-AR-207"
    assert board["gates"][0]["kind"] == "live-reviewer-gate"


def test_ui_state_ops_metrics_burndown_and_weekly_velocity(tmp_path):
    # Two done (in distinct ISO weeks) + one open across one taskset.
    _write_token_task(tmp_path, "TASK-AR-101", task_set_id="TASKSET-AR-B", est_tokens=100,
                      status="completed", completed_at="2026-06-01T10:00:00+00:00")
    _write_token_task(tmp_path, "TASK-AR-102", task_set_id="TASKSET-AR-B", est_tokens=100,
                      status="completed", completed_at="2026-06-09T10:00:00+00:00")
    _write_token_task(tmp_path, "TASK-AR-103", task_set_id="TASKSET-AR-B", est_tokens=100,
                      status="in_progress")
    ops = ui_state.build_state(tmp_path, now="2026-06-13T11:00:00+09:00")["ops_metrics"]
    burn = ops["burndown"]
    assert burn["total"] == 3
    assert burn["done"] == 2
    assert burn["remaining"] == 1
    assert burn["pct_done"] == round((2 / 3) * 100, 1)
    ts_row = next(r for r in burn["tasksets"] if r["task_set_id"] == "TASKSET-AR-B")
    assert ts_row["total"] == 3 and ts_row["done"] == 2 and ts_row["remaining"] == 1
    vel = ops["velocity"]
    assert vel["available"] is True
    # Two completions in two different ISO weeks.
    assert vel["total_done"] == 2
    assert len(vel["weeks"]) == 2
    assert {w["done"] for w in vel["weeks"]} == {1}


def test_ui_state_ops_metrics_in_resource_names_and_resource_endpoint(tmp_path):
    assert "ops_metrics" in ui_state.RESOURCE_NAMES
    payload = ui_state.build_resource(tmp_path, "ops_metrics", now="2026-06-13T11:00:00+09:00")
    assert payload["resource"] == "ops_metrics"
    assert payload["items"]["schema"] == ui_state.OPS_METRICS_SCHEMA


# --- TASK-AR-338: notification center + @mentions + daily brief --------------

AR338_NOW = "2026-06-14T10:00:00+09:00"


def _ar338_task(task_id, *, status="in_progress", task_set_id="TASKSET-AR-X", **extra):
    lines = [
        "---",
        f"id: {task_id}",
        f"status: {status}",
        "owner: lead-engineer",
        "priority: P0",
        f"task_set_id: {task_set_id}",
    ]
    for key, value in extra.items():
        lines.append(f"{key}: {value}")
    lines += ["created: 2026-06-14", "---", "", "## Goal", "", "Do a thing.", ""]
    return "\n".join(lines)


def _ar338_message(message_id, body, *, sender="owner", task_id="TASK-AR-900", ts="2026-06-14T09:00:00+09:00"):
    return "\n".join(
        [
            "---",
            f"id: {message_id}",
            f"from: {sender}",
            "to: lead-engineer",
            "type: instruction",
            f"ts: {ts}",
            f"task_id: {task_id}",
            "---",
            "",
            body,
            "",
        ]
    )


def _ar338_seed(tmp_path):
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900-x.md",
           _ar338_task("TASK-AR-900", status="blocked", blocked_reason="waiting on review"))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-901-y.md",
           _ar338_task("TASK-AR-901", status="planned"))
    _write(tmp_path / "agents" / "messages" / "inbox" / "MSG-1.md",
           _ar338_message("MSG-1", "Hey @lead-engineer please look, and @owner FYI"))


def test_notifications_aggregate_events_reminders_mentions_with_severity(tmp_path):
    _ar338_seed(tmp_path)
    state = ui_state.build_state(tmp_path, now=AR338_NOW)
    notifications = state["notifications"]
    assert notifications["schema"] == ui_state.NOTIFICATIONS_SCHEMA
    kinds = {item["kind"] for item in notifications["notifications"]}
    assert "blocked" in kinds
    assert "mention" in kinds
    blocked = next(item for item in notifications["notifications"] if item["kind"] == "blocked")
    assert blocked["severity"] == "blocked"
    assert blocked["task_id"] == "TASK-AR-900"
    # Blocked notification deep-links to the task (the blocked->notify->deep-link flow).
    assert blocked["deep_link"] == "#/home/board?select=TASK-AR-900"
    # Two distinct mention targets become two mention notifications.
    mentions = sorted(item["mention_target"] for item in notifications["notifications"] if item["kind"] == "mention")
    assert mentions == ["lead-engineer", "owner"]


def test_notifications_consume_calendar_reminders(tmp_path):
    # A task with a near-future due date produces a calendar reminder that the
    # notification center consumes as a due_soon reminder notification.
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-902-due.md",
           _ar338_task("TASK-AR-902", status="in_progress", due="2026-06-15"))
    state = ui_state.build_state(tmp_path, now=AR338_NOW)
    reminders = [item for item in state["notifications"]["notifications"] if item["kind"] == "reminder"]
    assert reminders, "expected a reminder consumed from the calendar"
    assert reminders[0]["severity"] in {"due_soon", "overdue"}


def test_notifications_apply_subscription_mute_keyword_and_read_state(tmp_path):
    _ar338_seed(tmp_path)
    # Subscribe to blocked+mention; mute the blocked task; mark the owner mention
    # read; keyword-mute mentions containing FYI.
    _write(
        tmp_path / ui_state.NOTIFICATIONS_CONFIG_REL,
        json.dumps(
            {
                "subscriptions": {"kinds": ["blocked", "mention"]},
                "mutes": ["TASK-AR-900"],
                "read": ["notif:mention:MSG-1:owner"],
                "keyword_rules": [{"keyword": "FYI", "action": "mute"}],
            }
        ),
    )
    notifications = ui_state.build_notifications(
        [], {"reminders": []},
        ui_state.load_tasks(tmp_path, AR338_NOW, []),
        ui_state.load_messages(tmp_path, AR338_NOW, []),
        ui_state.load_notifications_config(tmp_path, AR338_NOW, []),
        AR338_NOW,
    )
    by_id = {item["id"]: item for item in notifications["notifications"]}
    # Blocked task notification is muted by the explicit task-id mute rule.
    assert by_id["notif:blocked:TASK-AR-900"]["muted"] is True
    # Keyword rule mutes the FYI mention; the owner mention carries FYI + is read.
    assert by_id["notif:mention:MSG-1:owner"]["muted"] is True
    assert by_id["notif:mention:MSG-1:owner"]["read"] is True
    # The inbox excludes muted notifications.
    inbox_ids = {item["id"] for item in notifications["inbox"]}
    assert "notif:blocked:TASK-AR-900" not in inbox_ids


def test_notifications_unsubscribed_kinds_excluded_from_inbox(tmp_path):
    _ar338_seed(tmp_path)
    _write(
        tmp_path / ui_state.NOTIFICATIONS_CONFIG_REL,
        json.dumps({"subscriptions": {"kinds": ["mention"]}}),
    )
    notifications = ui_state.build_notifications(
        [], {"reminders": []},
        ui_state.load_tasks(tmp_path, AR338_NOW, []),
        ui_state.load_messages(tmp_path, AR338_NOW, []),
        ui_state.load_notifications_config(tmp_path, AR338_NOW, []),
        AR338_NOW,
    )
    inbox_kinds = {item["kind"] for item in notifications["inbox"]}
    assert inbox_kinds == {"mention"}
    # The blocked notification still exists in the full list but is not subscribed.
    blocked = next(item for item in notifications["notifications"] if item["kind"] == "blocked")
    assert blocked["subscribed"] is False


def test_notifications_default_config_is_permissive(tmp_path):
    _ar338_seed(tmp_path)
    config = ui_state.load_notifications_config(tmp_path, AR338_NOW, [])
    assert config["config_present"] is False
    notifications = ui_state.build_notifications(
        [], {"reminders": []},
        ui_state.load_tasks(tmp_path, AR338_NOW, []),
        ui_state.load_messages(tmp_path, AR338_NOW, []),
        config,
        AR338_NOW,
    )
    # With no config, every notification is subscribed and unmuted.
    assert all(item["subscribed"] for item in notifications["notifications"])
    assert notifications["totals"]["inbox"] == notifications["totals"]["total"]


def test_notifications_render_is_xss_safe(tmp_path):
    evil_task = _ar338_task("TASK-AR-903", status="blocked")
    evil_task = evil_task.replace("Do a thing.", "irrelevant")
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-903-evil.md", evil_task)
    # Carry the markup in the message body (escaped only at render time).
    _write(tmp_path / "agents" / "messages" / "inbox" / "MSG-evil.md",
           _ar338_message("MSG-evil", "@owner <img src=x onerror=alert(2)> <script>alert(1)</script>"))
    state = ui_state.build_state(tmp_path, now=AR338_NOW)
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    bodies = [item["body"] for item in state["notifications"]["notifications"]]
    # Raw markup survives verbatim in the JSON state (escaped only by escapeHtml
    # at render time)...
    assert any("<script>alert(1)</script>" in body for body in bodies)
    # ...but the served shell never inlines the unescaped markup.
    assert "<img src=x onerror=alert(2)>" not in html
    assert "<script>alert(1)</script>" not in html


def test_daily_brief_summarizes_completed_blocked_decisions_next(tmp_path):
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-900-x.md",
           _ar338_task("TASK-AR-900", status="blocked", blocked_reason="waiting"))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-904-done.md",
           _ar338_task("TASK-AR-904", status="completed", completed_at="2026-06-14T08:00:00+09:00"))
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-AR-905-next.md",
           _ar338_task("TASK-AR-905", status="ready"))
    _write(
        tmp_path / "reviews" / "DECISION-2026-06-14-x.md",
        "\n".join(["---", "id: DECISION-1", "title: Ship it", "type: decision",
                   "date: 2026-06-14", "---", "", "## Bottom Line", "", "We ship.", ""]),
    )
    state = ui_state.build_state(tmp_path, now=AR338_NOW)
    brief = state["daily_brief"]
    assert brief["schema"] == ui_state.DAILY_BRIEF_SCHEMA
    assert brief["date"] == "2026-06-14"
    assert [item["id"] for item in brief["completed"]] == ["TASK-AR-904"]
    assert any(item["id"] == "TASK-AR-900" for item in brief["blocked"])
    assert [item["id"] for item in brief["decisions"]] == ["DECISION-1"]
    next_ids = [item["id"] for item in brief["next_recommended"]]
    assert "TASK-AR-905" in next_ids
    # Completed/blocked tasks are not recommended as next work.
    assert "TASK-AR-904" not in next_ids
    assert "TASK-AR-900" not in next_ids


def test_notifications_and_daily_brief_are_resources(tmp_path):
    _ar338_seed(tmp_path)
    for resource in ("notifications", "daily_brief"):
        payload = ui_state.build_resource(tmp_path, resource, now=AR338_NOW)
        assert payload["resource"] == resource
        assert isinstance(payload["items"], dict)


def test_extract_mentions_dedupes_and_lowercases():
    assert ui_state.extract_mentions("@Owner ping @owner again @lead-engineer") == ["owner", "lead-engineer"]
    assert ui_state.extract_mentions("no mentions here") == []
    # An email-like token must not be treated as a mention.
    assert ui_state.extract_mentions("mail me at a@b.com") == []
