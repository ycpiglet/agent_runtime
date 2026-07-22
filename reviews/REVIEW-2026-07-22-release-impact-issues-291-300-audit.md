---
type: planning
title: Release-impact issue audit for GitHub 291 through 300
date: 2026-07-22
signal: action
score: 96
tags: [planning-record, release-impact, downstream-report, v0.7.0]
---

# Release-impact issue audit for #291 through #300

## Bottom Line

The numeric range contains eight open defects and two closed pull requests. Issue #291 is already
registered as `TASK-AR-600`. Issues #293, #294, #295, #297, #298, #299, and #300 remain reproducible
on main `467d2f7` and require new worker-ready tasks before v0.7.0. PR #292 only registered
`TASK-AR-600`; PR #296 delivered ordered taskset behavior and explicitly left #295 out of scope.

## Audit Matrix

| Number | Kind/state | Main read-back | Routing decision |
| --- | --- | --- | --- |
| #291 | High bug/open | `auto_merge` false-success path remains registered but unimplemented | Execute `TASK-AR-600` first |
| #292 | PR/closed | Registration-only PR for #291 | No duplicate work |
| #293 | Medium bug/open | taskset start persists internal `in_progress` alias | Register a focused status-persistence task |
| #294 | Medium bug/open | template dashboard imports absent `scripts/work.py` | Register a clean-template fallback task |
| #295 | Medium bug/open | both pre-commit hooks are mode `100644`; installers only set hooksPath | Register executable activation task |
| #296 | PR/closed | Ordered taskset implementation; body says #295 remains separate | No duplicate work |
| #297 | Medium bug/open | intermittent transient-spawn test boundary remains unchanged | Register deterministic isolation task |
| #298 | Medium bug/open | `strip_comment` is still quote-unaware | Register quote-aware parser task |
| #299 | High bug/open | allocator emits lowercase hex while dispatcher/audit regexes disagree | Register first in the new taskset |
| #300 | Medium bug/open | `_initiative_records` still ignores record `kind` | Register kind-aware classifier task |

## Execution Order

1. Complete `TASK-AR-600` because false merge success is the highest immediate external-state risk.
2. Fix #299 next because its producer/consumer identity mismatch blocks canonical work routing.
3. Fix #293 and #294 because they affect claim-first task start and every generated host session.
4. Fix #295 before release so Linux host governance hooks are actually active.
5. Fix #297, #298, and #300, then run the full release gates.
6. Only after every open release-impact issue is closed, claim release-only `TASK-AR-602`.

## Scope Boundaries

- Each issue receives one task and one worker-ready unit; unrelated refactors stay out of scope.
- Root/template pairs and the generated host lock must remain in parity whenever a managed template changes.
- No task may claim issue closure until focused tests, W4a, independent W4b, PR CI, merge read-back, and
  remote issue state are all evidenced.
- No v0.7.0 version bump, tag, release, or provider-live notification occurs in this remediation taskset.

## Action Board

| Action | Status |
| --- | --- |
| Execute `TASK-AR-600` for #291 | Next |
| Register and execute tasks for #293/#294/#295/#297/#298/#299/#300 | Next |
| Run `TASK-AR-602` only after the audit queue is closed | Planned |

