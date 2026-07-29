---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-649
display_id: TASK-AR-649
task_uid: 57d95039-80bf-4e22-b7f8-b8356dccf637
work_id: TASK-AR-649
work_uid: 57d95039-80bf-4e22-b7f8-b8356dccf637
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-30T07:44:00+09:00
started_at: 2026-07-30T07:44:00+09:00
title: Run the Allimbot security-service pilot
status: in_progress
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: risk-and-safety
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-649/UNIT-TASK-AR-649-001.md
reservation_id: RES-20260728-163601-b8c2a87a-11
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Prove runtime adoption works in a mixed Python/Next/Supabase security-sensitive service and uses native Allimbot events.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-074400-task-ar-649-ar649001.json
---

# TASK-AR-649 - Run the Allimbot security-service pilot

## Current Phase

- Bean Wiki attempt 6 passed exact acceptance, canonical verification, W4a,
  and fresh independent W4b. `TASK-AR-648` is complete.
- This task is re-anchored to exact Runtime product
  `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` and clean Allimbot commit
  `5cc15ff3f153339865ffb09b1f4c3b9124b1c4fd`.
- The live Allimbot primary has pre-existing uncommitted changes in
  `console/app/console/page.js` and `console/auth.js`. It is an observation
  surface only. A new same-commit target and frozen control are mandatory.
- No Allimbot consumer checkout has been created or written by this pilot yet.

## Goal

- Prove runtime adoption works in a mixed Python/Next/Supabase security-sensitive service and uses native Allimbot events.

## Scope

- Use one new disposable Allimbot worktree plus a same-commit frozen control.
  Apply exact `core+security-service`, complete ordinary, Critical-review, and
  offline event-recovery traces, and keep every production effect blocked.
- Preserve the live primary, host security/release policies, complete tracked
  product tree, credentials, dependencies, historical Bean evidence, and exact
  Runtime product.

## Acceptance Criteria

- Existing product security and release policies remain host-owned.
- Selection, ownership, safe apply, lock, doctor, reconcile, continuity, and
  frozen-control checks pass without a conflict.
- An ordinary task and a Critical read-only auth review complete with correct
  routing; the Critical task receives a distinct independent security review.
- Offline native events enter only a disposable local SQLite spool, survive a
  new reader process, contain only allowlisted data, and never flush.
- Compound, two-process restart, and Scribe projection complete without
  mutating host state.
- Raw physical isolation and its digest-bound path-free projection pass, and a
  strict Allimbot pilot contract accepts the exact evidence.
- No production deployment, migration, credential access/change, dependency
  installation, network delivery, consumer commit, or release action occurs.

## Verification

- Exact-product pilot isolation and Allimbot acceptance checks
- Runtime acceptance, native-event, security-service, adoption, and continuity
  focused tests
- Clean-target Allimbot Python and web/security tests using existing local
  dependencies only; unavailable suites are reported rather than installed
- W4a plus fresh independent W4b with no Runtime P0/P1
