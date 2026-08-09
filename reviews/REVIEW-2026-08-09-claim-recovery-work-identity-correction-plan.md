---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan
title: Claim Recovery and Work Identity Correction Plan
date: 2026-08-09
created_at: 2026-08-09T12:00:00+09:00
review_kind: recovery-plan
reviewer: codex-root-owner-approved-correction
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: PROCEED_REGISTER_CLAIM_FIRST
priority: P1
tags: [claim-recovery, work-identity, ledger-recovery, taskset-recovery, scribe, compound]
---

# Claim Recovery and Work Identity Correction Plan

## Decision

Register four new, collision-free tasks and execute them through W0-W6. Do not
rewrite or reuse the two older canonical task identities that currently own
`TASK-AR-653` and `TASK-AR-654`. Do not delete, complete, release, or otherwise
rewrite any historical terminal claim to make the collision disappear.

External version changes, tags, pushes, package publication, deployment, and
consumer rollout remain a separate Owner authorization boundary after local
release preflight.

## Fixed Historical Authority

| Display ID | Canonical first registration retained | Colliding V080 identity | Recovery disposition |
| --- | --- | --- | --- |
| `TASK-AR-653` | Merge Queue Safety, `f7ef3b94-9c25-4e2c-b0a0-da98e1d67a6b` | Scribe source-debt, `d7d6d63a-5059-4a2f-8399-d7ca683ba6ef` | re-key as `TASK-AR-662`; preserve four terminal claim triplets and implementation history |
| `TASK-AR-654` | Host Required Merge Gates, `6472cbce-31a6-46a9-aad7-f374b7ddf1f3` | repeated-failure Compound, `ef3cb8e5-d5b9-443e-ad93-5948ade62659` | re-key as `TASK-AR-663`; preserve two worker claims, review overlays, Compound records, and blocked evidence |

The Scribe implementation and final approval are ancestors of `main` through
commit `0002ff91`. The Compound implementation/evidence chain is retained at
commit `905480ce` and is also an ancestor of `main`. Their task/unit records
were lost when merge `2db74f8f` accepted the first-parent work-item files and
reservation ledger wholesale. This plan restores authority by re-keying; it
does not pretend the colliding reservation rows can be unioned as canonical.

## Exact Ledger Repair Rule

Restore only the six non-conflicting fulfilled reservations whose canonical
task files still cite them: `TASK-AR-652`, `TASK-AR-655`, `TASK-AR-656`,
`TASK-AR-657`, `TASK-AR-658`, and `TASK-AR-659`. The colliding V080 reservation
rows for old 653/654 are recovery evidence, never canonical fulfilled rows.

Add a bidirectional gate so every canonical task's `reservation_id` resolves
to one fulfilled row with exact display ID, task path, and `task_uid`, and so
explicit taskset membership is exact in both directions. Bind every new claim
to the canonical task `task_uid` and unit `work_uid`; display IDs alone are no
longer sufficient authority.

The V080 registry membership will be corrected to the canonical V080 tasks
`652, 655, 656, 657, 658, 659`. The Scribe and Compound intents continue as
successor recovery tasks 662/663 in this correction taskset, with an immutable
collision map tying their old UUIDs, claims, commits, and evidence to the new
identities. The historical 2026-07-30 registration input remains unchanged.

## Claim Recovery Transaction Contract

Recovery mutations use an immutable receipt-first WAL under
`agents/runtime/recovery_receipts/`. A receipt carries explicit Owner
attribution, reason, semantic and raw before/after digests, exact transition,
commit witness, and self digest. Pane events are derived notifications, not the
sole audit authority. Receipt publication failure leaves the subject
byte-identical; an uncertain post-commit read reports an indeterminate,
non-retry-safe outcome.

`rotate` performs an in-place cutover of one provably expired active claim. It
requires adoption first for legacy claims, preserves task/unit/scope/branch
authority, advances one mutation revision, records bounded worker lineage,
terminates the old instance, spawns the new instance, and prevents every prior
worker from acting as the independent release verifier. `owner-id` is durable
local attribution under this repository's filesystem threat model; it is not
claimed as cryptographic authentication.

## RED-first Sequence

1. Register `TASK-AR-660` through `TASK-AR-663` and their unit specs; record T0.
2. Claim `UNIT-TASK-AR-660-001` before creating its worktree.
3. RED and implement work-identity binding plus durable recovery receipts.
4. Claim and implement `UNIT-TASK-AR-660-002` owner-bound rotation.
5. Independently verify and integrate Task 660 before Task 661 starts.
6. RED and implement inverse reservation, strict taskset membership, immutable
   collision mapping, exact six-row ledger restoration, and stale Host Gates
   metadata reconciliation under Task 661.
7. Claim Tasks 662 and 663 normally. Re-run the complete Scribe and Compound
   acceptance surfaces against current `main`, create fresh evidence and
   independent reviews under their new identities, and preserve old artifacts.
8. Refresh pointers, plan anchors, generated views, Compound and Scribe state,
   run W4a/W4b, W5 integration, W6 cleanup, and local release preflight.

## Stop Boundaries

- Never mutate `CLAIM-20260803-002651-task-ar-655-5f27` again; its exact
  terminal state is `expired` with recorded before/after digest and Owner
  recovery evidence.
- Never use JSON union to repair the reservation ledger.
- Never make old 653/654 claim files resolve through the current colliding
  unit specs without the immutable collision map.
- Never infer Windows-native evidence from POSIX simulations.
- Stop before push, tag, publish, deployment, external CI dispatch, consumer
  mutation, or external release without the next explicit Owner authorization.

## Release Preconditions

- Recovery receipt, rotation, work-identity, taskset membership, template
  parity, RBAC, Scribe, Compound, and owner-governance gates pass.
- No P0/P1 independent finding remains in the corrected local candidate.
- Any native-Windows or other unavailable external evidence is listed as an
  explicit release blocker rather than converted to a pass.
- Bean Wiki and Allimbot pilot application occurs only after the Runtime
  correction version is locally releasable and separately authorized.
