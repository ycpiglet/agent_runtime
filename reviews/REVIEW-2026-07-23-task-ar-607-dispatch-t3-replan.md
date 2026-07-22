---
title: TASK-AR-607 Dispatch T3 Replan
date: 2026-07-23
signal: pass
score: 95
task_id: TASK-AR-607
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-607, github-297, ci-flake]
---

# TASK-AR-607 Dispatch T3 Replan

## Bottom Line

TASK-AR-606 is fully closed and the next registered unit is TASK-AR-607 for
GitHub issue 297. Current and historical CI evidence confirms a collection-
order flake around release helpers. The narrow reproducible defect candidate is
the test loader: its dynamically loaded release-cadence module retains the
process-global `subprocess` module, so monkeypatching `module.subprocess.run`
mutates the same object used by every test in the pytest process. Dispatch a
failure-first isolation regression and change only this test boundary unless
the probe disproves the hypothesis.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| W0 | pass | Active claims 0, one clean main worktree, no divergent task branches |
| Prior task | complete | TASK-AR-606 PR 312 and W6 PR 313 merged; main CI runs `29931322171` and `29932250263` passed on first attempts |
| Worker readiness | pass | `UNIT-TASK-AR-607-001` declares exact targets, unchanged oracle, 100-run acceptance, handoff, and stop boundary |
| Existing failure | confirmed | Run `29921668702` attempt 1 returned release-cadence rc 0 with empty stdout; a later attempt failed release-auto before the next rerun passed |
| Additional order evidence | confirmed | Run `29927077404` attempt 1 returned release-auto `not-triggered` for a critical flag; attempt 2 passed unchanged |
| Scope drift | none | Isolate test-owned module state; do not relax cadence thresholds, retry assertions, or production error handling |

## Decision

Add a failure-first regression proving that a monkeypatch applied to the
dynamically loaded release-cadence module cannot replace the parent pytest
process's `subprocess.run`. Then give each loaded test module a private narrow
subprocess facade. Preserve the transient failure oracle: exactly one spawn
raises, a subsequent real Git query succeeds, the proposal triggers, and no
query error remains. Production code changes require separate evidence from a
failing probe.

## Frontmatter Safety

TASK-AR-608 / GitHub issue 298 owns the quote-unaware frontmatter parser defect.
Until it lands, TASK-AR-607 metadata uses `GitHub issue 297` instead of a hash
form. Prose remains unchanged and no parser fix is included here.

## Anchors To Refresh

- `reviews/REVIEW-2026-07-23-task-ar-607-dispatch-t3-replan.md`
- `scripts/work.py`
- `scripts/task_claim_dispatcher.py`
- `tests/test_release_cadence_trigger.py`
- `scripts/release_cadence_trigger.py`
- `tests/test_release_auto_noncritical.py`

## Verification Boundary

- Commit the isolation assertion while it fails against the shared module.
- Make only the dynamic test loader state private.
- Run the release-cadence file and the release-auto collection-order pair.
- Run the transient recovery test at least 100 times without rerun recovery.
- Require independent W4b and adversarial CI-flake review before integration.
