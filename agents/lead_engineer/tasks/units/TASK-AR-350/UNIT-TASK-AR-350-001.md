---
unit_id: UNIT-TASK-AR-350-001
task_id: TASK-AR-350
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: worker_ready
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, cross_cutting, repeated_failure]
context: "Verify that the PM operating-system taskset has executable gates, routing, dispatcher metadata, template propagation, and Owner-facing closeout evidence."
inputs:
  - docs/superpowers/plans/2026-06-11-project-management-operating-system.md
  - agents/project/PROJECT-MANAGEMENT-CONTRACT.md
target_files:
  - scripts/verify_pm_operating_system_taskset.py
  - reviews/REVIEW-2026-06-12-agent-runtime-pm-operating-system-closeout.md
  - agents/lead_engineer/tasks/TASK-AR-342.md
  - agents/lead_engineer/tasks/TASK-AR-350.md
scope: "Close only TASKSET-AR-PM-OPERATING-SYSTEM after all PM gates pass; do not close Vision, Ops Feedback, or RSI work."
acceptance:
  - "The verification wrapper runs focused PM checks."
  - "The taskset work gate passes with --require-complete after PM tasks are completed."
  - "Closeout evidence distinguishes registration, implementation, template propagation, and migration watches."
verification:
  - "python scripts/verify_pm_operating_system_taskset.py --check"
  - "python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-PM-OPERATING-SYSTEM --require-complete --check"
handoff: "Report PM taskset pass/fail, changed files, verification commands, and remaining non-PM tasksets."
stop_condition: "Stop after PM closeout and resume the Owner-requested next taskset separately."
---

# UNIT-TASK-AR-350-001 - PM OS Closeout Verification

## Context

TASK-AR-350 closes the PM operating-system taskset only after the executable
PM surfaces exist and pass focused checks.

## Inputs

- `docs/superpowers/plans/2026-06-11-project-management-operating-system.md`
- `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`
- `scripts/task_unit_readiness_gate.py`
- `scripts/model_routing.py`

## Target Files

- `scripts/verify_pm_operating_system_taskset.py`
- `reviews/REVIEW-2026-06-12-agent-runtime-pm-operating-system-closeout.md`
- `agents/lead_engineer/tasks/TASK-AR-342.md`
- `agents/lead_engineer/tasks/TASK-AR-350.md`

## Scope

In scope: PM closeout verification, evidence records, and PM task status
updates.

Out of scope: closing non-PM tasksets, external publication, and provider-live
evidence.

## Steps

1. Confirm PM scripts, schema, template mirrors, and tests exist.
2. Run focused PM checks through the wrapper.
3. Mark PM task records complete only after checks pass.
4. Regenerate the backlog board.
5. Record the closeout review.

## Acceptance Criteria

- Verification wrapper passes or reports exact PM blockers.
- Named taskset gate passes with `--require-complete`.
- Closeout review lists implementation and migration watch evidence.

## Verification

```powershell
python scripts/verify_pm_operating_system_taskset.py --check
python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-PM-OPERATING-SYSTEM --require-complete --check
```

## Handoff

Report commands, outcomes, changed PM artifacts, and remaining tasksets.

## Stop Boundary

Stop after PM closeout. Continue Vision/OPS/RSI only under the next explicit
goal step or claim.
