---
id: TASK-AR-249
status: planned
owner: lead-engineer
priority: P1
difficulty: M
est_hours: 8
est_tokens: 1800
task_set_id: TASKSET-AR-PANE-PROGRESS
depends_on:
  - TASK-AR-247
  - TASK-AR-248
tags:
  - task-claim
  - continuity
  - governance-gate
  - pane-progress
  - no-ssot-write
audit_log:
  - docs/superpowers/plans/2026-06-10-pane-progress-tasksets.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - scripts/continuity_contract_gate.py
created: 2026-06-10
---

## Goal

Enforce progress updates in task claims and continuity pointers so new panes can resume active work without hidden state.

## Scope

- Add dispatcher options for `task_set_id`, `step_index`, `step_total`, and `status_text`.
- Validate `progress_pct` and phase/step consistency.
- Keep the root dispatcher and template dispatcher aligned.
- Strengthen continuity checks if the live pointer contract does not require step/status fields.

## Completion Criteria

- Claim creation writes `task_set_id`, `step_index`, `step_total`, `status_text`, and `updated_at`.
- Invalid progress or impossible step state is rejected.
- `NEXT-SESSION-POINTER.yml` points to the current task set instead of stale completed work.
- Focused dispatcher and continuity tests pass.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-249 planned
- gate: pending
- review: draft

