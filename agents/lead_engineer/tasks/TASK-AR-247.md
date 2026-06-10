---
id: TASK-AR-247
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 8
est_tokens: 1600
task_set_id: TASKSET-AR-PANE-PROGRESS
tags:
  - testset
  - golden-set
  - pane-progress
  - task-set
  - quality-gate
audit_log:
  - docs/superpowers/plans/2026-06-10-pane-progress-tasksets.md
  - agents/project/evals/pane-progress-v1.jsonl
  - agents/project/DATASET-CATALOG.yml
  - tests/test_pane_progress_contract.py
  - reviews/OFFLINE-EVAL-2026-06-10-task-ar-247-pane-progress.json
created: 2026-06-10
---

## Goal

Create the fixed pane/task-set progress golden set before UI or enforcement changes.

## Scope

- Add `agents/project/evals/pane-progress-v1.jsonl` with typical, edge, adversarial, ambiguous, and access-controlled cases.
- Register the dataset in `agents/project/DATASET-CATALOG.yml`.
- Add tests that verify every row has source refs, query contract metadata, expected outcome, and required progress fields.

## Completion Criteria

- `tests/test_pane_progress_contract.py` passes.
- The dataset includes `phase`, `step_index`, `step_total`, `progress_pct`, `status_text`, and `task_set_id` coverage.
- The dataset catches invalid progress percent, inconsistent phase/step state, and task-set aggregation cases.
- No UI or dispatcher behavior is changed before this test contract exists.

## State Machine Mapping

- cycle: evaluated
- task: TASK-AR-247 completed
- gate: pass
- review: evidence-recorded

## Completion Log

- Added `agents/project/evals/pane-progress-v1.jsonl` with 6 fixed cases across typical, edge, adversarial, ambiguous, and access-controlled types.
- Registered `pane-progress-gold` in `agents/project/DATASET-CATALOG.yml`.
- Added `tests/test_pane_progress_contract.py` for committed testset contract validation.
- Verified `pane-progress-gold status=pass score=1.0 cases=6 findings=0` with `scripts/offline_eval_gate.py`.

