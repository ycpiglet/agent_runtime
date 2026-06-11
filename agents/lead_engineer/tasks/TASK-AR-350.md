---
id: TASK-AR-350
display_id: TASK-AR-350
task_uid: a6ec5d39-e113-4690-9aa9-acf7c493bb79
registered_at: 2026-06-11T19:50:16+09:00
created_at: 2026-06-11T19:50:16+09:00
started_at: 2026-06-12T01:38:36+09:00
updated_at: 2026-06-12T01:38:36+09:00
completed_at: 2026-06-12T01:38:36+09:00
status: completed
priority: P0
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-350/UNIT-TASK-AR-350-001.md
horizon: short
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers: [ambiguity, cross_cutting, repeated_failure]
tags:
  - project-management
  - verification
  - closeout
---

# TASK-AR-350 - Verification and closeout

## Goal

- Add a taskset verification wrapper and Owner-facing closeout evidence for the PM operating system.

## Scope

- Create `scripts/verify_pm_operating_system_taskset.py`.
- Run task identity, unit readiness, model routing, dispatcher, board, Owner doc, and named taskset gates.
- Record closeout without claiming external/provider-live evidence.

## Acceptance Criteria

- `TASKSET-AR-PM-OPERATING-SYSTEM` cannot close unless all canonical tasks and gates pass.
- Closeout evidence distinguishes registration, implementation, and template propagation.
- Remaining migration watches are explicitly listed.

## Evidence Targets

- `scripts/verify_pm_operating_system_taskset.py`
- `reviews/REVIEW-2026-06-11-agent-runtime-pm-operating-system-closeout.md`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-PM-OPERATING-SYSTEM --require-complete --check`

