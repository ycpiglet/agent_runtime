---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-011
work_uid: ca4ef293-6095-4182-acd3-0624c5f79a16
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-011
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T02:42:34+09:00
updated_at: 2026-07-30T02:46:30+09:00
started_at: 2026-07-30T02:46:30+09:00
origin_type: pilot_replay
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-010.md
created_by: codex-root-v080-planner
summary: Replay Bean Wiki from a fourth fresh baseline after the independently approved consumer-continuity ownership repair
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-024630-task-ar-648-648011.json
escalation_triggers:
  - data_integrity
  - repeated_failure
context: Bean attempt 3 passed adoption, lock, doctor, portable pointer continuity, state sync, Scribe, RBAC, and preservation, then stopped on an ownership-insensitive documentation gate. UNIT-010 repaired only that boundary at exact product dd279cd5613578c87ed6c4c24b37325084449d82 and independently passed W4b at 99/100 with no P0/P1. This unit must prove the complete three-task Bean journey from a new worktree without changing any prior failure evidence or host-owned editorial/content surface.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-010.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-010.md
  - reviews/VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400.json
  - agent-runtime-product@dd279cd5613578c87ed6c4c24b37325084449d82
  - agent-runtime-lifecycle@5e44d7f6764865c87c818260e2b841e74c7b3d29
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - new:tests/fixtures/pilots/bean-wiki/evidence-green-attempt-4.json
  - new:reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-4.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-011.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-011.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-4-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-4-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-011.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: After Runtime registration, T3 re-anchoring, readiness, canonical plan selection, and a default working-tree Runtime claim, create a detached product worktree pinned to dd279cd5613578c87ed6c4c24b37325084449d82 and only /home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-4 on branch codex/task-ar-648-agent-runtime-green-pilot-4 from Bean baseline 357eee4fd8c29c33a949adbe3a0ffa80c874bf42. Apply exact core plus web-content templates, preserve Bean editorial assets as host-owned, and run exactly three offline traces: deterministic adoption verification at worker_low, one selectively invoked read-only coffee-flavor-wheel editorial review at worker_standard under bean-wiki-editorial-ops, and deterministic restart plus Scribe verification at worker_low. No consumer commit, content edit, dependency installation, provider-live call, publish, deploy, push, credential read, or network delivery is allowed.
acceptance:
  - Attempt 4 starts exactly at Bean 357eee4fd8c29c33a949adbe3a0ffa80c874bf42; Bean primary plus original red and green attempts 1-3 remain byte- and Git-state identical to their pre-run snapshots.
  - The installed template is byte-identical to Runtime product dd279cd5613578c87ed6c4c24b37325084449d82 at template tree fb7a9ad3dca93b9734467e2e9b5201ba2c1527a9; every adoption stage records template root, upstream ref, tree, and semantic digest.
  - Core plus web-content selection, v2 ownership, initial apply, immediate reconcile, lock check, doctor, and post-registration reconcile are observed with zero conflicts.
  - A no-STATUS host passes standby pointer continuity; a default claim leaves Bean HEAD unchanged and, after deterministic projection, pointer, claim, handoff, log, state-sync, RBAC, parallel, continuity, and complete Owner governance all pass.
  - Runtime wording is validated from digest-matched managed AGENT_RUNTIME.md; Bean README.md, AGENTS.md, and CLAUDE.md remain byte-identical and no host-owned document workaround occurs.
  - All declared host assets, BACKLOG.md, coffee-flavor-wheel.html, and the complete src/content manifest have matching before/after SHA-256 values with zero unexpected overwrite.
  - Exactly three local task, unit, and claim traces complete: worker_low adoption, worker_standard read-only editorial review, and worker_low restart/Scribe.
  - The editorial specialist reads AGENTS.md, docs/EDITORIAL.md, docs/AGENT-EDITORIAL-OPS.md, the configured review skill, personas, topic plan, and article; it writes only a bounded review artifact and never changes src/content or a generated index.
  - One intentional negative fixture creates a task-linked Compound record and a later semantic lookup retrieves that exact record rather than merely same-task unrelated records.
  - Two distinct local processes resume the restart claim; Scribe writes only its configured generated projection and never edits BACKLOG.md.
  - Requested tier, selected tier, resolved provider tier, execution surface, actual model observation, usage, tokens, cost, and savings remain distinct; unavailable provider observations remain null or unavailable.
  - Classifier output is regenerated after the final serial lifecycle write; classifier, state-sync, taskset, reconcile, host/content, diff, and local editorial checks pass.
  - Publish, deploy, origin push, host commit, credential read, network delivery, dependency installation, and content mutation counters are all integer zero.
  - The sanitized attempt-4 fixture, canonical W4a, and fresh independent W4b pass with no P0/P1 before Allimbot or release work starts.
