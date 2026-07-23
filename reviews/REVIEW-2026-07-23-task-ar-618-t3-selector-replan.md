---
title: TASK-AR-618 Exact Selector T3 Replan
date: 2026-07-23
signal: pass
score: 99
task_id: TASK-AR-618
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
review_type: dispatch-drift-replan
trigger: t2-anchor-drift
reviewed_by: codex-root
tags: [t3, work-cli, selector, ambiguity, data-integrity]
---

# TASK-AR-618 Exact Selector T3 Replan

## Bottom Line

T2 correctly blocked TASK-AR-618 after fifteen taskset anchors changed during
TASK-AR-617 completion and the subsequent CI-recovery integrations. The current
code still reproduces the registered defect, and none of the intervening
`scripts/work.py` changes altered selector resolution. The original hierarchy,
scope, and stop boundary therefore remain valid.

Re-anchor the taskset at the current verified main and dispatch only
`UNIT-TASK-AR-618-001`.

## Current-Head Evidence

- `python scripts/work.py criteria TASK-AR-618 --json` fails with
  `work-criteria:ambiguous` and lists the canonical task plus its descendant
  unit.
- `_candidate_work_paths` still appends the canonical task path and every
  `UNIT-*.md` below that task whenever the selector matches `TASK_DISPLAY_RE`.
- `_load_work_item` still suppresses the multi-match ambiguity check for unit
  IDs, so duplicate unit IDs in different task directories can select the
  first sorted path instead of failing closed.
- The existing verify, close, assign, and criteria focused suite passes 14/14,
  confirming that current tests do not cover exact task selection with
  descendants or duplicate unit IDs.
- Commits after registration changed frontmatter serialization and downstream
  decoding only; no selector-resolution commit landed.

## Revised Selector Contract

| Selector form | Required result |
|---|---|
| Existing explicit relative or absolute path | Resolve that exact file only |
| Exact `TASK-AR-N` with canonical task file | Resolve the task file only; do not discover descendants |
| Exact `UNIT-TASK-AR-N-N` with one canonical match | Resolve that unit only; do not fall through to its parent |
| Exact unit ID with multiple canonical matches | Fail with stable `ambiguous` paths |
| Missing exact task or unit | Fail with stable `not-found` text |

## Implementation Scope

- Refine only the shared candidate/load boundary in `scripts/work.py`.
- Add failure-first exact-task cases for verify, close, assign, and criteria
  using a task that has one or more descendant units.
- Add bounded duplicate-unit coverage and retain existing explicit-path,
  exact-unit, and missing-record behavior.
- Do not change command-specific mutation, verification, proposal, hierarchy,
  or frontmatter contracts.

## Verification

- `python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q`
- `python scripts/work_schema_gate.py --check`
- Independent W4b must inspect the selector precedence table, prove duplicate
  unit failure, and verify no command-specific semantic drift before PR CI.

## T3 Decision

The plan remains executable by the registered worker tier. Record current
hashes for this review, the original design, registration/dispatch flow, and
all target files from both work-CLI integrity units, then require a clean T2
check before creating the TASK-AR-618 claim.
