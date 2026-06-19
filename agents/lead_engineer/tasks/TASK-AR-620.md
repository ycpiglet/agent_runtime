---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-620
display_id: TASK-AR-620
task_uid: dee5279f-7a24-487e-b3fe-45e071a3c222
work_id: TASK-AR-620
work_uid: dee5279f-7a24-487e-b3fe-45e071a3c222
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
registered_at: 2026-06-20T01:08:00+09:00
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
title: Run Taskset Board evidence review queue beta and UX evaluation
status: planned
priority: P1
difficulty: M
est_hours: 3
est_tokens: 8000
owner: ux-evaluator
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-620/UNIT-TASK-AR-620-001.md
reservation_id: RES-20260620-010800-10191c6d-02
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Verify the implemented evidence review queue with exploratory beta-tester and UX-evaluator evidence covering unknown triage, known retrieval, capped drill-in, slow detail, timeout/retry, keyboard, mobile, reduced motion, and defect routing.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-620 - Run Taskset Board evidence review queue beta and UX evaluation

## Goal

- Verify the implemented evidence review queue with exploratory beta-tester and UX-evaluator evidence covering unknown triage, known retrieval, capped drill-in, slow detail, timeout/retry, keyboard, mobile, reduced motion, and defect routing.

## Scope

- Evaluation and evidence only. Do not mutate UI source files in this task. Any remaining visual, interaction, accessibility, performance, schema, or assetization defect must be routed with BTC-style IDs.

## Acceptance Criteria

- Beta evidence records exact clicked, typed, and keyboard paths for unknown evidence triage and known taskset retrieval.
- Evidence covers desktop and 390x844 mobile viewports with environment, data state, expected result, observed result, and pass/fail status.
- UX evaluation reviews typography, density, color/non-color cues, motion, effects, schema labels, assets, accessibility, responsiveness, and interaction recovery.
- Slow detail and timeout/retry states are exercised or explicitly simulated with documented limits.
- Every visible failure receives a BTC-TSERQ defect id and assetization class.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`
