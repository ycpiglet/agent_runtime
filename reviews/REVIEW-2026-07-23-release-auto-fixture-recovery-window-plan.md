---
title: Release-Auto Fixture Recovery Window Hardening Plan
date: 2026-07-23
signal: needs-fix
score: 94
tags: [planning, ci-flake, release-auto, test-fixture, github-320]
---

# Release-Auto Fixture Recovery Window Hardening Plan

## Bottom Line

Main run `29953104959` failed on Python 3.12 after the TASK-AR-615 helper
correctly recognized the exact pre-commit `fatal: could not parse HEAD`
response but exhausted all three attempts. The failing fixture was again
building `chore: tick 36`; stdout was empty and all three results were rc 128.
PR run `29952887714` had passed all Python versions on the same product code.

The classifier is behaving correctly, but its 0.15-second total recovery
window is shorter than the observed runner transient. This is a bounded test
fixture reliability follow-up, not a reason to broaden retryable mutation
classes or change product Git behavior.

## Evidence

| Field | Main first-attempt result |
| --- | --- |
| Main SHA | `92f0dae57bd589e95f79198c50b5c2dd0022c2fa` |
| Run | `29953104959` |
| Python | `3.12` |
| Test | `test_each_critical_flag_halts_for_owner[destructive_or_irreversible_operation]` |
| Command | `git commit --allow-empty -q -m "chore: tick 36"` |
| Failure | rc 128, empty stdout, exact `fatal: could not parse HEAD` |
| Recovery evidence | `attempts: 3` (all recognized, all exhausted) |
| Suite | 1 failed, 2158 passed, 4 skipped |

## Decision

Register a new P0 unit with failure-first coverage for three recognized
failures followed by success. Extend the retry window with a small capped
backoff while keeping the existing exact classifier unchanged. Prove that an
ambiguous response still stops immediately, permanent recognized failure
still exhausts loudly, and three synthetic pre-commit failures followed by a
real commit advance HEAD exactly once.

## Scope Boundary

- Modify only the release-auto test fixture helper and focused tests.
- Keep the exact command/rc/stdout/stderr classifier unchanged.
- Keep a strict attempt and elapsed-delay ceiling.
- Do not retry arbitrary Git mutations or post-commit ambiguity.
- Do not change release cadence, semantic versioning, release-auto product
  behavior, or CI policy.

## Verification

- Failure-first: three recognized failures followed by success currently
  raises at attempt three.
- Hardened helper recovers on the fourth call with the recorded capped
  backoff, without duplicate commits.
- Permanent recognized failure exhausts at the new bound with sanitized
  attempts evidence; all ambiguous variants remain single-attempt failures.
- Full release-auto/cadence tests, backlog taskset expectations, and the
  taskset work gate pass before independent W4b and first-attempt CI.
