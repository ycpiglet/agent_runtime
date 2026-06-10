---
id: TASK-AR-287
display_id: TASK-AR-287
task_uid: 326fe2d8-f5aa-453c-b1ae-f267fdeda63b
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: ""
updated_at: 2026-06-11T01:45:00+09:00
completed_at: ""
title: Enforce pane lifecycle event logging
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - events
  - lifecycle
---

# TASK-AR-287 - Enforce pane lifecycle event logging

## Goal

- Make pane lifecycle events mandatory enough that UI replay and audits can prove what happened.

## Scope

- Require pane started, claimed, heartbeat, blocked, handoff, released, and closed events for active worker panes.
- Add a gate that compares active claims against append-only pane events.
- Preserve root-orchestrator ownership for shared SSoT writes.
- Keep event writing append-only.

## Acceptance Criteria

- Active claims without pane lifecycle events produce findings.
- Released claims without handoff or close events produce findings.
- Non-orchestrator SSoT write attempts remain blocking.
- UI state can replay pane lifecycle without parsing freeform chat summaries.

## Evidence Targets

- `scripts/pane_event_log.py`
- `scripts/collaboration_concurrency_gate.py`
- `tests/test_pane_event_log.py`
- `tests/test_collaboration_concurrency_gate.py`

