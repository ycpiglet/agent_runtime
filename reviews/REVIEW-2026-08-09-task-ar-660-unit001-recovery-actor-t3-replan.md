---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-09-task-ar-660-unit001-recovery-actor-t3-replan
title: TASK-AR-660 Unit 001 Recovery Actor Attribution T3 Replan
date: 2026-08-09
created_at: 2026-08-09T15:41:40+09:00
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
verdict: AMEND_RECOVERY_ACTOR_AND_CONSUMER_WIRING
priority: P1
owner_approval_ref: owner instruction to proceed with all approved recovery work, 2026-08-09
release_authorized: false
tags: [task-ar-660, unit-001, t3-replan, attribution, recovery-actor, consumer-wiring]
---

# TASK-AR-660 Unit 001 recovery actor attribution T3 replan

## Bottom Line

Separate the human Owner who authorizes recovery from the registered agent
instance that executes it. Add the two terminalize-instruction consumers and
their exact template mirrors, plus their focused test, to the Unit 001
footprint before W4a.

## Signal

| Surface | State | Evidence |
| --- | --- | --- |
| Recovery receipts | pass | immutable receipts retain the exact Owner Git identity |
| Claim provenance | pass | recovered_by remains the Owner Git identity |
| Derived pane events | block before repair | new events 668 and 669 used the Owner identity as runtime actor |
| Attribution gate | block before repair | both events were post-cutoff and lacked a registered agent_instance_id |
| Consumer instructions | incomplete before repair | reaper and SessionStart hook omitted the newly required actor argument |

## Action

Require --actor-instance-id on adopt, terminalize, and activate-store.
Resolve its exact direct registry record before receipt publication or subject
mutation; derive role, display name, and callsite only from that record. Emit
the registered instance as actor while preserving the separate owner_id.

Add exactly these five paths to the declared footprint:

- scripts/claim_reaper.py
- src/agent_runtime/templates/project/scripts/claim_reaper.py
- scripts/claim_reaper_hook.py
- src/agent_runtime/templates/project/scripts/claim_reaper_hook.py
- tests/test_claim_reaper.py

The dispatcher, pane event writer, their template mirrors, and dispatcher tests
were already declared Unit 001 paths.

## Risks / Blockers

Accepting an arbitrary actor string would merely move the laundering seam from
owner_id to a caller-controlled agent_instance_id. Missing, unknown, aliased,
unstable, oversized, duplicate-member, schema-mismatched, or filename/payload-
mismatched instance records must refuse before any receipt or subject mutation.
Omitting consumer wiring would leave Owner-facing recovery instructions unrunnable.

## Decision

ACCEPT the bounded actor-attribution repair and five-path consumer amendment.
It grants no rotation, claim release, acceptance, completion, external CI,
push, tag, publish, or deploy authority.

## Next Steps

Finish RED/GREEN verification, re-record the taskset assumptions against this
review, and renew the active claim from its exact revision and scope digest.
Persist the claim through the claim-only crash-safety transaction, then commit
the product repair and corrected derived events before W4a.
