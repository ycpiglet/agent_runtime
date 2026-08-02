---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-taskset-ar-v080-post-ar654-plan-revalidation
title: v0.8 operability hardening post-AR-654 plan revalidation
date: 2026-08-03
created_at: 2026-08-03T00:15:00+09:00
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-v080-post-ar654-revalidation-20260803
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: REVALIDATE_AR655_NEXT_WITHOUT_RELEASE_AUTHORITY
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 957582daa11a56a217eb04b4a57659ae60fbe7e2
candidate_tree: 0089a0aada59644cd5c495688b65fbcd0bb80544
release_authorized: false
tags: [taskset-revalidation, t2-dispatch, t3-replan, task-ar-654, task-ar-655, lease-bounds, release-blocker]
---

# v0.8 operability hardening post-AR-654 plan revalidation

## Decision

Revalidate `TASKSET-AR-V080-OPERABILITY-HARDENING` at exact local candidate
`957582daa11a56a217eb04b4a57659ae60fbe7e2`, tree
`0089a0aada59644cd5c495688b65fbcd0bb80544`, and dispatch `TASK-AR-655` next.
The planned order after its bounded repair remains `TASK-AR-657`, then the
release-candidate work in `TASK-AR-651`. This decision authorizes only a new
local task claim and RED-first implementation within registered scope. It does
not close TASK-AR-654 or authorize integration, CI dispatch, versioning,
packaging, publication, deployment, or release.

## Why T2 blocked

The task-claim dispatcher correctly refused AR-655 because the T0 assumption
snapshot still described the pre-repair AR-654 baseline. Its findings named
the AR-654 task/unit records, repeated-failure source/template code, claim
dispatcher, template contract, host lock, and regression files changed by the
subsequent accepted AR-654 repair chain. Using `--skip-plan-check` would erase
the distinction between reviewed drift and accidental drift, so it is not
used.

The current baseline is materially different but internally coherent:

- AR-654 implementation `94589d68` has a fresh five-command Verify and an
  append-only Compound that brings declared coverage to 41/41.
- Exact worker W4a, distinct independent W4b, and distinct skeptic evidence
  are committed through `957582da`; both independent reviews report no
  current-scope P0/P1/P2.
- At the exact reviewed candidate AR-654 remains `in_progress`, its unit
  remains `verification_status: failed`, and its claim is still `claimed`
  because native Windows, Scribe, and adjacent-task release blockers remain
  open. This revalidation transitions that claim to `blocked` after its W4
  chain, without adding release provenance, so its completed worker footprint
  cannot block the separately claimed repair that resolves an explicit
  dependency.
- The taskset purpose and Owner stop boundaries have not changed.

## AR-655 scope correction required after claim

The accepted AR-654 audit routed one previously unregistered P1 to the already
planned AR-655 task:

`defect:negative-lease-or-grace-kills-live-claim:315a2daf2bae5424`

The current AR-655 task/unit mention task-claim renewal, but their target list
does not yet include the reaper source/template and negative-grace regressions.
After claim creation, AR-655 must record a bounded T3 scope amendment before
editing those paths. It must perform exact Compound lookup, add the signature
to task/unit/claim parity, add RED tests for both negative create lease and
negative reaper grace, and only then implement fail-closed bounds. Zero-value
and positive boundary compatibility must be decided from actual existing
contracts rather than assumed.

## Re-anchored assumptions

The refreshed assumption set preserves the prior taskset design and pins:

- this revalidation record and the final AR-654 W4b/skeptic evidence;
- current AR-654 and AR-655 task/unit authority;
- repeated-failure, claim-store, dispatcher, lease/reaper, state-sync,
  worktree, UI, template, and host-lock implementation surfaces; and
- the relevant regression files used to challenge the next dispatch.

Future implementation changes are expected to drift these hashes. That drift
must again be reviewed and re-recorded before dispatching the next task; this
review is not a permanent bypass.

## Safety and release boundary

- Do not use negative or zero-duration metadata for the live AR-655 claim.
- Treat the AR-654 claim's `blocked` transition as a non-release handoff; do
  not add `released_at`, verifier approval, or any release claim.
- Preserve the tracked inner claim-store generation during linked-worktree
  activation; only the matching outer admin marker may be created.
- Do not mutate consumer repositories, STATUS/Scribe archives, credentials,
  providers, databases, notifications, or remote state.
- Do not claim native Windows evidence from POSIX execution.
- Keep AR-654, AR-655, AR-657, and AR-651 release blockers explicit until
  their own exact-candidate evidence chains are complete.

`release_authorized` remains false.