verification:
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-4.json --check
  - python -m pytest tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report exact Runtime product/lifecycle and Bean baselines, product/template trees, worktree/branch identities, immutable snapshots of primary and attempts 1-3, selection and ownership counts, every preserved digest, continuity mode, managed-contract hashes, pointer/claim/sidecar agreement, three task/unit/claim traces and routing fields, Compound retrieval precision, restart process identities, Scribe projection, Bean validation results, reconcile provenance, Git HEAD invariants, integer-zero external effects, sanitized fixture digest, W4a evidence, and independent W4b verdict.
stop_condition: Stop immediately on any P0 or P1, consumer commit, primary or attempts 1-3 mutation, host/content overwrite, missing or ambiguous Runtime/template provenance, continuity fail-open, host-document workaround, unverified claim, missing task trace, unrelated Compound retrieval, unsupported model/cost claim, dependency installation, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-011 - Bean Wiki Green Replay Attempt 4

## Context

Attempt 3 proved the portable pointer path and exposed the next ownership
boundary. UNIT-010 repaired that boundary without changing Bean and passed
canonical plus independent verification on one exact Runtime product. Attempt
4 is therefore a fresh consumer proof, not a repair of the frozen checkout.

## Inputs

- Runtime product: `dd279cd5613578c87ed6c4c24b37325084449d82`
- Runtime product tree: `ea843b6ca5661f04179376df92a11f4416217ab1`
- Runtime template tree: `fb7a9ad3dca93b9734467e2e9b5201ba2c1527a9`
- Runtime lifecycle close: `5e44d7f6764865c87c818260e2b841e74c7b3d29`
- Bean baseline: `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Attempt-4 path: `.pilot-worktrees/bean-wiki-task-ar-648-green-4`
- Attempt-4 branch: `codex/task-ar-648-agent-runtime-green-pilot-4`
- UNIT-010 W4a, independent W4b, and canonical verification
- Attempt-3 immutable failure report and Bean's editorial operations contract

## Target Files

- Sanitized attempt-4 fixture and a distinct attempt-4 pilot report
- UNIT-011 W4a and independent W4b
- Runtime pilot validator/tests only if observed evidence requires a bounded
  correction
- Task, unit, claim, pointer, assumption, classifier, board, and evidence-index
  lifecycle projections
- Disposable Bean host evidence and one read-only editorial review artifact

## Scope

Install exact `core+web-content` into one fresh Bean worktree, run exactly
three bounded offline traces, and promote green evidence only if ownership,
continuity, Git, editorial/content, routing, Scribe, Compound, and
zero-external-effect assertions all pass. The Bean editorial SSOT remains
host-owned.

## Steps

1. Register, T3-anchor, verify readiness and canonical selection, then create a
   default working-tree Runtime claim without moving Runtime HEAD.
2. Snapshot Runtime product provenance and every Bean primary/frozen checkout
   before creating attempt 4.
3. Create fresh detached Runtime product and Bean attempt-4 worktrees at the
   exact fixed commits; capture host, backlog, article, and content digests.
4. Plan, safe-apply, lock, doctor, and reconcile `core+web-content`.
5. Register three local Bean traces and prove standby/active continuity plus
   full installed governance without a consumer commit.
6. Selectively invoke one read-only editorial specialist under Bean's
   editorial SSOT; write only its review artifact.
7. Record/retrieve one Compound, resume a restart claim from distinct local
   processes, and prove fresh Scribe state without editing its source.
8. Regenerate final projections, validate Bean and Runtime evidence, complete
   W4a, and obtain independent W4b.

## Acceptance Criteria

- Exact Runtime and Bean provenance is recorded and every existing Bean
  checkout remains unchanged.
- Adoption/reconcile has zero conflict; the standby and active pointer journey
  plus complete installed Owner governance pass without editing host docs.
- All host, backlog, article, and content digests match before and after.
- Three local traces complete with truthful routing/provider-observation
  fields; the editorial review is the only specialist-written artifact.
- Exact Compound retrieval, cross-process restart, fresh Scribe projection,
  local validation, and integer-zero external effects are observed.
- The sanitized fixture, W4a, and fresh independent W4b pass with no P0/P1.

## Verification

- `python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-4.json --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`
- The focused routing, claim, continuity, ownership, adoption, and sanitizer
  commands declared in frontmatter
- `python scripts/owner_governance_gate.py`
- `python -m pytest -q`

## Handoff

Report exact provenance and worktree identities, immutable before/after
snapshots, selection/ownership counts, every preserved digest, continuity and
managed-contract proof, three trace/routing records, Compound retrieval,
restart/Scribe evidence, Git invariants, zero-effect counters, fixture digest,
W4a, and independent W4b.

## Deliberate Exclusions

- No Bean content, generated content index, host editorial file, or earlier
  pilot edit.
- No dependency installation, provider-live execution, consumer commit, or
  external delivery.
- No Allimbot action before attempt-4 independent approval.
- No version, tag, package, release, push, publish, or deployment action.

## Stop Boundary

Any P0/P1 or mismatch in provenance, ownership, continuity, Git state,
editorial/content bytes, task trace, routing truth, Scribe output, Compound
retrieval, or zero-effect counters freezes attempt 4 and keeps Allimbot
blocked.
