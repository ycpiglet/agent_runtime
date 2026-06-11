# Worker-Ready Unit Specs

Unit specs are the smallest execution record a worker agent can claim. They
carry details that do not belong in `BACKLOG.md` or `BACKLOG-BOARD.md`.

## Path

```text
agents/lead_engineer/tasks/units/<task_id>/UNIT-<task_id>-NNN.md
```

## Required Frontmatter

```yaml
---
unit_id: UNIT-TASK-AR-344-001
task_id: TASK-AR-344
task_set_id: TASKSET-AR-PM-OPERATING-SYSTEM
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: worker_ready
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, cross_cutting, repeated_failure]
context: "Why this unit exists."
inputs:
  - agents/project/PROJECT-MANAGEMENT-CONTRACT.md
target_files:
  - scripts/task_unit_readiness_gate.py
scope: "Exact in-scope and out-of-scope boundary."
acceptance:
  - "Observable result."
verification:
  - "python scripts/task_unit_readiness_gate.py --task-id TASK-AR-344 --check"
handoff: "What the worker must report."
stop_condition: "Stop after this unit and do not continue into adjacent tasksets."
---
```

## Required Sections

Every worker-ready unit must include non-empty sections:

- `Context`
- `Inputs`
- `Target Files`
- `Scope`
- `Steps`
- `Acceptance Criteria`
- `Verification`
- `Handoff`
- `Stop Boundary`

If a planner cannot fill these fields, set `status:
planner_refine_required`. A worker must not execute that unit until a planner
updates the record.

## Example

See `TASK-AR-350/UNIT-TASK-AR-350-001.md` for a closeout verification unit.
