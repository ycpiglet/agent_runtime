---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-actor-toctou-t3-replan
title: TASK-AR-660 Unit 001 Recovery Actor TOCTOU T3 Replan
date: 2026-08-09
created_at: 2026-08-09T16:14:07+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
tier: T3
reviewer: le-20260809-130000-kst-ar660001
reviewer_role: orchestrator
status: accepted
signal: pass
score: 100
verdict: AMEND_RECOVERY_ACTOR_TRANSACTION_AND_ATTRIBUTION_GATE
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, attribution, recovery-actor, toctou]
---

# TASK-AR-660 Unit 001 recovery actor TOCTOU T3 replan

## Bottom Line

Reopen Unit 001 after the preliminary independent audit. Re-prove the exact
registered recovery actor inside the claim-store commit transaction and make
the attribution gate independently reject post-cutoff pane events whose
claimed instance is absent or whose canonical attribution fields do not match
the registry.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| Preliminary audit | block | `reviews/ROLE-REVIEW-2026-08-09-TASK-AR-660-INDEPENDENT-AUDITOR-PREFLIGHT.md` reports P1 actor-registry TOCTOU |
| Dispatcher RED | pass | nine adopt/terminalize/activate-store unlink, atomic-replace, and field-change races fail before repair |
| Dispatcher repair | pass | exact registry bytes are revalidated under the cooperative claim-store lock immediately before receipt precommit |
| Attribution gate | incomplete | a nonempty `agent_instance_id` currently bypasses registration and canonical-field checks |
| Prior W4a | superseded | `reviews/VERIFY-2026-08-09-unit-task-ar-660-001-20260809155259.json` predates the P1 finding |

## Action

Keep the already declared dispatcher and dispatcher-test footprint. Add
exactly these three paths to Unit 001 and the active claim scope:

- `scripts/attribution_gate.py`
- `src/agent_runtime/templates/project/scripts/attribution_gate.py`
- `tests/test_attribution_gate.py`

For all three owner-bound recovery mutations, resolve the actor only while the
claim-store lock is held and compare the exact registry-record digest again at
the receipt precommit boundary. Registry disappearance, replacement, field
change, duplicate canonical members, or identity mismatch must leave the
subject, receipt store, and derived events unchanged.

For post-cutoff pane events, the attribution gate must require the named
instance to resolve to one direct regular registry record and require the
event's actor, role, display name, and callsite to equal canonical registry
values. Legacy pre-cutoff findings remain watch-only according to the existing
cutoff policy.

## Risks / Blockers

Revalidation outside the cooperative lock merely narrows the race and is not
authority. Conversely, dispatcher-only enforcement leaves imported, hand-
edited, or future-writer events able to launder an arbitrary nonempty instance
ID through the global attribution gate. Both enforcement points and their
template mirrors are required before a fresh W4a/W4b.

## Decision

`ACCEPT` the bounded transaction and attribution-gate amendment. Reset Unit
001 verification to pending, re-record taskset assumptions, renew the main
claim from its exact revision and scope digest, regenerate the managed host
lock, and repeat W4a plus a fresh context-isolated W4b. This grants no rotation,
claim release before W4b acceptance, task completion, external CI, push, tag,
publish, or deploy authority.

## Next Steps

Finish RED/GREEN tests and exact root/template parity, persist the scope renewal
through the claim-only crash-safety transaction, then run the complete Unit 001
verification and security gates. Only a new W4b with P0/P1 zero may authorize
release of the main Unit 001 claim.
