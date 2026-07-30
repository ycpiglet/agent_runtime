---
id: REVIEW-2026-07-30-task-ar-653-post-task-ar-652-t3-replan
title: TASK-AR-653 post-TASK-AR-652 T3 replan
kind: replan
status: approved
signal: pass
date: 2026-07-30
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
priority: P1
predecessor_commit: 1a18a3a6c21dc2ca1e5d58b5e9ebbf216ecaf3d8
---

# TASK-AR-653 Post-TASK-AR-652 T3 Replan

## Decision

TASK-AR-652 is locally integrated, independently approved, closed, and
compounded. Revalidate the operability plan at TASK-AR-653 and dispatch only
`UNIT-TASK-AR-653-001` in a fresh claim/worktree.

The current read-only Scribe evaluation is the failure baseline:

- `STATUS.md` contains 773 hot items and is `overdue`;
- the generated projection is `fresh`;
- only 10 items are selected; yet
- `readiness=ready` and `closure_blocking=false`.

TASK-AR-653 must make those states truthful without autonomously rewriting
`STATUS.md` or any consumer-owned source.

## Executable Target Clarification

The first W2 preflight refused the claim before mutation because
`tests/test_session_start_hook.py` does not exist and claim footprints require
existing paths. Directly running
`src/agent_runtime/templates/project/scripts/test_session_start_hook.py` from
the Runtime checkout fails because that fixture expects a rendered host root.
Rendered-host behavior remains covered by `tests/test_template_smoke.py`.

The unit footprint is expanded before claim creation to include the root
mirrors for Scribe and closure, both session-start hook copies,
`src/agent_runtime/doctor.py`, and the template smoke suite. The existing
`tests/test_session_continuity_hooks.py` is the executable root integration
suite for session-start behavior and replaces the impossible target. No claim
or worktree was created by the refused dispatch. This is a planning
clarification only; it does not authorize writes outside the Runtime
repository.

## Implementation Order

1. Add failure-first tests for projection-only readiness, missing active
   task/claim coverage, active/no-touch cleanup exclusion, invalid cleanup
   receipts, and Scribe authority limits.
2. Separate source-debt, projection-freshness, active-coverage, cleanup-plan,
   and cleanup-outcome state.
3. Generate a bounded deterministic cleanup plan that selects cold history
   only and never chooses meaning when records conflict.
4. Validate a cleanup receipt against source before/after digests and the
   resulting hot count.
5. Keep selective Scribe routing on the low-cost policy introduced by
   TASK-AR-652 while retaining canonical decisions with the owning role.
6. Run W4a, then require a distinct W4b before release and local integration.

## Acceptance Interpretation

- A fresh projection is a faithful bounded view, not proof that source debt
  was cleared.
- Active work means canonical active task and non-overlay claim identities;
  each must be represented or explicitly surfaced as missing coverage.
- A cleanup plan is proposal/evidence only. It cannot write a host-owned
  source.
- A cleanup receipt is valid only when its before/after bindings and outcome
  agree with the actual files under evaluation.
- Raw prompt text, secrets, and absolute host paths must not enter portable
  receipts.

## Boundaries

- Runtime repository only; Bean Wiki, Allimbot, and Autofolio primaries remain
  read-only until the observation-only pilot phase.
- No credential access, live provider call, package installation, notification
  delivery, database/broker/order action, deploy, push, PR, tag, version bump,
  publication, or release.
- Stop rather than compressing active/no-touch records or resolving conflicting
  host meaning automatically.
