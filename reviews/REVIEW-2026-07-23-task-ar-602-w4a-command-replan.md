---
id: REVIEW-2026-07-23-task-ar-602-w4a-command-replan
title: TASK-AR-602 W4a command portability replan
kind: planning
status: approved
date: 2026-07-23
task_id: TASK-AR-602
unit_id: UNIT-TASK-AR-602-001
decision: proceed
---

# TASK-AR-602 W4a command portability replan

## Current objective

Complete W4a against the already published and independently pre-approved
v0.7.0 release without weakening the tag-target assertion.

## Evidence that triggered replan

`reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202.json` records:

- release cascade pass at 0.7.0;
- full pytest pass: 2,198 passed, 6 skipped, 0 failed in 814.29 seconds;
- annotated tag type pass;
- failure of the declared `git rev-parse 'v0.7.0^{}'` only after the Windows
  shell consumed its caret/quote sequence;
- an owner-governance nonzero result that did not reproduce when rerun directly
  after the evidence write.

The tag itself was independently read back through GitHub's API as an annotated
tag object targeting commit `23c4be4059dc4c12d107ac8cc5fefa795dfab7f8`.

## Decision

Replace only the task/unit tag peel command with
`git rev-parse v0.7.0~0`. Git defines `~0` as the commit itself after resolving
the revision, so this keeps the same acceptance meaning while avoiding a
Windows shell metacharacter. All other registered commands remain unchanged
and must rerun.

The runner defect is not fixed inside TASK-AR-602. It is registered separately
as `TASK-AR-621` under
`TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY` with a T0 assumption snapshot.

## Stop conditions

- Stop if the portable command does not resolve to the approved merge commit.
- Stop if owner governance fails again or any pytest test fails.
- Preserve the failed evidence record and link it alongside the passing result.

