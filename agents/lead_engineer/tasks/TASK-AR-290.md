---
id: TASK-AR-290
display_id: TASK-AR-290
task_uid: 2ce7f36f-3bdf-41b3-9040-f32cc3db4034
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: 2026-06-11T11:53:49+09:00
updated_at: 2026-06-11T11:53:49+09:00
completed_at: 2026-06-11T11:53:49+09:00
title: Surface multi-pane assurance in UI
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 1200
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - ui
  - assurance
---

# TASK-AR-290 - Surface multi-pane assurance in UI

## Goal

- Make multi-pane census, process compliance, role coverage, drift, and event replay visible in the UI.

## Scope

- Add UI state resources for census, process audit, role coverage, drift, and event replay.
- Render a multi-pane assurance panel or section in the runtime console.
- Show pass, watch, block, waived, active, stale, and missing-evidence states.
- Preserve source links back to claims, events, task files, reviews, and gates.

## Acceptance Criteria

- UI can answer whether 5+ panes are active now or only historical.
- UI shows which agents/processes are missing, waived, or underused.
- UI shows stale worktree and heartbeat drift without requiring manual markdown search.
- UI state remains read-only for assurance data.

## Evidence Targets

- `src/agent_runtime/ui_state.py`
- `src/agent_runtime/ui_console.py`
- `tests/test_ui_state.py`
- `tests/test_ui_console.py`
