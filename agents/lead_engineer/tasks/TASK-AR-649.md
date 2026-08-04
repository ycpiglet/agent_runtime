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
updated_at: 2026-07-30T08:35:05+09:00
started_at: 2026-07-30T07:44:00+09:00
title: Run the Allimbot security-service pilot
status: completed
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
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-649-independent-auditor-closeout.json
  - agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-649-skeptic-closeout.json
verification:
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/allimbot/isolation-green-attempt-1.json --check --json
  - python scripts/pilot_acceptance.py --host allimbot --fixture tests/fixtures/pilots/allimbot/evidence-green-attempt-1.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-6.json --check --json
  - python -m pytest tests/test_pilot_isolation_gate.py tests/test_pilot_acceptance.py tests/test_allimbot.py tests/test_security_service.py -q
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
verification_status: passed
verified_at: 2026-07-30T08:31:00+09:00
verified_by: codex-root-task-ar-649
evidence_refs:
  - reviews/VERIFY-2026-07-30-task-ar-649-20260730083100.json
review_refs:
  - reviews/W4A-2026-07-30-unit-task-ar-649-001.md
  - reviews/W4B-2026-07-30-unit-task-ar-649-001.md
  - reviews/SKEPTIC-2026-07-30-task-ar-649-closeout.md
resolution: done
completed_at: 2026-07-30T08:35:05+09:00
closed_by: codex-root-task-ar-649
measurement_unavailable_reason: Offline pilot did not expose trustworthy task-hour, provider-token, or cost telemetry.
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

- `python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/allimbot/isolation-green-attempt-1.json --check --json`
- `python scripts/pilot_acceptance.py --host allimbot --fixture tests/fixtures/pilots/allimbot/evidence-green-attempt-1.json --check --json`
- `python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-6.json --check --json`
- Focused Runtime pilot, claim, state, continuity, Owner, adoption, and config
  regression commands are pinned in frontmatter.
- Clean-target Allimbot Python tests use existing local dependencies only;
  unavailable web suites are reported rather than installed.
- W4a plus fresh independent W4b must have no Runtime P0/P1.

## Superseded Verification Attempts

- `reviews/VERIFY-2026-07-30-task-ar-649-20260730083005.json` preserves the
  failure-first evidence where descriptive verification prose was consumed as
  shell commands. It was replaced by the explicit eight-command frontmatter
  set and is historical, not active closeout evidence.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-30T08:35:05+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Offline pilot did not expose trustworthy task-hour, provider-token, or cost telemetry.
- Closed by: `codex-root-task-ar-649`
- Verification evidence:
  - `reviews/VERIFY-2026-07-30-task-ar-649-20260730083100.json`
- Reviews:
  - `reviews/W4A-2026-07-30-unit-task-ar-649-001.md`
  - `reviews/W4B-2026-07-30-unit-task-ar-649-001.md`
  - `reviews/SKEPTIC-2026-07-30-task-ar-649-closeout.md`
<!-- work-close:end -->
