---
id: REVIEW-2026-07-24-task-ar-622-t3-current-head-revalidation
title: TASK-AR-622 current-head T3 revalidation
kind: planning
status: approved
date: 2026-07-24
task_id: TASK-AR-622
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
decision: replan
---

# TASK-AR-622 Current-Head T3 Revalidation

## Current objective

Revalidate the lossless work-frontmatter scalar plan at current main before
dispatching `UNIT-TASK-AR-622-001`.

## Drift finding

T2 correctly refused dispatch because `scripts/work.py` changed after the prior
T3 snapshot. The intervening change is limited to the verification subprocess
execution boundary:

- Windows now passes the original command string directly to `CreateProcess`
  without an implicit `cmd.exe`.
- POSIX retains the existing shell execution contract.
- an `OSError` is represented as a failed command result with return code 127.

No intervening change altered `_frontmatter_scalar`, `_frontmatter`,
`_rewrite_frontmatter`, `backlog_board.strip_comment`,
`backlog_board.parse_frontmatter`, or `backlog_board.parse_header_block`.

## Current-head defect check

The registered defect remains present:

- registration already encodes new hash-bearing scalar values safely;
- quoted or encoded values already survive verify and close rewrites;
- an unsafe legacy raw line such as `origin_ref: source #274` is still passed
  through `strip_comment` before lifecycle code sees it;
- verify and close therefore still accept the truncated parser-visible value
  and can rewrite the record without detecting the discarded suffix.

## T3 decision

The existing hierarchy, unit scope, acceptance criteria, and stop boundary
remain valid. Dispatch only `UNIT-TASK-AR-622-001`.

Implementation must:

1. add deterministic raw-record regressions for verify and close before changing
   production code;
2. reject unsafe legacy unquoted hash-bearing scalars before any lifecycle
   rewrite;
3. preserve registration and rewrite behavior for safely quoted or encoded
   scalar and list values;
4. avoid inferred suffix recovery, bulk historical migration, evidence-schema
   changes, and unrelated command-execution changes.

## Re-anchor set

- `reviews/REVIEW-2026-07-24-task-ar-622-t3-current-head-revalidation.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`
- `scripts/backlog_board.py`

## Required verification

- `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY`
- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`
- `python scripts/owner_governance_gate.py`
