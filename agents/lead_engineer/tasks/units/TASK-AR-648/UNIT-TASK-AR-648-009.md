---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-009
work_uid: c1b02a36-6fc9-466e-bcec-d4e104bb9652
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-009
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: blocked
verification_status: failed
owner: lead-engineer
created_at: 2026-07-30T01:28:00+09:00
updated_at: 2026-07-30T01:54:54+09:00
blocked_at: 2026-07-30T01:54:54+09:00
started_at: 2026-07-30T01:33:40+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-3-registration.md
created_by: codex-root-v080-planner
summary: Replay Bean Wiki adoption from a fresh pinned worktree after the independently approved portable-continuity repair
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-013340-task-ar-648-648009.json
escalation_triggers:
  - data_integrity
  - repeated_failure
context: UNIT-008 closed the portable-continuity P0 at exact product b82042eba58f1e06e1e73130a189cb72245462a0. Canonical W4a, independent W4b at 99/100, and six-command verification passed with no P0/P1. Bean primary and the two failed green attempts remain immutable evidence. This unit creates attempt 3 only from Bean baseline 357eee4fd8c29c33a949adbe3a0ffa80c874bf42 and proves the complete offline adoption, selective editorial review, Compound, restart, Scribe, routing, and continuity journey.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080.md
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-008.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-008.md
  - reviews/VERIFY-2026-07-30-unit-task-ar-648-008-20260730011630.json
  - agent-runtime-product@b82042eba58f1e06e1e73130a189cb72245462a0
  - agent-runtime-lifecycle@da15ddf6c9e06c89368b3ccc53c4fca603165b1b
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - new:tests/fixtures/pilots/bean-wiki/evidence-green.json
  - new:reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-009.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-009.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-3-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-3-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-009.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: After Runtime registration, T3 re-anchoring, plan selection, and claim creation, create only /home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-3 on branch codex/task-ar-648-agent-runtime-green-pilot-3 from the exact Bean baseline. Apply the exact b82042eb core plus web-content template, preserve all Bean editorial assets as host-owned, and run only three offline tasks: deterministic adoption verification at worker_low, one read-only coffee-flavor-wheel specialist review at worker_standard under the Bean Wiki editorial operations contract, and deterministic restart plus Scribe verification at worker_low. Default claim persistence must leave Bean HEAD unchanged. No consumer commit, content edit, package install, publish, deploy, push, credential read, or network delivery is allowed.
acceptance:
  - Attempt 3 starts exactly at 357eee4fd8c29c33a949adbe3a0ffa80c874bf42; Bean primary and all three earlier pilot worktrees remain unmodified.
  - The projected template is byte-identical to product b82042eba58f1e06e1e73130a189cb72245462a0 at template tree d61713bc4066d4ea549efcc7826da10929e64e94, and every reconcile records template root, upstream ref, tree, and semantic digest.
  - Core plus web-content selection, ownership, initial apply, immediate reconcile, lock check, doctor, and post-registration reconcile are recorded from observed output with zero conflicts.
  - A no-STATUS clean host begins with a valid standby pointer; after a default claim and deterministic projection, pointer, claim, handoff, and log sidecars pass the installed parallel, state-sync, RBAC, and owner-governance gates.
  - All 16 declared host assets, BACKLOG.md, coffee-flavor-wheel.html, and the complete src/content manifest have matching before and after SHA-256 digests with zero unexpected overwrite.
  - Default Bean claim creation records working_tree persistence and leaves Git HEAD at the original baseline; no explicit SCM opt-in is used.
  - Exactly three local task, unit, and claim traces complete: worker_low adoption verification, worker_standard read-only editorial review, and worker_low restart/Scribe verification.
  - The editorial specialist reads AGENTS.md, docs/EDITORIAL.md, docs/AGENT-EDITORIAL-OPS.md, the configured review skill and personas, and the article; it writes only a bounded review artifact and never changes src/content.
  - Read-only Bean content and editorial checks pass without dependency installation or network access; no generated content index is edited by hand.
  - One intentional negative fixture creates a task-linked Compound record and a later matching lookup retrieves the exact record.
  - Two distinct local processes resume the same restart task and claim; Scribe writes only the configured projection and never edits BACKLOG.md.
  - Requested, selected, resolved-provider, execution-surface, observed-model, provider-usage, token, cost, and savings fields remain distinct; unavailable observations remain null or unavailable.
  - Classifier output is regenerated only after the final serial lifecycle write, then classifier, state-sync, taskset, reconcile, host/content, and diff checks pass.
  - External-effect counters for publish, deploy, origin push, host commit, credential read, network delivery, package install, and content mutation are all integer zero.
  - Sanitized green fixture validation, canonical W4a, and fresh independent W4b pass before Allimbot or release work starts.
verification:
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green.json --check
  - python -m pytest tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report exact Runtime product/lifecycle and Bean baselines, worktree and branch identity, selected and ownership counts, every preserved digest, continuity mode, pointer/claim/sidecar agreement, task/unit/claim and routing fields, Compound retrieval, restart process identities, Scribe projection, Bean validation results, reconcile provenance, Git HEAD invariants, external-effect counters, sanitized fixture digest, W4a evidence, and independent W4b verdict.
