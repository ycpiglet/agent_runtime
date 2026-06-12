---
id: TASK-AR-370
display_id: TASK-AR-370
task_uid: 5655d2cb-a038-4c74-8a50-6e707e4ece98
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-12T11:06:57+09:00
started_at: 2026-06-12T09:43:38+09:00
completed_at: 2026-06-12T11:06:57+09:00
title: Generated work-item numbering classifier + task ID reservation ledger
status: completed
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

# TASK-AR-370 - Generated work-item numbering classifier + task ID reservation ledger

## Goal

- Prevent concurrent panes from selecting the same human display ID before a task file exists, and move Owner-facing `1 -> 1.1 -> 1.1.1 -> 1.1.1.1` numbers into a generated classifier view.

## Scope

- Keep canonical task identity UUID/timestamp backed; planners must not hand-reserve human ordinal numbers.
- Generate Owner-facing work-item numbers across initiative, taskset, task, and unit records.
- Design and implement a small reservation ledger for stable task file creation when a command needs to reserve an ID/range.
- Add an allocator command that reserves one ID or a contiguous range before task files are written.
- Record reservation owner, timestamp, taskset, initiative, status, and expiry/abandonment behavior.
- Add a gate that fails duplicate display IDs, duplicate live reservations, stale reservations beyond policy, or task files missing `task_uid`.
- Preserve immutable `task_uid` as the canonical identity after creation.
- Keep generated classification output current through `scripts/work_item_classifier.py --check`.

## Out Of Scope

- Rewriting historical display IDs.
- Moving existing task files.
- Changing Git history.

## Acceptance Criteria

- Two concurrent planners cannot successfully reserve the same display ID range.
- Owner-facing numbers are assigned by the classifier and show initiative/taskset/task/unit position clearly.
- A task file created from a reservation clears or fulfills that reservation.
- The gate reports exact duplicate/stale reservation paths and exits non-zero.

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- New focused tests for allocator and stale reservation cases.
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE --check`

## Handoff

- Report the ledger path, allocator command, race behavior, and rollback path for abandoned reservations.

## Completion Evidence

- Implemented `python scripts/task_identity.py reserve-id` with a lock-protected JSON ledger at `agents/project/work-items/TASK-ID-RESERVATIONS.json`.
- Extended `python scripts/task_identity.py create --reservation-id <id>` so creating a task from a reservation marks that reservation `fulfilled` with task path, task ID, task UID, and timestamp.
- Extended `python scripts/task_identity.py check --check` to report duplicate display IDs, duplicate active reservations, stale active reservations, active reservations that point to existing tasks, and invalid fulfilled reservations.
- Recorded the Owner/Claude Work Item generator, metadata envelope, and agent identity design discussion in `reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md`.

## Verification Results

- `python -m py_compile scripts\task_identity.py` -> pass
- `pytest tests\test_task_identity.py tests\test_work_item_classifier.py -q` -> `9 passed`
- `pytest tests -q` -> `432 passed`
- `python scripts/task_identity.py check --check` -> pass, `findings=0`
- `python scripts/work_item_classifier.py --check` -> pass, `findings=0`
- `python scripts/evidence_index_generator.py --write` -> pass, `findings=0`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check` -> pass, `findings=0`

