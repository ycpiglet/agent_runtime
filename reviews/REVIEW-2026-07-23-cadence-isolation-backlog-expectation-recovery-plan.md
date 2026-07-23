---
title: Cadence Isolation Backlog Expectation Recovery Plan
date: 2026-07-23
signal: needs-fix
score: 96
tags: [planning, ci-recovery, backlog, taskset-classification, task-ar-619]
---

# Cadence Isolation Backlog Expectation Recovery Plan

## Bottom Line

TASK-AR-619 PR #336 run `29973935786` reached `2193 passed` and failed one
exact-equality regression in `tests/test_backlog_board_tasksets.py`. The
canonical classifier correctly discovered
`TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION`, but the hand-maintained
expected taskset set did not include it. This is separate from the cadence
injection implementation and must be recovered as an adjacent, test-only CI
task before PR #336 can obtain its required three-version matrix.

## Decision

Register a narrow recovery task that adds both newly registered taskset IDs—the
cadence injection taskset and this recovery taskset—to the exact expected set.
Preserve exact equality, production classification, and every other expected
ID. No production file changes are authorized.

## Evidence

- PR: `#336`
- workflow run: `29973935786`, attempt 1
- Python 3.10 result: `1 failed, 2193 passed, 4 skipped`
- failure: `test_real_backlog_tasks_are_classified_into_registered_task_sets`
- sole extra classifier item: `TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION`
- Python 3.11/3.12 were canceled by matrix fail-fast after reaching package tests

## Scope Boundary

- Change only `tests/test_backlog_board_tasksets.py` plus lifecycle evidence.
- Keep the assertion as exact set equality.
- Do not change classifier behavior, backlog generation, or taskset metadata.
- Include this recovery taskset's own ID so registration does not create a
  second expectation mismatch.

## Verification

- Focused real-backlog exact-set test passes.
- All backlog taskset tests pass.
- Taskset gate passes.
- Independent W4b confirms only the expected set changed and CI passes before
  integration.
