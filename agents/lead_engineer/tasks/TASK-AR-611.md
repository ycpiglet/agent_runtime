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
updated_at: 2026-06-19T15:36:00+09:00
title: Derive Taskset Board IA implementation and beta units
status: planned
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
tags:
  - work-cli-created
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

## Verification

- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION --check`
- `python scripts/evidence_index_generator.py --check`
