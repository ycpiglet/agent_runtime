---
status: implemented
origin_type: task_handoff
origin_ref: agents/lead_engineer/tasks/TASK-AR-618.md
tags:
  - task-ar-618
  - work-cli
  - selector-integrity
---

# TASK-AR-618 Exact Selector Precedence

## Outcome

The shared work-item resolver now treats an exact task ID as the canonical task record only. Exact unit IDs still search the unit tree, but more than one canonical match is a bounded ambiguity error instead of silently selecting the first path. Existing explicit relative and absolute path resolution remains first priority.

## Failure-First Evidence

- Commit `858ac9f2` adds the regression cases before the production change.
- Before the fix, the focused suite reported `5 failed, 15 passed`.
- Four failures reproduced exact task IDs being expanded into their descendant unit paths for `verify`, `close`, `assign`, and `criteria`.
- The fifth failure reproduced duplicate unit IDs being silently resolved to the first sorted path.

## Selector Precedence

| Selector | Candidate construction | Ambiguity behavior |
| --- | --- | --- |
| Existing explicit path | The referenced file only | Deterministic single path |
| Exact `TASK-*` ID | `agents/lead_engineer/tasks/<TASK>.md` only | Missing canonical task is not found |
| Exact `UNIT-*` ID | Every matching `agents/lead_engineer/tasks/units/*/<UNIT>.md` | More than one match is an error with sorted paths |
| Unknown selector | No candidates | Command-scoped not-found error |

## Implementation

- Commit `c4b384ff` removes descendant-unit expansion from exact task candidate construction.
- The common loader now rejects every multi-path result, including duplicate exact unit IDs.
- No `verify`, `close`, `assign`, or `criteria` command-specific mutation semantics changed.

## Verification

- `python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q` -> `20 passed in 8.70s`
- `python scripts/work_schema_gate.py --check` -> pass, zero findings and warnings

