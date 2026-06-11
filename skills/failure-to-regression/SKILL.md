---
name: failure-to-regression
description: Use when a repeated failure, compound note, review finding, or Owner correction should become a regression fixture, gate, or explicit watch state.
---

# Failure To Regression

## Required Inputs

1. casebook entry in `agents/project/casebooks/failure-and-compound-casebook.md`.
2. Reproduction command, or an explicit non-repro reason.
3. Owner boundary and affected gate.
4. Proposed fixture, gate, task proposal, or accepted_watch state.

## Workflow

1. Record `symptom`, `trigger`, `dedupe_key`, `recurrence_count`, and
   `linked_regression_fixture`.
2. If a reproduction command exists, add or update the smallest deterministic
   fixture that would have caught the failure.
3. If no deterministic reproduction exists, record the non-repro reason and
   route to proposal or accepted_watch.
4. Verify with the named gate before marking prevention status `verified`.

## Boundaries

- Owner-gated, release, version, external, destructive, prod-data, and
  cost-bearing cases stay proposal-only until approved.
- Do not close `needs_enforcement` entries as notes without a gate, fixture,
  task proposal, or accepted_watch reason.
