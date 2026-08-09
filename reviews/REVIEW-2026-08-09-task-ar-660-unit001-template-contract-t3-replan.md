---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-template-contract-t3-replan
title: TASK-AR-660 Unit 001 Template Contract Footprint T3 Replan
date: 2026-08-09
created_at: 2026-08-09T15:07:05+09:00
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
verdict: AMEND_UNIT001_TEMPLATE_CONTRACT_FOOTPRINT
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, template-mirror, footprint]
---

# TASK-AR-660 Unit 001 template contract footprint T3 replan

## Bottom line

Add `agents/project/TEMPLATE-MIRROR-CONTRACT.json` to Unit 001 and the active
claim footprint, re-record the taskset assumptions against this review, and
rebind the claim through the owner-bound adoption transaction before W4a.

## Why the original footprint was incomplete

Unit 001 introduces `scripts/recovery_receipt.py` and its installed-project
mirror. The mirror gate uses `agents/project/TEMPLATE-MIRROR-CONTRACT.json` as
the explicit expected-common inventory, so the new governed pair is invisible
unless that contract adds `recovery_receipt.py`. The implementation commit
correctly added the entry, but planning omitted the contract from `target_files`.
Reverting the contract would weaken the acceptance proof; silently retaining an
undeclared edit would violate claim scope authority.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| Product need | pass | `recovery_receipt.py` has an exact installed-project mirror |
| Declared footprint | block before amendment | mirror contract was absent from Unit 001 and claim `target_files` |
| Scope choice | pass | add one contract path; do not revert governed inventory |
| Release authority | closed | `release_authorized: false` |

## Action

Add exactly one product path to the Unit 001 footprint:

- `agents/project/TEMPLATE-MIRROR-CONTRACT.json`

No claim status, lease, task/unit identity, branch authority, release authority,
or external system is changed by this amendment. The existing owner-bound
`adopt` operation will record the exact old and new scope digests together with
the canonical work-identity binding in its immutable recovery receipt.

## Risks / Blockers

Until the T3 registry and owner-bound adoption both succeed, the current claim
scope digest does not authorize the contract edit and W4a is blocked. Reverting
the contract would instead create a blind spot in the template mirror gate.

## Assumptions and verification

The correction remains local-filesystem-only. Receipt-first publication,
strict durability truth, canonical task/unit UUID authority, root/template
parity, and independent W4b remain mandatory. The taskset plan assumptions are
re-recorded only after the final Unit 001 product bytes are fixed, so subsequent
drift fails closed.

## Decision

`ACCEPT` this bounded footprint amendment and T3 re-anchor. It grants no
rotation, release, acceptance, completion, push, tag, publish, or deploy
authority.

## Next Steps

Re-record the taskset assumptions against this review, commit the exact Unit
001 product, then run owner-bound `adopt` with this review as `replan_ref`.
Confirm its before/after scope and work-identity digests and immutable receipt
before W4a and independent W4b.
