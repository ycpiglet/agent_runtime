---
id: TASK-AR-370
display_id: TASK-AR-370
task_uid: 5655d2cb-a038-4c74-8a50-6e707e4ece98
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-12T08:17:54+09:00
title: Task ID reservation ledger and create-task lock
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - race_condition
  - cross_cutting
tags:
  - task-identity
  - registration
  - concurrency
---

# TASK-AR-370 - Task ID reservation ledger and create-task lock

## Goal

- Prevent concurrent panes from selecting the same human display ID before a task file exists.

## Scope

- Design and implement a small reservation ledger for `TASK-AR-*` display IDs.
- Add an allocator command that reserves one ID or a contiguous range before task files are written.
- Record reservation owner, timestamp, taskset, initiative, status, and expiry/abandonment behavior.
- Add a gate that fails duplicate display IDs, duplicate live reservations, stale reservations beyond policy, or task files missing `task_uid`.
- Preserve immutable `task_uid` as the canonical identity after creation.

## Out Of Scope

- Rewriting historical display IDs.
- Moving existing task files.
- Changing Git history.

## Acceptance Criteria

- Two concurrent planners cannot successfully reserve the same display ID range.
- A task file created from a reservation clears or fulfills that reservation.
- The gate reports exact duplicate/stale reservation paths and exits non-zero.

## Verification

- `python scripts/task_identity.py check --check`
- New focused tests for allocator and stale reservation cases.
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE --check`

## Handoff

- Report the ledger path, allocator command, race behavior, and rollback path for abandoned reservations.

