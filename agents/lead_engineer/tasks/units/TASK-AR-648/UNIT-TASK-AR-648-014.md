---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-014
work_uid: 6342347f-9cc4-48e2-a52b-8667610b18fb
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-014
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T04:45:18+09:00
updated_at: 2026-07-30T04:45:18+09:00
origin_type: pilot_replay
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-013.md
created_by: codex-root-v080-planner
summary: Replay Bean Wiki from a fifth fresh disposable checkout with a new frozen control after the exact Runtime mirror and isolation repairs passed independent review
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - repeated_failure
  - cross_cutting
context: Bean attempt 4 completed all three bounded local traces but exposed a packaged taskset timestamp regression and an isolation contract that treated unrelated live-primary changes as pilot failure. UNIT-012 repaired portable script parity and introduced causal pilot isolation; UNIT-013 closed the remaining missing-side mirror blind spot at exact product 34427e1fe18d6c4db8a81142616ccad24cc6e7de with W4a and fresh independent W4b. This fifth replay must use a new disposable target and a new immutable control, not mutate or trust the changing status hashes of earlier attempts, and prove the complete offline Bean journey before Allimbot can begin.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-4.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-011.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-011.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-012.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-012.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-013.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-013.md
  - docs/pilot-isolation-contract.md
  - agent-runtime-product@34427e1fe18d6c4db8a81142616ccad24cc6e7de
  - agent-runtime-lifecycle@60df0ebd4ce0d54cbc065aaddb80ea60828551ec
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - new:tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json
  - new:tests/fixtures/pilots/bean-wiki/isolation-green-attempt-5.json
  - new:reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-5.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-014.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-014.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-5-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-5-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-014.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: After Runtime registration, T3 re-anchoring, readiness, canonical selection, and a default working-tree Runtime claim, create one detached Runtime product worktree pinned to 34427e1fe18d6c4db8a81142616ccad24cc6e7de, one detached Bean frozen-control worktree pinned to 357eee4fd8c29c33a949adbe3a0ffa80c874bf42, and only /home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-5 as the writable consumer target on branch codex/task-ar-648-agent-runtime-green-pilot-5 from the same Bean baseline. Capture all isolation snapshots immediately after creation and before target writes. Apply exact core plus web-content templates, preserve Bean editorial assets as host-owned, and run exactly three offline traces: deterministic adoption verification at worker_low, one selectively invoked read-only coffee-flavor-wheel editorial review at worker_standard under bean-wiki-editorial-ops, and deterministic restart plus Compound plus Scribe verification at worker_low. No consumer commit, content edit, dependency installation, provider-live call, publish, deploy, push, credential read, or network delivery is allowed.
acceptance:
  - Runtime execution is pinned to product 34427e1fe18d6c4db8a81142616ccad24cc6e7de, product tree d94bf33a89482a6299b454e6594404afef7adfcf, template tree e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f, and packaged-scripts tree 62311b7847f66206a2a33e4bd497750bf074384f; its detached product checkout stays clean.
  - Attempt 5 and its new frozen control both start exactly at Bean 357eee4fd8c29c33a949adbe3a0ffa80c874bf42. The control's HEAD, complete porcelain-status digest, and tracked-diff digest remain identical across the pilot.
  - The only observed write root is the disposable attempt-5 checkout. Its expected Runtime projection is attributed authorized_target; any frozen-control change, overlapping root, or observed write outside the target blocks.
  - Bean primary is recorded as live_observation. Unrelated state drift is a watch and is never attributed to the pilot; a command or write trace targeting it still blocks.
  - Core plus web-content selection, v2 ownership, plan, safe apply, lock, doctor, immediate reconcile, and post-registration reconcile complete with zero conflicts and exact Runtime/template provenance.
  - The installed taskset gate accepts real ISO-second board timestamps after a later render, and installed work.py now succeeds without a consumer patch.
  - A no-STATUS host passes standby pointer continuity; default claims leave Bean HEAD unchanged and pointer, claim, sidecars, state-sync, RBAC, parallel, continuity, complete taskset, and Owner governance agree.
  - Bean README.md, AGENTS.md, CLAUDE.md, BACKLOG.md, editorial SSOT, configured specialist assets, coffee-flavor-wheel.html, the generated article index, and the complete src/content manifest retain matching before/after SHA-256 values.
  - Exactly three local task, unit, and claim traces complete: worker_low adoption, worker_standard read-only editorial review, and worker_low restart/Compound/Scribe. Requested, selected, resolved-provider, execution-surface, observed-model, usage, token, cost, and savings fields remain distinct and truthful.
  - The editorial specialist reads every declared Bean editorial input, writes only one bounded review artifact, and never changes src/content or a generated content index.
  - One intentional negative fixture creates a task-linked Compound record; semantic lookup retrieves that exact record first with no unrelated match.
  - Two distinct local processes resume the same restart claim; Scribe writes only its configured projection and never edits BACKLOG.md.
  - Final classifier, state-sync, taskset, reconcile, host/content, diff, editorial, pilot-isolation, and local Runtime acceptance checks pass.
  - Publish, deploy, origin push, consumer commit, credential read, network delivery, dependency installation, and content mutation counters are all integer zero.
  - The sanitized attempt-5 fixture, canonical W4a, and fresh independent W4b pass with no P0/P1 before Allimbot or release work starts.
