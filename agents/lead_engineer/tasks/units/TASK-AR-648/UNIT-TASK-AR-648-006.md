---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-006
work_uid: 3a600790-841d-4fdf-9b25-5a61835a490a
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-006
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: blocked
verification_status: failed
owner: lead-engineer
created_at: 2026-07-29T23:02:11+09:00
updated_at: 2026-07-29T23:29:30+09:00
blocked_at: 2026-07-29T23:29:30+09:00
started_at: 2026-07-29T23:08:58+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-registration.md
created_by: codex-root-v080-planner
summary: Replay Bean Wiki adoption from the pinned original baseline and produce independently verified green evidence
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-230858-task-ar-648-648006.json
escalation_triggers:
  - data_integrity
  - repeated_failure
context: UNIT-005 closed the explicit claim publication defects at product SHA 6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39 with canonical W4a and independent W4b approval. The original red pilot and blocked green attempt 1 remain immutable. This unit creates a new Bean worktree from baseline 357eee4fd8c29c33a949adbe3a0ffa80c874bf42, replays the three bounded tasks, and promotes green evidence only if host, content, Git, routing, continuity, and external-effect boundaries all remain true.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080.md
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1.md
  - reviews/REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-003-r2.md
  - reviews/W4A-2026-07-29-unit-task-ar-648-005-r4.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-005-r4.md
  - agent-runtime@6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - new:tests/fixtures/pilots/bean-wiki/evidence-green.json
  - new:reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - new:reviews/W4A-2026-07-29-unit-task-ar-648-006.md
  - new:reviews/W4B-2026-07-29-unit-task-ar-648-006.md
  - new:reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md
  - new:reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-registration.md
  - new:reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-t3-replan.md
  - new:reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-006.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Create one clean linked Bean Wiki worktree and new branch from the exact original host baseline. Apply the exact Agent Runtime product template with core plus web-content, preserve all declared Bean editorial assets as host-owned, and run only three offline tasks: deterministic adoption verification at worker_low, one read-only specialist review at worker_standard, and deterministic restart plus Scribe verification at worker_low. Default claim persistence must leave Bean HEAD unchanged. No consumer commit, content edit, publish, deploy, push, credential read, or network delivery is allowed.
acceptance:
  - The new Bean worktree and branch start exactly at 357eee4fd8c29c33a949adbe3a0ffa80c874bf42; the dirty primary checkout and frozen attempt 1 remain byte-for-byte untouched.
  - The exact Runtime product template has no product-file delta from 6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39, and every reconcile command records the resolved template root, ref, tree, and digest.
  - The core plus web-content selection count, ownership counts, initial apply, immediate reconcile, lock check, doctor result, and post-registration reconcile are captured without unsupported fixed-count assumptions.
  - All 16 declared host assets, BACKLOG.md, and the complete src/content manifest have matching before and after SHA-256 digests with zero unexpected overwrite.
  - Default Bean claim creation records working_tree persistence and leaves Git HEAD at the original baseline; no explicit SCM opt-in is used.
  - Exactly three local task/unit/claim traces complete: worker_low adoption verification, worker_standard read-only coffee-flavor-wheel editorial review, and worker_low restart/Scribe verification.
  - The editorial task writes only a bounded review artifact and never changes coffee-flavor-wheel.html or any src/content file.
  - One intentional negative fixture creates a task-linked Compound record and a later matching lookup retrieves it.
  - Two distinct local processes resume the same restart task and claim; Scribe writes only the configured projection and never edits BACKLOG.md.
  - Requested, selected, resolved-provider, execution-surface, observed-model, provider-usage, and savings fields remain distinct; unobserved model, token, cost, and savings values remain unavailable.
  - Classifier output is regenerated only after the final serial task/claim projection, then classifier, state-sync, taskset, reconcile, host/content, and diff checks pass.
  - External-effect counters for publish, deploy, origin push, host commit, credential read, network delivery, and content mutation are all integer zero.
  - Sanitized green fixture validation, canonical W4a, and fresh independent W4b pass before TASK-AR-649 or release work starts.
