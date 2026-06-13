---
unit_id: UNIT-TASK-AR-373-001
task_id: TASK-AR-373
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: worker_ready
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, cross_cutting]
context: "Legacy planned tasks now carry the v2.0 metadata envelope but have no machine-readable worker-readiness classification."
inputs:
  - agents/project/WORK-MODEL-2.0.md
  - scripts/task_unit_readiness_gate.py
target_files:
  - scripts/unit_readiness_report.py
  - tests/test_unit_readiness_report.py
scope: "Add the read-only classifier. Out of scope: writing units, changing statuses."
acceptance:
  - "Report classifies all open tasks into four classes with counts."
verification:
  - "python -m pytest tests/test_unit_readiness_report.py -q"
handoff: "Report class counts and top migration candidates."
stop_condition: "Stop after this unit."
---

# UNIT-TASK-AR-373-001 — worker-readiness classifier report

## Context
- Open tasks are v2.0-migrated but lack a machine-readable readiness classification; planners discover missing units only at dispatch.

## Inputs
- agents/project/WORK-MODEL-2.0.md
- scripts/task_unit_readiness_gate.py

## Target Files
- scripts/unit_readiness_report.py
- tests/test_unit_readiness_report.py

## Scope
- Build scripts/unit_readiness_report.py classifying each non-completed task as worker_ready | task_detail_sufficient | unit_missing | planner_refine_required (units/<task>/ presence + acceptance/verification sections). Read-only (--json + table).

## Steps
- Enumerate non-completed task files; for each, check for a units/<task>/ dir and acceptance+verification sections; assign a class; emit counts + per-task rows.

## Acceptance Criteria
- Report classifies all open tasks into the four classes with counts.
- Tasks with units/<task>/ + acceptance+verification -> worker_ready.
- Exit 0 always (report-only).

## Verification
- `python -m pytest tests/test_unit_readiness_report.py -q`
- `python scripts/unit_readiness_report.py --check`

## Handoff
- Report the class counts and the top planner_refine_required candidates.

## Stop Boundary
- Stop after this unit; do not author units for the classified tasks.
