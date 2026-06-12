---
unit_id: UNIT-TASK-AR-372-003
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
completed_at: 2026-06-12T12:45:18+09:00
verification_status: passed
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, data_integrity, cross_cutting]
context: "Extend deterministic work registration so planner-approved structured input can create worker-ready unit specs, not only task records."
inputs:
  - scripts/work.py
  - scripts/task_unit_readiness_gate.py
  - tests/test_work_registration.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - tests/test_work_registration.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
  - reviews/REVIEW-2026-06-12-work-registration-unit-scaffold.md
scope: "Add optional deterministic unit spec generation to work.py new; keep AI split/criteria/assign and closeout automation out of scope."
acceptance:
  - "tasks[].units[] input creates UNIT-<task>-NNN files under agents/lead_engineer/tasks/units/<task_id>/."
  - "Generated unit specs carry the work-item envelope plus readiness-gate required frontmatter and sections."
  - "Generated task files link the first unit through unit_spec for board visibility."
  - "Unit-including inputs are idempotent and missing required unit fields fail before partial files are created."
  - "The generated unit spec passes task_unit_readiness_gate with --require-ready."
verification:
  - "python -m py_compile scripts\\work.py"
  - "pytest tests/test_work_registration.py tests/test_task_unit_readiness_gate.py tests/test_work_item_classifier.py -q"
  - "python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-003 --require-ready --check"
  - "python scripts/work_item_classifier.py --check"
handoff: "Report the tasks[].units[] input shape, readiness-gate evidence, and remaining TASK-AR-372 closeout/verify work."
stop_condition: "Stop after deterministic unit generation is verified; do not implement work close, work verify, or AI planner proposal tools in this unit."
---

# UNIT-TASK-AR-372-003 - Worker-Ready Unit Generation In Work CLI

## Context

`TASK-AR-372` already has a deterministic `work.py new` path for initiatives,
tasksets, tasks, reviews, owner docs, and generated views. The next gap is the
optional unit layer: a planner-approved registration input should be able to
create worker-ready unit specs that a lower-cost worker can execute from the
record alone.

## Inputs

- `scripts/work.py`
- `scripts/task_unit_readiness_gate.py`
- `tests/test_work_registration.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`
- `reviews/REVIEW-2026-06-12-work-registration-cli.md`

## Target Files

- `scripts/work.py`
- `tests/test_work_registration.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`
- `reviews/REVIEW-2026-06-12-work-registration-unit-scaffold.md`
- `owner-docs.yml`
- `BACKLOG-BOARD.md`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.json`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.md`

## Scope

In scope: optional `tasks[].units[]` input validation, deterministic
`UNIT-<task>-NNN` ID generation, unit frontmatter/body rendering,
`unit_spec` linkage from the generated task file, idempotent existing-record
detection, tests for readiness and partial-write prevention, and generated view
refresh.

Out of scope: automatic AI decomposition, criteria generation, assignment,
approval bypass, `work close`, `work verify`, and bulk migration of old tasks.

## Steps

1. Add unit input validation to `scripts/work.py`.
2. Assign unit IDs only after task display IDs are resolved.
3. Render unit specs with the readiness-gate required frontmatter and sections.
4. Include unit paths in idempotent results and generated classification.
5. Add regression tests that run the real readiness gate against a generated
   unit.

## Acceptance Criteria

- A structured JSON input with `tasks[].units[]` creates a unit file at
  `agents/lead_engineer/tasks/units/TASK-AR-901/UNIT-TASK-AR-901-001.md`.
- The generated unit frontmatter includes `schema_version`, `work_id`,
  `work_uid`, `kind: unit`, `parent_id`, `unit_id`, `task_id`, readiness fields,
  and `verification_status: pending`.
- The generated task frontmatter includes `unit_spec` pointing to the first
  generated unit.
- A second run of the same input returns `already_exists` and does not duplicate
  task reservations.
- Missing required unit fields fail before `agents/` files are created.
- The real `task_unit_readiness_gate.py` passes for the generated unit.

## Verification

```powershell
python -m py_compile scripts\work.py
pytest tests/test_work_registration.py tests/test_task_unit_readiness_gate.py tests/test_work_item_classifier.py -q
python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-003 --require-ready --check
python scripts/work_item_classifier.py --check
```

## Handoff

`scripts/work.py new --input <json>` now accepts optional `tasks[].units[]`
records. Each unit must provide `title`, `context`, `inputs`, `target_files`,
`scope`, `steps`, `acceptance`, `verification`, `handoff`, and
`stop_condition`. The command remains deterministic and does not infer or
approve AI-generated decomposition.

## Completion Evidence

- `python -m py_compile scripts\work.py`
- `pytest tests/test_work_registration.py tests/test_task_unit_readiness_gate.py tests/test_work_item_classifier.py -q`
- `python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-003 --require-ready --check`
- `python scripts/work_item_classifier.py --check`

## Stop Boundary

Stop after deterministic unit scaffold generation. Continue into `work close`,
`work verify`, AI `split/criteria/assign`, or agent identity attribution only
under separate units.
