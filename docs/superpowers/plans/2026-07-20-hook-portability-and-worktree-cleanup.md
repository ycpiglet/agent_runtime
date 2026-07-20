---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
work_uid: 3c7b7116-5dba-4517-b8b7-3dc5f935ba0e
kind: taskset
id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
parent_id: INIT-AR-HOOK-PORTABILITY-CLEANUP
initiative_id: INIT-AR-HOOK-PORTABILITY-CLEANUP
status: active
owner: lead_engineer
created_at: 2026-07-20T12:56:05+09:00
updated_at: 2026-07-20T12:56:05+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md
created_by: codex-root
summary: Repair cross-platform hook commands, activate Git hook wiring, and verify a clean worktree lifecycle.
---

# Hook Portability Maintainer

## Goal

- Repair cross-platform hook commands, activate Git hook wiring, and verify a clean worktree lifecycle.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-601` | Repair portable hooks and clean the checkout |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-601-001` | `TASK-AR-601` | Make hook execution portable and close the worktree lifecycle |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
