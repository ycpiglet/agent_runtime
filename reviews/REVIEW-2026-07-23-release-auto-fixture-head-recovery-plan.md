---
title: Release-Auto Fixture HEAD Recovery Plan
date: 2026-07-23
signal: needs-fix
score: 91
tags: [planning, ci-flake, release-auto, test-fixture, github-320]
---

# Release-Auto Fixture HEAD Recovery Plan

## Bottom Line

Post-merge main run `29945156772` failed on Python 3.10 while constructing a
40-commit release-auto test fixture. The 37th `git commit --allow-empty`
returned rc 128 with `fatal: could not parse HEAD`; the suite otherwise had
2,142 passing tests. PR #319's immediately preceding three-version CI passed
on the same product code. This is a separate test-fixture mutation reliability
defect, recorded as GitHub issue 320, not a cadence decision regression.

## Evidence

| Field | First-attempt result |
| --- | --- |
| Main SHA | `3defd445636f6fee39d1c8a151681d3f06992b38` |
| Run / job | `29945156772` / `89008561485` |
| Test | `test_decision_record_is_agent_council_noncritical` |
| Command | `git commit --allow-empty -q -m "chore: tick 36"` |
| Failure | rc 128, `fatal: could not parse HEAD` |
| Suite | 1 failed, 2142 passed, 4 skipped |

The fixture helper currently executes every Git mutation once. Its diagnostic
path is sanitized and useful, but it has no recovery boundary for a known
transient failure that occurs before the commit can advance HEAD.

## Decision

Register a narrow P0 test-harness unit. Add failure-first coverage for the
recognized transient `could not parse HEAD` result, retry that exact pre-commit
failure with a short bound, and keep every unknown or deterministic failure as
an immediate loud assertion. Do not add retries to product Git operations and
do not retry ambiguous failures that may have committed successfully.

## Scope Boundary

- Modify only the release-auto test fixture helper and its tests.
- Preserve sanitized command/stdout/stderr evidence.
- Do not retry arbitrary non-zero Git mutations.
- Do not change cadence, release-auto, semantic-version, or CI policy behavior.

## Verification

- Failure-first test proves the recognized transient currently raises.
- One recognized failure followed by success makes exactly two attempts.
- Three recognized failures exhaust with sanitized attempt evidence.
- Unknown failures make exactly one attempt and fail loud.
- Full release-auto/cadence tests, repeated fixture construction, and taskset
  gates pass before independent W4b.