stop_condition: Stop immediately on any P0 or P1, consumer commit, primary or frozen-worktree mutation, host/content overwrite, missing or ambiguous template provenance, continuity fail-open, unverified green claim, missing task trace, unsupported model/cost claim, dependency installation, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-009 - Bean Wiki Green Replay Attempt 3

## Context

UNIT-008 repaired the portable continuity contradiction exposed by frozen Bean
attempt 2. The exact product passed canonical W4a, independent W4b, and the
complete Runtime verification boundary. Attempt 3 is therefore a fresh
consumer replay, not a repair of either preserved failure.

## Inputs

- Runtime product `b82042eba58f1e06e1e73130a189cb72245462a0`
- Runtime lifecycle close `da15ddf6c9e06c89368b3ccc53c4fca603165b1b`
- Bean baseline `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- UNIT-008 W4a, independent W4b, and canonical verification evidence
- Original red pilot plus the two frozen green-attempt reports
- `bean-wiki-editorial-ops` and Bean's host editorial SSOT

## Target Files

- Sanitized Bean green fixture and successful pilot report
- UNIT-009 W4a and independent W4b evidence
- Runtime pilot validator and regressions only if observed evidence requires a
  narrowly scoped correction
- Canonical task, unit, claim, pointer, classifier, board, assumption, and
  evidence-index projections
- Disposable attempt-3 host evidence and read-only editorial-review artifacts

## Fixed Boundaries

- Runtime product: `b82042eba58f1e06e1e73130a189cb72245462a0`
- Runtime lifecycle close: `da15ddf6c9e06c89368b3ccc53c4fca603165b1b`
- Runtime template tree: `d61713bc4066d4ea549efcc7826da10929e64e94`
- Bean baseline: `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Attempt-3 path: `.pilot-worktrees/bean-wiki-task-ar-648-green-3`
- Attempt-3 branch: `codex/task-ar-648-agent-runtime-green-pilot-3`

## Scope

Install `core+web-content`, run three bounded offline traces, and promote green
evidence only if all continuity, ownership, Git, editorial, routing, Scribe,
Compound, and zero-external-effect assertions are observed. The Bean
editorial specialist is read-only and may produce only its review artifact.

## Steps

1. Register and T3-anchor this Runtime unit, verify plan selection, and create
   its default working-tree claim.
2. Snapshot Runtime product provenance plus Bean primary and frozen-attempt
   identities before creating attempt 3.
3. Create the fresh Bean worktree at the exact baseline and capture host,
   backlog, article, and complete content digests.
4. Plan, safe-apply, lock, doctor, and reconcile the exact template.
5. Register three local Bean tasks and run adoption plus the strict
   pointer/claim/sidecar governance journey.
6. Run one selective read-only editorial specialist under the Bean editorial
   operations contract.
7. Record and retrieve one Compound, then prove restart and Scribe state from
   distinct local processes.
8. Regenerate final projections, run Bean and Runtime verification, sanitize
   evidence, complete W4a, and obtain fresh independent W4b.

## Acceptance Criteria

- Exact Runtime and Bean provenance is recorded and all primary/frozen
  worktrees remain unchanged.
- Adoption and immediate/post-registration reconcile have zero conflicts;
  the no-STATUS pointer continuity journey passes without moving Bean HEAD.
- All host, backlog, article, and complete content digests match before and
  after.
- The three bounded task/unit/claim traces complete with truthful, distinct
  routing and provider-observation fields.
- The editorial review is the only specialist-written artifact and all
  `src/content/**` bytes remain unchanged.
- Compound retrieval, cross-process restart, fresh Scribe projection, local
  Bean validation, and integer-zero external effects are observed.
- The sanitized fixture, W4a, and independent W4b pass before Allimbot.

## Verification

- `python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green.json --check`
- `python -m pytest tests/test_pilot_acceptance.py -q`
- The focused routing, claim, continuity, adoption, ownership, and sanitizer
  commands declared in frontmatter
- `python scripts/owner_governance_gate.py`
- `python -m pytest -q`

## Handoff

Report exact provenance, selection and ownership counts, every preserved
digest, continuity mode and sidecar agreement, task and routing traces,
Compound retrieval, restart identities, Scribe freshness, Bean validation,
Git invariants, zero-effect counters, fixture digest, W4a, and W4b.

## Deliberate Exclusions

- No article, content registry, generated index, or host editorial file edit.
- No consumer commit or explicit SCM-persistence opt-in.
- No dependency installation, provider-live request, credential access, or
  network delivery.
- No Allimbot action before this unit passes independent W4b.
- No version, tag, package, release, push, publish, or deployment action.

## Stop Boundary

Any P0/P1 or mismatch in provenance, continuity, Git, content, ownership,
task trace, routing truth, Scribe output, Compound retrieval, or integer-zero
external-effect counters freezes attempt 3 as evidence and blocks Allimbot.
