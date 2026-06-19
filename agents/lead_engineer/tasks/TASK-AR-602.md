---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-602
display_id: TASK-AR-602
task_uid: abcc24fb-904d-4d57-9de1-45f9ab7e7f4d
work_id: TASK-AR-602
work_uid: abcc24fb-904d-4d57-9de1-45f9ab7e7f4d
kind: task
parent_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
registered_at: 2026-06-19T08:18:00+09:00
created_at: 2026-06-19T08:18:00+09:00
updated_at: 2026-06-19T09:00:00+09:00
title: Derive next UI implementation and UX evaluation units
status: planned
started_at: 2026-06-19T08:55:00+09:00
verification_status: passed
verified_at: 2026-06-19T09:00:00+09:00
verified_by: codex-interface-designer-ui-next-units-602
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-602-20260619090000.json
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
reservation_id: RES-20260619-081800-ff02ebb7-03
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Turn the accepted design-direction RFC into the next implementation refactor and beta-tester evaluation records without bypassing W0-W6.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-602 - Derive next UI implementation and UX evaluation units

## Goal

- Turn the accepted design-direction RFC into the next implementation refactor and beta-tester evaluation records without bypassing W0-W6.

## Scope

- Planning and registration input only. Do not edit UI source files. The output must be specific enough for interface-designer and ux-evaluator claims.

## Acceptance Criteria

- A follow-up registration input names the next UI source mutation task, its target files, and its token/component/pattern/one-off classification.
- A beta-tester artifact plan records clicked/typed flows, recovery attempts, viewport/data state, and BTC-style failure routing.
- The next implementation task keeps page files focused on layout/data wiring and moves repeated surface area into pattern assets.
- The plan preserves design-system gate and focused UI test commands for W4a/W4b.

## Verification

- `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC --check`
- `python scripts/evidence_index_generator.py --check`
