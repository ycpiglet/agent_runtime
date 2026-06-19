---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-604
display_id: TASK-AR-604
task_uid: a60cb6b0-21a6-4f46-a0df-c1fbba8d9ba3
work_id: TASK-AR-604
work_uid: a60cb6b0-21a6-4f46-a0df-c1fbba8d9ba3
kind: task
parent_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
registered_at: 2026-06-19T09:08:00+09:00
created_at: 2026-06-19T09:08:00+09:00
updated_at: 2026-06-19T12:21:22+09:00
title: Run operator attention graph beta and UX evaluation
status: planned
priority: P1
difficulty: M
est_hours: 3
est_tokens: 7000
owner: ux-evaluator
team: ui-ux
initiative_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-604/UNIT-TASK-AR-604-001.md
reservation_id: RES-20260619-090800-36377773-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Verify the first operator_attention_graph implementation through user-like beta actions, recovery attempts, responsive checks, accessibility review, and BTC-style defect routing.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
  - python scripts/ui_ux_cycle.py --root . assess --json
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-19T12:21:22+09:00
verified_by: codex-ux-evaluator-oag-604-resume
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-604-20260619122122.json
---

# TASK-AR-604 - Run operator attention graph beta and UX evaluation

## Goal

- Verify the first operator_attention_graph implementation through user-like beta actions, recovery attempts, responsive checks, accessibility review, and BTC-style defect routing.

## Scope

- Evaluation and evidence only. Do not mutate UI source files in this task. File implementation defects as beta evidence or follow-up work, not direct fixes.

## Acceptance Criteria

- Beta-tester evidence records clicked or keyboard-driven paths from taskset attention to claim evidence, graph/wiki context, and command readiness.
- Recovery attempts cover empty graph, stale evidence, blocked command, and interrupted claim states.
- Desktop and mobile viewport notes include environment, exact actions, and observed result.
- Every visible defect is assigned a BTC-style failure ID with reproduction path.
- UX evaluation covers labels, focus order, reduced motion, non-color-only state, and responsive graph-to-list fallback.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`
