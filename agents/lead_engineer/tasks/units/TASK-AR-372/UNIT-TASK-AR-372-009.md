---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-372-009
work_uid: 9f0f0d0b-cbfb-4de0-8db0-32e944ac6d0e
kind: unit
parent_id: TASK-AR-372
unit_id: UNIT-TASK-AR-372-009
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
verification_status: passed
team: agent-runtime-core
owner: lead_engineer
created_at: 2026-06-12T14:29:06+09:00
updated_at: 2026-06-12T14:32:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-06-12-work-assign-command.md
created_by: codex
summary: Add proposal-only work split command for task-to-unit decomposition gaps.
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - planning_boundary
context: Add the remaining B-mode planner tool surface for Work Items by proposing worker-ready unit specs from an unsplit task without creating canonical unit files or reserving display IDs.
inputs:
  - scripts/work.py
  - tests/test_work_split.py
  - scripts/task_unit_readiness_gate.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - tests/test_work_split.py
  - agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-009.md
  - reviews/REVIEW-2026-06-12-work-split-command.md
scope: Implement work.py split as a deterministic proposal-only task-to-unit recommender; do not create unit files, reserve IDs, auto-apply proposals, or implement Work Explorer UI.
acceptance:
  - work.py split accepts a task ID or task path and detects existing canonical unit specs.
  - If the task has no registered unit specs, the command writes a B-mode planning proposal JSON and draft markdown with proposed unit specs.
  - Proposed units include the worker-ready section fields needed by the unit readiness contract.
  - The command does not mutate the source task or create unit files.
  - If units already exist, the command returns pass and writes no proposal.
  - Tests cover proposal creation, pass-without-proposal, and missing task failure.
verification:
  - python -m py_compile scripts/work.py
  - pytest tests/test_work_split.py tests/test_work_assign.py tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
  - python scripts/work.py split TASK-AR-372 --json
  - python scripts/work.py split --help
handoff: Report work split syntax, proposal-only outputs, readiness self-check behavior, and remaining approved-apply/UI gaps.
stop_condition: Stop after split proposal generation is implemented, verified, and recorded; leave approved apply, automatic dispatch, and Work Explorer UI to separate records.
verified_at: 2026-06-12T14:31:00+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-372-009-20260612143100.json
resolution: done
completed_at: 2026-06-12T14:32:00+09:00
closed_by: codex
actual_hours: 0.6
actual_tokens: 0
---

# UNIT-TASK-AR-372-009 - Proposal-Only Work Split Command

## Context

Add the remaining B-mode planner tool surface for Work Items by proposing
worker-ready unit specs from an unsplit task without creating canonical unit
files or reserving display IDs.

## Inputs

- scripts/work.py
- tests/test_work_split.py
- scripts/task_unit_readiness_gate.py
- agents/lead_engineer/tasks/TASK-AR-372.md

## Target Files

- scripts/work.py
- tests/test_work_split.py
- agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-009.md
- reviews/REVIEW-2026-06-12-work-split-command.md

## Scope

Implement `work.py split` as a deterministic proposal-only task-to-unit
recommender. Do not create unit files, reserve IDs, auto-apply proposals, or
implement Work Explorer UI behavior in this unit.

## Steps

1. Load a task work item without treating existing child units as ambiguous.
2. Detect existing canonical unit specs and return pass/no-op when present.
3. For tasks with no units, derive proposed unit specs from task acceptance,
   verification, target files, and context.
4. Run an internal readiness check over the proposed unit fields.
5. Write a B-mode proposal JSON and draft only for unsplit tasks.
6. Add regression tests for proposal creation, no-op pass, and missing task.

## Acceptance Criteria

- `python scripts/work.py split TASK-AR-901 --json` writes a B-mode proposal in
  tests when a task has no child unit specs.
- The proposal includes `mode: B`, `status: proposed`, `action_type:
  plan_update`, source refs, target files, verifier list, owner boundary,
  proposed unit specs, and readiness findings.
- Proposed unit specs include context, inputs, target files, scope, steps,
  acceptance, verification, handoff, and stop condition.
- The source task text is unchanged by proposal generation.
- The command does not create files under `agents/lead_engineer/tasks/units/`
  for the target task.
- If canonical units already exist, the command returns `work-split: pass` and
  writes no planning outbox files.
- Missing task returns nonzero and writes nothing.

## Verification

```powershell
python -m py_compile scripts/work.py
pytest tests/test_work_split.py tests/test_work_assign.py tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
python scripts/work.py split TASK-AR-372 --json
python scripts/work.py split --help
```

## Handoff

Report `work split` syntax, proposal-only outputs, readiness self-check
behavior, and remaining approved-apply/UI gaps.

## Stop Boundary

Stop after split proposal generation is implemented, verified, and recorded.
Leave approved apply, automatic dispatch, and Work Explorer UI to separate
records.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T14:32:00+09:00`
- Resolution: `done`
- Actual hours: `0.6`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-unit-task-ar-372-009-20260612143100.json`
<!-- work-close:end -->
