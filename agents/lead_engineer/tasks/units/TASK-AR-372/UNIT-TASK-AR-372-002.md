---
unit_id: UNIT-TASK-AR-372-002
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
completed_at: 2026-06-12T12:27:29+09:00
verification_status: passed
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, data_integrity, cross_cutting]
context: "Create the deterministic structured registration path that consumes the work schema and task ID reservation ledger."
inputs:
  - agents/project/WORK-SCHEMA.yml
  - scripts/task_identity.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - scripts/backlog_board.py
  - scripts/work_item_classifier.py
  - tests/test_work_registration.py
  - tests/test_backlog_board_tasksets.py
scope: "Implement deterministic JSON-based work registration for initiative, taskset plan, task files, registration review, owner docs, registry, and generated views; do not implement AI split/criteria/assign."
acceptance:
  - "A structured JSON input creates an initiative, taskset plan, two task files, and a registration review."
  - "The command is idempotent for the same input."
  - "Missing required fields and duplicate display IDs fail before partial files are created."
  - "Missing display IDs are allocated through the reservation ledger."
verification:
  - "python -m py_compile scripts\\work.py scripts\\backlog_board.py scripts\\work_item_classifier.py"
  - "pytest tests/test_work_registration.py tests/test_backlog_board_tasksets.py tests/test_work_item_classifier.py -q"
  - "python scripts/work.py --help"
handoff: "Report command syntax, input shape, generated files, and remaining TASK-AR-372 registration gaps."
stop_condition: "Stop after deterministic structured registration; leave AI planner tools and unit creation automation for later units."
---

# UNIT-TASK-AR-372-002 - Deterministic Work Registration CLI

## Context

`TASK-AR-372` needs one planner-facing command path for work registration. The
previous unit established the field dictionary SSoT; this unit connects that
planning contract to a deterministic `work.py new` command.

## Inputs

- `agents/project/WORK-SCHEMA.yml`
- `scripts/task_identity.py`
- `scripts/work_item_classifier.py`
- `scripts/backlog_board.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`

## Target Files

- `scripts/work.py`
- `scripts/backlog_board.py`
- `scripts/work_item_classifier.py`
- `tests/test_work_registration.py`
- `tests/test_backlog_board_tasksets.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`

## Scope

In scope: JSON input validation, deterministic creation of initiative/taskset
plan/task/review records, taskset metadata registry, reservation-ledger
fulfillment, owner-doc pointer update, generated view refresh, and tests.

Out of scope: AI task decomposition, criteria generation, assignment,
interactive approval workflows, external side effects, and bulk migration.

## Steps

1. Add a `scripts/work.py new --input <json>` command.
2. Reuse `task_identity.py` reservation helpers under the reservation lock.
3. Add a taskset registry consumed by the backlog board.
4. Refresh board, work-item classification, and evidence index after creation.
5. Add tests for creation, idempotence, duplicate ID failure, missing field
   failure, and automatic display ID allocation.

## Acceptance Criteria

- A sample structured input creates an initiative, taskset plan, two task files,
  registration review, owner-doc pointer, taskset registry row, and generated
  board/classification views.
- The same command returns success on a second run without duplicating
  reservations.
- Duplicate display IDs and missing task fields fail before `agents/` files are
  created.
- Missing task display IDs are allocated as fulfilled reservation-ledger rows.

## Verification

```powershell
python -m py_compile scripts\work.py scripts\backlog_board.py scripts\work_item_classifier.py
pytest tests/test_work_registration.py tests/test_backlog_board_tasksets.py tests/test_work_item_classifier.py -q
python scripts/work.py --help
```

## Handoff

`scripts/work.py new --input <json>` is now the deterministic first registration
path. It is intentionally JSON-only and does not perform AI decomposition or
assignment.

## Completion Evidence

- `python -m py_compile scripts\work.py scripts\backlog_board.py scripts\work_item_classifier.py`
- `pytest tests/test_work_registration.py tests/test_backlog_board_tasksets.py tests/test_work_item_classifier.py -q`
- `python scripts/work.py --help`

## Stop Boundary

Stop after deterministic registration. Continue into unit generation,
criteria generation, assignment proposals, or closeout automation only under
separate units.
