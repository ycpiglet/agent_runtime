---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-372-006
work_uid: 6a7e26f2-7697-4e60-b8db-076cb058b4b0
kind: unit
parent_id: TASK-AR-372
unit_id: UNIT-TASK-AR-372-006
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-12T13:29:59+09:00
updated_at: 2026-06-12T13:32:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-06-12-work-verify-command.md
created_by: codex
summary: Add deterministic work close command with passed-evidence and actuals guardrails.
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - lifecycle_metadata
context: Add deterministic closeout automation so completed work items require passed verification evidence, completion metadata, resolution semantics, and actuals instead of hand-written frontmatter.
inputs:
  - scripts/work.py
  - scripts/work_schema_gate.py
  - agents/project/WORK-SCHEMA.yml
  - tests/test_work_close.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - scripts/work_schema_gate.py
  - agents/project/WORK-SCHEMA.yml
  - tests/test_work_close.py
  - agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-006.md
  - reviews/REVIEW-2026-06-12-work-close-command.md
scope: Implement work.py close for deterministic done closeout; do not implement AI split, criteria, assign, or Work Explorer UI.
acceptance:
  - work.py close locates a task or unit by ID/path and refuses done closeout unless verification_status is passed.
  - Done closeout requires at least one passed verification evidence JSON referenced by evidence_refs.
  - Done closeout requires actual_hours and actual_tokens.
  - Successful closeout writes status completed, resolution, completed_at, updated_at, closed_by, actual_hours, actual_tokens, and an idempotent generated Closeout block.
  - Closeout refreshes generated board, classification, and evidence index outputs.
verification:
  - python -m py_compile scripts/work.py scripts/work_schema_gate.py
  - pytest tests/test_work_close.py tests/test_work_verify.py tests/test_work_schema_gate.py -q
  - python scripts/work.py close --help
handoff: Report work close syntax, evidence preconditions, actuals metadata, and remaining AI proposal tools.
stop_condition: Stop after deterministic closeout is implemented, verified, and recorded; leave split/criteria/assign to separate planner-gated units.
verified_at: 2026-06-12T13:31:00+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-372-006-20260612133100.json
resolution: done
completed_at: 2026-06-12T13:32:00+09:00
closed_by: codex
actual_hours: 0.4
actual_tokens: 0
---

# UNIT-TASK-AR-372-006 - Deterministic Work Close Command

## Context

Add deterministic closeout automation so completed work items require passed
verification evidence, completion metadata, resolution semantics, and actuals
instead of hand-written frontmatter.

## Inputs

- scripts/work.py
- scripts/work_schema_gate.py
- agents/project/WORK-SCHEMA.yml
- tests/test_work_close.py
- agents/lead_engineer/tasks/TASK-AR-372.md

## Target Files

- scripts/work.py
- scripts/work_schema_gate.py
- agents/project/WORK-SCHEMA.yml
- tests/test_work_close.py
- agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-006.md
- reviews/REVIEW-2026-06-12-work-close-command.md

## Scope

Implement `work.py close` for deterministic done closeout. Do not implement AI
`split`, `criteria`, `assign`, or Work Explorer UI behavior in this unit.

## Steps

1. Add closeout evidence validation that checks passed verification metadata
   and passed verification JSON references.
2. Add actuals and resolution metadata writes for successful closeout.
3. Add a generated closeout body block that is replaceable on rerun.
4. Refresh generated board, classification, and evidence index outputs after
   a successful close.
5. Register `actual_hours` and `closed_by` in the work schema catalog.
6. Add regression tests for success, missing evidence, and missing actuals.

## Acceptance Criteria

- `python scripts/work.py close UNIT-TASK-AR-901-001 --actual-hours 1.25
  --actual-tokens 321 --json` closes a verified unit in tests.
- Done closeout refuses pending verification, missing evidence refs, failed
  evidence, and missing actuals without mutating the work item.
- Closeout metadata includes `status: completed`, `resolution`,
  `completed_at`, `closed_by`, `actual_hours`, and `actual_tokens`.
- The generated Closeout block includes completion time, resolution, actuals,
  actor, and evidence refs.
- `WORK-SCHEMA.yml` includes the closeout fields written by the command.

## Verification

```powershell
python -m py_compile scripts/work.py scripts/work_schema_gate.py
pytest tests/test_work_close.py tests/test_work_verify.py tests/test_work_schema_gate.py -q
python scripts/work.py close --help
```

## Handoff

Report `work close` syntax, evidence preconditions, actuals metadata, and the
remaining AI proposal tools.

## Stop Boundary

Stop after deterministic closeout is implemented, verified, and recorded. Leave
`split`, `criteria`, and `assign` to separate planner-gated units.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T13:32:00+09:00`
- Resolution: `done`
- Actual hours: `0.4`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-unit-task-ar-372-006-20260612133100.json`
<!-- work-close:end -->
