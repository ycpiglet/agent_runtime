---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-611
display_id: TASK-AR-611
task_uid: 8c371e62-1093-41ff-8b23-49d2aba31b0d
work_id: TASK-AR-611
work_uid: 8c371e62-1093-41ff-8b23-49d2aba31b0d
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
registered_at: 2026-06-19T15:36:00+09:00
created_at: 2026-06-19T15:36:00+09:00
started_at: 2026-06-19T18:20:00+09:00
updated_at: 2026-06-19T19:12:00+09:00
title: Derive Taskset Board IA implementation and beta units
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
reservation_id: RES-20260619-153600-cf31ceee-03
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Turn the accepted Taskset Board IA RFC into a source-mutation implementation registration input and a paired beta/UX evaluation plan without bypassing W0-W6.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python scripts/ui_ux_cycle.py --root . propose --dry-run --json
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION --check
  - python scripts/evidence_index_generator.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-19T18:40:00+09:00
verified_by: codex-interface-designer-task-ar-611
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-611-20260619184000.json
resolution: done
completed_at: 2026-06-19T19:12:00+09:00
closed_by: codex-interface-designer-task-ar-611
actual_hours: 1.0
actual_tokens: 12000
---

# TASK-AR-611 - Derive Taskset Board IA implementation and beta units

## Goal

- Turn the accepted Taskset Board IA RFC into a source-mutation implementation registration input and a paired beta/UX evaluation plan without bypassing W0-W6.

## Scope

- Planning and registration input only. Do not edit UI source files. The output must be specific enough for interface-designer and ux-evaluator claims.

## Acceptance Criteria

- A follow-up registration input names the next UI source mutation task, target files, target API/schema contracts, and token/component/pattern/one-off classification.
- A beta-tester artifact plan records clicked/typed flows, recovery attempts, viewport/data state, keyboard traversal, reduced-motion behavior, and BTC-style failure routing.
- The next implementation task keeps page files focused on layout and data wiring while repeated surface area is moved into pattern assets.
- The plan preserves design-system gate, focused UI tests, evidence index, and independent W4b verification commands.

## Outputs

- Implementation registration input:
  `agents/project/work-items/REGISTRATION-2026-06-19-taskset-board-attention-workspace-implementation.json`.
- Implementation plan:
  `reviews/PLAN-2026-06-19-taskset-board-attention-workspace-implementation.md`.
- Beta/UX evidence plan:
  `reviews/BETA-PLAN-2026-06-19-taskset-board-attention-workspace.md`.
- Source mutation remains out of scope for this task; the follow-up
  implementation task must create a fresh claim/worktree before editing UI
  source files.

## Verification

- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION --check`
- `python scripts/evidence_index_generator.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T19:12:00+09:00`
- Resolution: `done`
- Actual hours: `1.0`
- Actual tokens: `12000`
- Closed by: `codex-interface-designer-task-ar-611`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-611-20260619184000.json`
<!-- work-close:end -->
