---
unit_id: UNIT-TASK-AR-372-001
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
completed_at: 2026-06-12T12:03:41+09:00
verification_status: passed
horizon: unit
model_tier: worker_standard
escalation_triggers: [ambiguity, data_integrity, cross_cutting]
context: "Establish the work item field dictionary before building the broader registration CLI/API."
inputs:
  - reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
  - agents/project/PROJECT-MANAGEMENT-CONTRACT.md
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - agents/project/WORK-SCHEMA.yml
  - scripts/work_schema_gate.py
  - scripts/owner_governance_gate.py
  - tests/test_work_schema_gate.py
scope: "Create a deterministic schema catalog and gate only; do not implement full work new/split/criteria/assign behavior in this unit."
acceptance:
  - "WORK-SCHEMA.yml defines work kinds, core envelope fields, provenance, closure, measurement, relationship, governance, search, and computed-only policies."
  - "A deterministic gate fails missing required catalog fields, missing kind matrices, missing resolution semantics, and stored derived fields."
  - "Owner governance runs the work schema gate."
verification:
  - "python scripts/work_schema_gate.py --check"
  - "pytest tests/test_work_schema_gate.py tests/test_task_unit_readiness_gate.py -q"
  - "python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-001 --require-ready --check"
  - "python scripts/owner_governance_gate.py"
handoff: "Report schema fields covered, gate behavior, verification commands, and remaining TASK-AR-372 CLI work."
stop_condition: "Stop after WORK-SCHEMA SSoT and gate; do not build the full registration CLI/API in this unit."
---

# UNIT-TASK-AR-372-001 - Work Schema SSoT And Gate

## Context

TASK-AR-372 needs a structured registration command path. The command should not
invent fields ad hoc, so this unit establishes the field dictionary and the
first deterministic gate before CLI scaffolding begins.

## Inputs

- `reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md`
- `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`
- `agents/lead_engineer/tasks/TASK-AR-372.md`
- `scripts/task_identity.py`
- `scripts/work_item_classifier.py`

## Target Files

- `agents/project/WORK-SCHEMA.yml`
- `scripts/work_schema_gate.py`
- `scripts/owner_governance_gate.py`
- `tests/test_work_schema_gate.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`

## Scope

In scope: define the work item schema catalog, record measurable acceptance
criteria for this unit, add a deterministic gate, add focused tests, and wire
the gate into owner governance.

Out of scope: implementing `work new`, `work split`, `work criteria`,
`work assign`, full registration CRUD, UI Work Explorer, or agent identity spawn
records.

## Steps

1. Add the work schema file with kind, field, and computed-only policies.
2. Add a gate that validates the schema without external YAML dependencies.
3. Add focused tests that prove the gate catches missing required fields and
   stored derived fields.
4. Wire the gate into owner governance.
5. Verify the unit and leave TASK-AR-372 open for the next CLI/API unit.

## Acceptance Criteria

- `WORK-SCHEMA.yml` contains the work kinds `initiative`, `taskset`, `task`,
  `unit`, `routine`, and `spike`.
- The schema records identity, provenance, closure, measurement, relationship,
  governance, display/search, and attribution fields with `type`,
  `required_for`, `populated_by`, `consumed_by`, and `query_use`.
- The schema makes `progress_pct`, `age`, `lead_time`, `est_actual_delta`, and
  `rollup_progress_pct` computed-only.
- `scripts/work_schema_gate.py --check` passes against the repository schema and
  fails fixture schemas that remove required fields or store derived fields.
- Owner governance includes the work schema gate.

## Verification

```powershell
python scripts/work_schema_gate.py --check
pytest tests/test_work_schema_gate.py tests/test_task_unit_readiness_gate.py -q
python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-001 --require-ready --check
python scripts/owner_governance_gate.py
```

## Handoff

Report the schema coverage, gate behavior, command results, and the next
remaining TASK-AR-372 unit for `work new` or structured registration.

## Completion Evidence

- `python -m py_compile scripts\work_schema_gate.py`
- `python scripts/work_schema_gate.py --check`
- `pytest tests/test_work_schema_gate.py tests/test_task_unit_readiness_gate.py -q`
- `python scripts/task_unit_readiness_gate.py --task-id TASK-AR-372 --unit-id UNIT-TASK-AR-372-001 --require-ready --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE --check`
- `python scripts/owner_governance_gate.py`

## Stop Boundary

Stop after the schema SSoT and gate are verified. Continue into full
registration CLI/API behavior only under a separate TASK-AR-372 unit.
