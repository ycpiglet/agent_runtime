---
title: Release Cadence Query Recovery Plan
date: 2026-07-23
signal: needs-fix
score: 90
tags: [planning, release-cadence, release-auto, ci-flake, github-316]
---

# Release Cadence Query Recovery Plan

## Bottom Line

PR 315 CI run `29936269777` attempt 1 proved a remaining failure mode after
TASK-AR-607: a repository with a valid baseline tag and 40 commits was reported
as `not-triggered` by the release-auto orchestrator. The unchanged attempt 2 and
post-merge main matrix passed. This is not the dynamic test-module monkeypatch
leak fixed by TASK-AR-607; it is a separate cadence query recovery defect and
must be closed before v0.7.0.

## Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Valid cadence fixture | fail | `test_noncritical_path_reaches_release_in_dry_run` expected `executed`, received `not-triggered` |
| First CI attempt | fail | run `29936269777`, attempt 1, Python 3.12; 1 failed and 2121 passed |
| Unchanged retry | pass | run `29936269777`, attempt 2; Python 3.10, 3.11, and 3.12 passed |
| Post-merge main | pass | run `29936900984`; all three Python versions passed |
| Prior isolation fix | distinct | TASK-AR-607 changed only the dynamic test loader's private module facades |

## Decision

Register a narrow production-hardening task. Add failure-first coverage for a
transient non-zero Git query result followed by a valid answer. Preserve the
legitimate no-tag quiet path, but retry and surface other exhausted query
failures as `git-query-error` so release-auto fails loud rather than silently
skipping a release cycle. Keep root/template parity and the generated-host lock
current.

## Scope Boundary

- Do not change cadence thresholds or semantic version bump policy.
- Do not turn a genuinely untagged repository into an error.
- Do not weaken the release-auto `not-triggered` contract for a genuinely quiet
  repository.
- Stop and replan if reliable classification requires changing callers outside
  release cadence, release auto, and their existing shared helper consumers.

## Verification

- Failure-first simulated transient non-zero query recovers to a triggered
  report.
- Exhausted unexpected non-zero queries produce structured diagnostics and a
  release-auto `trigger-error` result.
- A deterministic no-tag response remains a quiet pass.
- Focused cadence/auto tests, root/template parity, host lock, repeated probes,
  and the full Python matrix pass before release.