verification:
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green.json --check
  - python -m pytest tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report exact Runtime and Bean baselines, worktree/branch identity, selected and ownership counts, every preserved digest, task/unit/claim and routing fields, Compound retrieval, restart process identities, Scribe projection, reconcile provenance, Git HEAD invariants, external-effect counters, sanitized fixture digest, W4a evidence, and independent W4b verdict.
stop_condition: Stop immediately on any P0 or P1, consumer commit, primary or frozen-worktree mutation, host/content overwrite, stale or ambiguous template provenance, unverified green claim, missing claim trace, unsupported model/cost claim, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-006 - Bean Wiki Green Replay Attempt 2

## Context

UNIT-005's exact Runtime product passed canonical W4a and independent W4b.
The original Bean red pilot and failed attempt 1 remain immutable, so this
unit is the first authorized fresh replay from the original Bean baseline.

## Inputs

- Runtime product `6ccfd9192185a87fa4ef0d4bd654fdba4dd84e39`
- Bean baseline `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Original red and blocked attempt-1 reports
- UNIT-003 and UNIT-005 independent approvals

## Target Files

- Green pilot report and sanitized fixture
- Green-fixture validator and regressions
- UNIT-006 W4a/W4b evidence
- Canonical task, claim, pointer, classifier, board, and evidence projections

## Scope

Create one fresh disposable Bean worktree, apply `core+web-content`, run three
offline traced tasks, and capture sanitized acceptance evidence. Consumer
product/content edits and every external effect are outside scope.

## Decision

This is a fresh consumer replay, not a continuation of attempt 1. The worktree
must begin at the original Bean baseline and use a new branch and path.

## Steps

1. Capture immutable Runtime, primary Bean, frozen attempt-1, and host/content
   baselines.
2. Create the new Bean worktree only after this unit is claimed.
3. Plan, reconcile, safe-apply, lock, and verify the `core+web-content`
   projection with exact template provenance.
4. Register and run the deterministic adoption task; prove default claim
   creation does not move Bean `HEAD`.
5. Run one selective editorial specialist as a read-only task.
6. Run restart and Scribe in distinct local processes.
7. Regenerate final projections, collect zero-effect evidence, and create the
   sanitized green fixture.
8. Complete Runtime W4a and an independent W4b before closing the unit.

## Acceptance Criteria

- Bean starts at the exact baseline and default claim creation does not move
  `HEAD`.
- Declared host assets, `BACKLOG.md`, and all `src/content/**` bytes remain
  unchanged.
- Adoption, editorial review, and restart/Scribe tasks each have a complete
  task/unit/claim trace and truthful routing fields.
- Compound retrieval, process restart, projection freshness, reconcile
  stability, and integer-zero external-effect counters are observed.
- Sanitized green evidence, W4a, and independent W4b all pass.

## Verification

- `python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green.json --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`
- Registered adoption, claim, classifier, state-sync, governance, sanitizer,
  and full-suite commands in frontmatter

## Handoff

Report exact baselines and template provenance, selection and ownership
counts, preserved digests, all task/claim/routing records, Compound and
restart evidence, Scribe state, Git invariants, external-effect counters,
fixture digest, W4a, and independent W4b.

## Deliberate Exclusions

- The pilot does not edit or improve the reviewed article.
- It does not claim provider token or cost savings without provider evidence.
- It does not reuse, reset, clean, amend, or repair the frozen first attempt.
- It does not start Allimbot or any release action.

## Stop Boundary

Any P0/P1 or mismatch in Git, content, ownership, task trace, continuity,
evidence truth, or external-effect counters stops the replay and preserves the
worktree as failure evidence.

## Outcome

Blocked at step 4. The valid default claim left Bean `HEAD` unchanged, but the
installed parallel-worktree gate required `STATUS.md` or
`agents/lead_engineer/STATUS.md`; neither the selected template, adopt plan,
lock, nor doctor provided or diagnosed either candidate. Independent W4b
confirmed P0 and `REQUEST_CHANGES` at 45/100.

Attempt 2 is frozen at
`/home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-2`.
The editorial and restart/Scribe tasks did not start. All host/content digests
match their baselines and every external-effect counter is zero. See
`reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md` and
`reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md`.
