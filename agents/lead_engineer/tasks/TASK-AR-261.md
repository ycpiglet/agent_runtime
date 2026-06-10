---
id: TASK-AR-261
display_id: TASK-AR-261
task_uid: 38a4b41b-8318-465f-ad5f-b8cae196c19c
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Realtime backlog status pointer sync enforcement
status: completed
priority: P0
importance: High
difficulty: L
est_hours: 6
est_tokens: 2200
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: agent-runtime-core
owner: lead-engineer
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [backlog, status, pointer, sync, gate]
audit_log: [BACKLOG-BOARD.md, STATUS.md, agents/project/NEXT-SESSION-POINTER.yml]
---

## Goal

Prevent task progress from drifting away from backlog board, status, and next-session pointer surfaces.

## Completion Criteria

- A `state_sync_gate.py` checks active taskset/task consistency across task files, claims, board, status, and pointer.
- Board freshness is measured against task metadata updates.
- Contradictory active taskset states block Owner governance.
- Focused tests cover stale board, stale pointer, and consistent active taskset states.

## Execution Notes

- The gate should not require all historical docs to be perfect.
- It should focus on the active taskset and recently changed task files.

## Result

- Added `scripts/state_sync_gate.py` and template copy.
- Added focused tests in `tests/test_state_sync_gate.py`.
- Wired state sync gate into Owner governance.
- Verified state sync gate: `findings=0`, `block=0`, `watch=0`.
