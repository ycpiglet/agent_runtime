---
id: TASK-AR-344
display_id: TASK-AR-344
task_uid: 53dc0739-dc37-40b0-b31e-4f553ae1b92a
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
updated_at: 2026-06-11T19:50:16+09:00
status: planned
priority: P0
difficulty: L
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - project-management
  - gate
  - worker-ready
---

# TASK-AR-344 - Unit readiness gate

## Goal

- Block low-tier worker dispatch when task or unit records lack enough detail.

## Scope

- Implement `scripts/task_unit_readiness_gate.py`.
- Validate required fields: context, inputs, target files, scope, acceptance criteria, verification commands, and handoff.
- Add focused tests and a migration mode so legacy tasks can be reported without breaking all old work at once.

## Acceptance Criteria

- Gate fails for an active worker task missing a ready unit spec.
- Gate passes for a complete unit fixture.
- Gate output names the missing field and owning task/unit.

## Evidence Targets

- `scripts/task_unit_readiness_gate.py`
- `tests/test_task_unit_readiness_gate.py`
- Owner governance integration plan

