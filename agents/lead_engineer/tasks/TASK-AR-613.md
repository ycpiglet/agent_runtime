---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-613
display_id: TASK-AR-613
task_uid: 6bcce750-b52c-4e7a-8c02-fb8caa36394a
work_id: TASK-AR-613
work_uid: 6bcce750-b52c-4e7a-8c02-fb8caa36394a
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
registered_at: 2026-06-19T18:35:00+09:00
created_at: 2026-06-19T18:35:00+09:00
started_at: 2026-06-19T20:56:29+09:00
updated_at: 2026-06-19T21:55:26+09:00
verification_status: passed
verified_at: 2026-06-19T21:49:12+09:00
verified_by: codex-independent-w4b-verifier
evidence_refs:
  - reviews/VERIFY-2026-06-19-task-ar-613-closeout.json
title: Run Taskset Board attention workspace beta and UX evaluation
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 9000
owner: ux-evaluator
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-ATTENTION-WORKSPACE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-613/UNIT-TASK-AR-613-001.md
reservation_id: RES-20260619-183500-c4338bba-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-interface-designer-task-ar-611
summary: Verify the attention workspace through user-like beta actions, keyboard traversal, mobile and desktop viewport checks, reduced-motion review, recovery states, and BTC-style defect routing.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
resolution: done
completed_at: 2026-06-19T21:55:26+09:00
closed_by: codex-ux-evaluator-ar-613
actual_hours: 1.5
actual_tokens: 12000
---

# TASK-AR-613 - Run Taskset Board attention workspace beta and UX evaluation

## Goal

- Verify the attention workspace through user-like beta actions, keyboard traversal, mobile and desktop viewport checks, reduced-motion review, recovery states, and BTC-style defect routing.

## Scope

- Evaluation and evidence only. Do not mutate UI source files in this task. Implementation defects become BTC-style follow-up candidates or a new claimed implementation task.

## Acceptance Criteria

- Beta evidence records exact clicked or typed actions for unknown-target discovery, known-target retrieval, relation detail inspection, and all-tasksets fallback.
- Keyboard traversal is exercised from route entry through lane controls, switcher, card selection, relation detail, and fallback list.
- Recovery attempts cover empty lane, stale evidence, blocked command, interrupted claim, expired claim, and no active claim states.
- Desktop and mobile viewport notes include environment, viewport, data state, expected result, observed result, and pass/fail status.
- Reduced-motion behavior and non-color-only state cues are reviewed.
- Every visible defect gets a BTC-TSAW failure id with reproduction path and assetization class.

## Verification

- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
- `python scripts/ui_ux_cycle.py --root . assess --json`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T21:55:26+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `12000`
- Closed by: `codex-ux-evaluator-ar-613`
- Evidence:
  - `reviews/VERIFY-2026-06-19-task-ar-613-closeout.json`
<!-- work-close:end -->
