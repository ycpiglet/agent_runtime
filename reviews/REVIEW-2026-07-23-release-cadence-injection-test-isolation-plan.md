---
title: Release Cadence Injection Test Isolation Plan
date: 2026-07-23
signal: needs-fix
score: 94
tags: [planning, release-cadence, release-auto, ci-flake, test-isolation]
---

# Release Cadence Injection Test Isolation Plan

## Bottom Line

Two separate post-merge `main` CI attempts failed in cadence query-failure
injection tests with an observed injection count of zero. Both unchanged
reruns either passed or are being rerun. The tests isolate the loaded cadence
module's mutable `subprocess` facade, but still delegate every non-target query
to a real Git subprocess. A transient failure in an earlier, non-target query
can therefore short-circuit the scenario before the intended query is reached,
making the assertion report a false test failure.

This is a test-harness isolation defect, not evidence that the production
cadence error contract is wrong. Register a narrow task to make each injected
scenario supply deterministic successful answers for every non-target Git
query while preserving the exact retry-count and fail-loud assertions.

## Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| First distinct failure | fail | run `29970171133` attempt 1, Python 3.10: `test_each_partial_query_failure_invalidates_triggered_report[tag-time]`, expected 3 injected calls, observed 0 |
| First unchanged rerun | pass | run `29970171133` attempt 2; Python 3.10, 3.11, and 3.12 passed |
| Second distinct failure | fail | run `29970914790` attempt 1, Python 3.10: `test_partial_cadence_query_error_halts_even_when_commit_threshold_fires`, expected 6 injected diff calls, observed 0 |
| Shared harness boundary | exposed | both tests return `real_run(cmd, **kwargs)` for all non-target cadence queries |
| Production retry/error contract | covered | TASK-AR-613 and focused tests already prove retry, sanitized diagnostics, trigger-error, and genuine no-tag behavior |

## Decision

Replace real-Git fallback inside the two query-failure injection families with
a deterministic query-response fixture or helper. The helper must model the
minimum valid tagged repository answers required by `build_report`, then fail
only the selected query. Keep fixture repository creation only where the
release-auto orchestration needs package and evidence files; cadence query
answers themselves must not depend on the runner's Git process after failure
injection begins.

## Scope Boundary

- Do not change production retry counts, cadence thresholds, bump semantics, or
  release-auto result classification.
- Do not weaken or remove the exact three-attempt and six-diff-call assertions.
- Do not paper over the failure with broad retries around pytest or CI.
- Change only the focused test harness unless failure-first evidence proves a
  production seam is necessary; stop and replan before any production change.

## Verification

- Both affected injection families pass repeatedly without spawning Git for
  non-target cadence queries.
- The selected query still fails exactly three times, or both selected diff
  queries fail exactly six times.
- Reports remain `git-query-error`, never `watch`, `pass`, or `not-triggered`.
- Focused cadence/release-auto tests and the full suite pass on supported Python
  versions before release.
