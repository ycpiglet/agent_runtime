---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-372-007
work_uid: e8cd82a3-3990-4273-ad73-03727fd97544
kind: unit
parent_id: TASK-AR-372
unit_id: UNIT-TASK-AR-372-007
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-06-12T13:51:49+09:00
updated_at: 2026-06-12T13:55:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-06-12-work-close-command.md
created_by: codex
summary: Add proposal-only work criteria evaluator for acceptance-to-verification gaps.
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - planning_boundary
context: Add the first B-mode planner tool surface after deterministic registration, verification, and closeout by evaluating whether work item acceptance criteria are backed by executable verification commands.
inputs:
  - scripts/work.py
  - tests/test_work_criteria.py
  - agents/project/PLANNING-LOOP-CONTRACT.md
  - schemas/planning-proposal.schema.json
  - agents/lead_engineer/tasks/TASK-AR-372.md
target_files:
  - scripts/work.py
  - tests/test_work_criteria.py
  - agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-007.md
  - reviews/REVIEW-2026-06-12-work-criteria-command.md
scope: Implement work.py criteria as a proposal-only B-mode evaluator; do not auto-apply criteria changes, implement LLM generation, split, assign, or Work Explorer UI.
acceptance:
  - work.py criteria evaluates acceptance criteria and executable verification commands for a work item.
  - If a criterion lacks executable verification, the command writes a planning proposal JSON under agents/planning/outbox and a draft under agents/planning/drafts.
  - The command does not mutate the source task or unit record.
  - If all criteria have executable verification coverage, the command returns pass and writes no proposal.
  - Tests cover proposal creation, pass-without-proposal, and missing work failure.
verification:
  - python -m py_compile scripts/work.py
  - pytest tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
  - python scripts/work.py criteria UNIT-TASK-AR-372-007 --json
  - python scripts/work.py criteria --help
handoff: Report work criteria syntax, proposal-only outputs, and remaining split/assign gaps.
stop_condition: Stop after criteria proposal generation is implemented, verified, and recorded; leave split and assign to separate planner-gated units.
verified_at: 2026-06-12T13:54:00+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-372-007-20260612135400.json
resolution: done
completed_at: 2026-06-12T13:55:00+09:00
closed_by: codex
actual_hours: 0.5
actual_tokens: 0
---

# UNIT-TASK-AR-372-007 - Proposal-Only Work Criteria Command

## Context

Add the first B-mode planner tool surface after deterministic registration,
verification, and closeout by evaluating whether work item acceptance criteria
are backed by executable verification commands.

## Inputs

- scripts/work.py
- tests/test_work_criteria.py
- agents/project/PLANNING-LOOP-CONTRACT.md
- schemas/planning-proposal.schema.json
- agents/lead_engineer/tasks/TASK-AR-372.md

## Target Files

- scripts/work.py
- tests/test_work_criteria.py
- agents/lead_engineer/tasks/units/TASK-AR-372/UNIT-TASK-AR-372-007.md
- reviews/REVIEW-2026-06-12-work-criteria-command.md

## Scope

Implement `work.py criteria` as a proposal-only B-mode evaluator. Do not
auto-apply criteria changes, implement LLM generation, `split`, `assign`, or
Work Explorer UI behavior in this unit.

## Steps

1. Parse acceptance criteria and verification commands from work item
   frontmatter or body sections.
2. Identify criteria that have no executable verification command.
3. Write a planning proposal JSON under `agents/planning/outbox/` and a draft
   under `agents/planning/drafts/` only when gaps exist.
4. Keep the source work item unchanged.
5. Add regression tests for proposal creation, no-gap pass, and missing work.

## Acceptance Criteria

- `python scripts/work.py criteria UNIT-TASK-AR-901-001 --json` writes a B-mode
  proposal in tests when a unit has acceptance criteria but no executable
  verification.
- The proposal includes `mode: B`, `status: proposed`, `action_type:
  plan_update`, source refs, target files, verifier list, and owner boundary.
- The source work item text is unchanged by proposal generation.
- If executable verification exists, the command returns `work-criteria: pass`
  and writes no planning outbox files.
- Missing work returns nonzero and writes nothing.

## Verification

```powershell
python -m py_compile scripts/work.py
pytest tests/test_work_criteria.py tests/test_work_close.py tests/test_work_verify.py -q
python scripts/work.py criteria UNIT-TASK-AR-372-007 --json
python scripts/work.py criteria --help
```

## Handoff

Report `work criteria` syntax, proposal-only outputs, and remaining `split` /
`assign` gaps.

## Stop Boundary

Stop after criteria proposal generation is implemented, verified, and recorded.
Leave `split` and `assign` to separate planner-gated units.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T13:55:00+09:00`
- Resolution: `done`
- Actual hours: `0.5`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-unit-task-ar-372-007-20260612135400.json`
<!-- work-close:end -->
