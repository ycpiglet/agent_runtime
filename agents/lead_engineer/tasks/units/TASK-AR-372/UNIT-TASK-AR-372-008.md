---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-372-008
work_uid: 6d6a32bd-5eb4-48da-b0e7-f3a3f74f9ef2
kind: unit
parent_id: TASK-AR-372
unit_id: UNIT-TASK-AR-372-008
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
verification_status: passed
team: agent-runtime-core
owner: lead_engineer
created_at: 2026-06-12T14:12:12+09:00
updated_at: 2026-06-12T14:15:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-06-12-work-criteria-command.md
created_by: codex
summary: Add proposal-only work assign command for team and owner routing gaps.
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - planning_boundary
context: Add the assignment planner tool surface requested for Work Items by recommending team and owner metadata while keeping automatic dispatch and claim creation behind approved planning apply.
inputs:
  - scripts/work.py
  - tests/test_work_assign.py
  - agents/project/TEAMS.md
  - scripts/task_claim_dispatcher.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - tests/test_work_assign.py
  - agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-008.md
  - reviews/REVIEW-2026-06-12-work-assign-command.md
scope: Implement work.py assign as a deterministic proposal-only recommender; do not mutate source work items, create task claims, auto-dispatch workers, or implement work split.
acceptance:
  - work.py assign recommends team and owner metadata for a work item from local routing context.
  - If team or owner metadata is missing, the command writes a B-mode planning proposal JSON and draft markdown.
  - The command does not mutate the source work item or create task claim records.
  - If team and owner are already explicit, the command returns pass and writes no proposal.
  - Tests cover proposal creation, pass-without-proposal, and missing work failure.
verification:
  - python -m py_compile scripts/work.py
  - pytest tests/test_work_assign.py tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
  - python scripts/work.py assign UNIT-TASK-AR-372-008 --json
  - python scripts/work.py assign --help
handoff: Report work assign syntax, proposal-only outputs, assignment heuristics, and remaining split gap.
stop_condition: Stop after assignment proposal generation is implemented, verified, and recorded; leave split and approved apply/dispatch behavior to separate units.
verified_at: 2026-06-12T14:14:09+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-372-008-20260612141409.json
resolution: done
completed_at: 2026-06-12T14:15:00+09:00
closed_by: codex
actual_hours: 0.5
actual_tokens: 0
---

# UNIT-TASK-AR-372-008 - Proposal-Only Work Assign Command

## Context

Add the assignment planner tool surface requested for Work Items by recommending
team and owner metadata while keeping automatic dispatch and claim creation
behind approved planning apply.

## Inputs

- scripts/work.py
- tests/test_work_assign.py
- agents/project/TEAMS.md
- scripts/task_claim_dispatcher.py
- agents/lead_engineer/tasks/TASK-AR-372.md

## Target Files

- scripts/work.py
- tests/test_work_assign.py
- agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-008.md
- reviews/REVIEW-2026-06-12-work-assign-command.md

## Scope

Implement `work.py assign` as a deterministic proposal-only recommender. Do not
mutate source work items, create task claims, auto-dispatch workers, or
implement `work split` behavior in this unit.

## Steps

1. Read the target work item and local routing context from Work metadata and
   `agents/project/TEAMS.md`.
2. Recommend a team and owner from target paths, tags, and work text.
3. Include active claim workload counts as recommendation context.
4. Write a B-mode proposal JSON and draft only when assignment metadata is
   incomplete.
5. Add regression tests for proposal creation, no-op pass, and missing work.

## Acceptance Criteria

- `python scripts/work.py assign UNIT-TASK-AR-901-001 --json` writes a B-mode
  proposal in tests when team or owner metadata is missing.
- The proposal includes `mode: B`, `status: proposed`, `action_type:
  plan_update`, source refs, target files, verifier list, owner boundary,
  recommended team, recommended owner, and workload context.
- The source work item text is unchanged by proposal generation.
- The command does not create files under `agents/runtime/task_claims/`.
- If team and owner are explicit, the command returns `work-assign: pass` and
  writes no planning outbox files.
- Missing work returns nonzero and writes nothing.

## Verification

```powershell
python -m py_compile scripts/work.py
pytest tests/test_work_assign.py tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
python scripts/work.py assign UNIT-TASK-AR-372-008 --json
python scripts/work.py assign --help
```

## Handoff

Report `work assign` syntax, proposal-only outputs, assignment heuristics, and
the remaining `split` gap.

## Stop Boundary

Stop after assignment proposal generation is implemented, verified, and
recorded. Leave `split` and approved apply/dispatch behavior to separate units.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T14:15:00+09:00`
- Resolution: `done`
- Actual hours: `0.5`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-unit-task-ar-372-008-20260612141409.json`
<!-- work-close:end -->
