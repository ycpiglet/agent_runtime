---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-606
display_id: TASK-AR-606
task_uid: 744809da-dfd2-4105-ad36-98406c23a81c
work_id: TASK-AR-606
work_uid: 744809da-dfd2-4105-ad36-98406c23a81c
kind: task
parent_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
registered_at: 2026-06-19T12:26:00+09:00
created_at: 2026-06-19T12:26:00+09:00
updated_at: 2026-06-19T12:26:00+09:00
title: Run claim-aware relation adapter beta and UX evaluation
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 5000
owner: ux-evaluator
team: ui-ux
initiative_id: INIT-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-606/UNIT-TASK-AR-606-001.md
reservation_id: RES-20260619-122600-bbf35777-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Repeat beta-tester and UX-evaluator verification after the claim-aware adapter implementation, with focus on active claim, interrupted, guarded, mobile, focus, and reduced-motion behavior.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-606 - Run claim-aware relation adapter beta and UX evaluation

## Goal

- Repeat beta-tester and UX-evaluator verification after the claim-aware adapter implementation, with focus on active claim, interrupted, guarded, mobile, focus, and reduced-motion behavior.

## Scope

- Evaluation and evidence only. Do not mutate UI source files in this task. Any remaining visual or semantic defect must be routed with BTC-style IDs.

## Acceptance Criteria

- Beta evidence includes user-like click/keyboard paths for active claim, no-claim, expired claim, interrupted claim, and blocked/guarded command states.
- UX evaluation covers labels, non-color-only state, focus order, reduced motion, mobile layout, and command readiness clarity.
- Every user-visible defect is assigned a BTC-style ID and reproduction path.
- The evaluation states whether the next cycle should pursue another implementation refinement or a new visual direction.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`