verification:
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/bean-wiki/isolation-green-attempt-5.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json --check
  - python -m pytest tests/test_pilot_isolation_gate.py tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
handoff: Report exact Runtime product/lifecycle and Bean baselines, product/template/scripts trees, target/control/live-observation identities and immutable snapshots, isolation-gate decision, selection and ownership counts, every preserved digest, continuity and managed-contract proof, delayed taskset timestamp proof, installed work-now result, three trace/routing records, exact Compound retrieval, restart process identities, Scribe projection, Bean validation, Git HEAD invariants, integer-zero external effects, sanitized fixture digest, W4a, and independent W4b.
stop_condition: Stop immediately on any P0 or P1, Runtime product drift, consumer commit, frozen-control mutation, observed write outside attempt 5, unsupported causality attribution, host/content overwrite, missing or ambiguous Runtime/template provenance, continuity fail-open, host-document workaround, unverified claim, missing task trace, unrelated Compound retrieval, unsupported model/cost claim, dependency installation, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-014 - Bean Wiki Green Replay Attempt 5

## Context

Replay the independently approved exact Runtime product in one new disposable
Bean checkout. A second new Bean checkout is the immutable control. Existing
attempts are historical evidence only; the live primary is an observation
surface whose unrelated drift cannot be called pilot-caused.

## Inputs

- Runtime product: `34427e1fe18d6c4db8a81142616ccad24cc6e7de`
- Runtime product tree: `d94bf33a89482a6299b454e6594404afef7adfcf`
- Runtime template tree: `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f`
- Runtime packaged-scripts tree: `62311b7847f66206a2a33e4bd497750bf074384f`
- Runtime lifecycle baseline: `60df0ebd4ce0d54cbc065aaddb80ea60828551ec`
- Bean baseline: `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Disposable target: `.pilot-worktrees/bean-wiki-task-ar-648-green-5`
- Frozen control: `.pilot-worktrees/bean-wiki-task-ar-648-control-5`

## Target Files

- Runtime attempt-5 acceptance and isolation fixtures
- Runtime attempt-5 pilot report, W4a, and independent W4b
- Runtime task, unit, pointer, plan-assumption, classifier, board, and evidence
  lifecycle projections
- Disposable Bean Runtime projection and bounded pilot evidence only

## Scope

Adopt exact `core+web-content` into only the attempt-5 disposable worktree.
Capture a new frozen-control baseline and a live-primary observation before
any target write. Run exactly three offline traces and make no Runtime product,
Bean content, frozen checkout, Allimbot, or external-system change.

## Steps

1. Register this unit and T3 assumptions, then prove readiness and canonical
   selection before claiming it.
2. Create the exact Runtime product, fresh frozen-control, and disposable
   attempt-5 worktrees; capture the causal-isolation baseline before writes.
3. Install `core+web-content` into only the disposable target and prove
   adoption, ownership, lock, doctor, parity, and preservation.
4. Run the three bounded offline traces with low-cost deterministic routing by
   default and one selectively invoked standard editorial specialist.
5. Close all local traces serially, re-render after a distinct wall-clock
   second, and prove taskset, continuity, Owner governance, isolation, and
   Scribe.
6. Promote no evidence until Runtime W4a and a fresh independent W4b both
   approve the exact replay with no P0/P1.

## Acceptance Criteria

- Runtime, Bean baseline, target, control, and live-observation provenance are
  exact and causal-isolation evidence passes.
- Adoption, lock, doctor, delayed taskset render, installed `work.py now`,
  continuity, Scribe, Compound, and Owner governance all pass.
- Three trace records are complete and model/provider/cost fields remain
  truthful.
- Host/editorial/content bytes and Bean HEAD are preserved; all external
  effect counters are zero.
- W4a and a fresh independent W4b approve with no P0/P1.

## Verification

- Attempt-5 pilot-isolation and pilot-acceptance validators
- Focused Runtime isolation, adoption, claim, continuity, and ownership tests
- Exact Runtime mirror, asset-usage, Owner-governance, and sanitizer gates
- Bean local editorial/content/diff checks and complete installed taskset gate

## Handoff

Return exact Runtime and Bean provenance, all isolation snapshots and
attribution, adoption/ownership counts, preservation digests, the three
routing traces, Compound/restart/Scribe evidence, zero-effect counters,
attempt-5 fixtures, W4a, and independent W4b.

## Stop Boundary

- No Bean primary, prior attempt, frozen-control, Autofolio, or Allimbot write.
- No article, content index, editorial SSOT, host-document workaround, or
  dependency change.
- No provider-live call or unsupported cost/savings observation.
- No consumer commit and no release, version, tag, package, remote, publish,
  or deployment action.
