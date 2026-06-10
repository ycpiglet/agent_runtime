---
id: TASK-AR-253
display_id: TASK-AR-253
task_uid: 485edce3-c9c4-4c41-9a8b-6da311b89f97
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Enforce single-writer SSoT through concurrency gate
status: completed
priority: P0
importance: High
difficulty: M
est_hours: 4
est_tokens: 1100
task_set_id: TASKSET-AR-COLLAB-CONCURRENCY
team: agent-runtime-core
owner: risk-controller
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:20:00+09:00
completed_at: 2026-06-10T23:20:00+09:00
tags: [ssot, gate, concurrency]
audit_log: [scripts/collaboration_concurrency_gate.py, tests/test_collaboration_concurrency_gate.py]
---

## Goal

Block worker pane attempts to write shared SSoT files directly.

## Completion Criteria

- Non-orchestrator `ssot_write_attempted` events for shared SSoT paths fail the gate.
- Approved orchestrator SSoT events pass.
- The gate is wired into owner governance.

## Result

- Added `scripts/collaboration_concurrency_gate.py`.
- Added owner governance integration.
