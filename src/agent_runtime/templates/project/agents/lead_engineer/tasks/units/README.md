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
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
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

See `examples/UNIT-EXAMPLE-001.md` for a reusable worker-ready example.

## Optional Frontmatter

- `depends_on`: list of unit ids (`UNIT-...`) and/or task ids (`TASK-...`)
  that must be completed before this unit may start. Every reference must
  resolve to an existing unit spec or task file;
  `scripts/task_unit_readiness_gate.py` reports
  `unit:depends-on-unknown-ref:<ref>` for dangling references and
  `unit:depends-on-self:<ref>` for self references.
  `scripts/wave_dispatcher.py` consumes this field to decompose units into
  topological waves: units in the same wave have no `depends_on` edges
  between them and pairwise-disjoint `target_files` footprints. A task id
  reference means "after every selected unit of that task".

```yaml
depends_on:
  - UNIT-TASK-AR-344-001
  - TASK-AR-350
```
