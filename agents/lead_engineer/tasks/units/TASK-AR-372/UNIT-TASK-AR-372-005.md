---
unit_id: UNIT-TASK-AR-372-005
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
completed_at: 2026-06-12T13:13:09+09:00
verification_status: passed
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
context: Add deterministic verification execution so generated unit specs can be measured and recorded without hand-written evidence.
inputs:
  - scripts/work.py
  - tests/test_work_verify.py
  - scripts/evidence_index_generator.py
  - agents/project/WORK-SCHEMA.yml
target_files:
  - scripts/work.py
  - tests/test_work_verify.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
  - reviews/REVIEW-2026-06-12-work-verify-command.md
scope: Implement work.py verify for existing task/unit verification commands and evidence records; do not implement work close or AI split/criteria/assign.
acceptance:
  - work.py verify locates a unit by unit_id and runs its frontmatter verification commands.
  - Each command result records status, return code, stdout, stderr, started_at, and finished_at.
  - A verification evidence JSON record is written under reviews/ and included in reviews/INDEX.md.
  - The verified work item frontmatter is updated with verification_status, verified_at, verified_by, and evidence_refs.
  - Failed commands return nonzero and still write failed evidence.
verification:
  - python -m py_compile scripts\\work.py
  - pytest tests/test_work_verify.py tests/test_work_registration.py tests/test_now.py -q
  - python scripts/work.py --help
handoff: Report work verify syntax, evidence path behavior, and remaining work close gap.
stop_condition: Stop after deterministic verification evidence is written; leave work close and AI planner proposal tools to separate units.
verified_at: 2026-06-12T13:13:09+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-unit-task-ar-372-005-20260612131309.json
updated_at: 2026-06-12T13:13:09+09:00
---

# UNIT-TASK-AR-372-005 - Deterministic Work Verify Command

## Context

`work new` can now create initiative, taskset, task, and unit records. The next
missing piece is measured verification: a unit should carry executable
verification commands, and a deterministic tool should run those commands and
write evidence rather than leaving verification as prose.

## Inputs

- `scripts/work.py`
- `tests/test_work_verify.py`
- `scripts/evidence_index_generator.py`
- `agents/project/WORK-SCHEMA.yml`
- `agents/lead_engineer/tasks/TASK-AR-372.md`

## Target Files

- `scripts/work.py`
- `tests/test_work_verify.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`
- `reviews/REVIEW-2026-06-12-work-verify-command.md`
- `owner-docs.yml`
- `BACKLOG-BOARD.md`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.json`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.md`
- `reviews/INDEX.md`

## Scope

In scope: `scripts/work.py verify <id>`, unit/task lookup, verification command
execution, JSON evidence record creation, verified work-item frontmatter update,
evidence index refresh, pass/fail exit status, and focused tests.

Out of scope: work item closeout, actuals/cost capture, automatic criteria
generation, assignment, approval workflows, and broad migration of historical
tasks.

## Steps

1. Add a `verify` subcommand to the Work CLI.
2. Locate a unit by `unit_id` or explicit path and read its frontmatter
   `verification` commands.
3. Execute commands under the selected repository root.
4. Write `reviews/VERIFY-*.json` with command results.
5. Update the unit frontmatter with verification status and evidence refs.
6. Add regression tests for pass, fail, and missing-command behavior.

## Acceptance Criteria

- `python scripts/work.py verify UNIT-TASK-AR-901-001 --json` runs the unit's
  verification commands in tests and returns pass for zero exit codes.
- Failed verification commands return nonzero and write failed evidence.
- Missing verification commands fail without creating `reviews/`.
- Passing verification updates `verification_status: passed`, `verified_at`,
  `verified_by`, and `evidence_refs`.
- `reviews/INDEX.md` includes the generated verification evidence path.

## Verification

```powershell
python -m py_compile scripts\work.py
pytest tests/test_work_verify.py tests/test_work_registration.py tests/test_now.py -q
python scripts/work.py --help
```

## Handoff

Use `python scripts/work.py verify <unit_id-or-path> --json` to run a work
item's declared verification commands and record evidence. The command is
deterministic; it does not infer missing verification criteria.

## Completion Evidence

- `python scripts/work.py verify UNIT-TASK-AR-372-005 --now 2026-06-12T13:13:09+09:00 --actor codex --json`
- `python scripts/evidence_index_generator.py --check`

## Stop Boundary

Stop after verification evidence generation. Continue into `work close`,
actuals, costs, or proposal-gated AI planner tools only under separate units.