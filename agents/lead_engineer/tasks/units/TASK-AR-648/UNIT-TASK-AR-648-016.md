---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-016
work_uid: b27f62b7-ceab-43ec-b6b3-a6d8325ab2ce
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-016
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T06:26:06+09:00
updated_at: 2026-07-30T06:26:06+09:00
origin_type: pilot_replay
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-015.md
created_by: codex-root-v080-planner
summary: Replay Bean Wiki from a sixth fresh disposable checkout using the independently approved versioned acceptance and sanitized-isolation product
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - repeated_failure
  - cross_cutting
context: Bean attempt 5 completed adoption, exactly three offline traces, preservation, delayed taskset freshness, and causal isolation, but exposed two Runtime evidence-contract P1s. UNIT-015 repaired only those Runtime defects at exact product 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2 and passed W4a plus fresh independent W4b with no P0/P1. This sixth replay must use a new disposable target, a new immutable same-commit control, a detached exact-product Runtime checkout, and a freshly captured raw isolation baseline. It must then prove the raw-to-sanitized evidence path and exact `(host, pilot_id)` acceptance contract without modifying Bean content or any historical checkout. Allimbot remains blocked until this unit passes.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-5.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-014.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-014.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-015.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-015.md
  - docs/pilot-acceptance-contract.md
  - docs/pilot-isolation-contract.md
  - agent-runtime-product@4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2
  - agent-runtime-lifecycle@57c7ba45ad5d7c56fed2d7bf5cebb4aee60e58ae
  - bean-wiki@357eee4fd8c29c33a949adbe3a0ffa80c874bf42
target_files:
  - new:tests/fixtures/pilots/bean-wiki/evidence-green-attempt-6.json
  - new:tests/fixtures/pilots/bean-wiki/isolation-green-attempt-6.json
  - new:tests/fixtures/pilots/contracts/bean-wiki-v080-green-attempt-6.json
  - new:reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-6.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-016.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-016.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-6-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-6-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-016.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - agents/project/knowledge/compounds/INDEX.json
  - agents/runtime/a2a/messages.jsonl
  - agents/runtime/pane_events/pane-events.jsonl
  - BACKLOG-BOARD.md
  - ARCHIVE-INDEX.md
  - reviews/INDEX.md
scope: After registration, T3 re-anchoring, readiness, canonical selection, and a default working-tree Runtime claim, create a detached Runtime product checkout pinned exactly to 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2, a detached Bean frozen-control checkout pinned to 357eee4fd8c29c33a949adbe3a0ffa80c874bf42, and only /home/keti-itp-01/ycpiglet/.pilot-worktrees/bean-wiki-task-ar-648-green-6 as the writable consumer target on branch codex/task-ar-648-agent-runtime-green-pilot-6 from the same Bean baseline. Capture physical isolation snapshots after checkout creation and before target writes. Apply exact core plus web-content templates and run exactly three offline traces: deterministic adoption verification at worker_low, one selectively invoked read-only coffee-flavor-wheel editorial review at worker_standard under bean-wiki-editorial-ops, and deterministic restart plus Compound plus Scribe verification at worker_low. Raw isolation evidence may exist only as a local transient artifact long enough to pass v1 validation and produce a digest-bound path-free v2 projection. No consumer commit, content edit, dependency installation, provider-live call, publish, deploy, push, credential read, or network delivery is allowed.
acceptance:
  - Runtime execution is pinned to product 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2, product tree b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f, template tree e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f, and packaged-scripts tree 62311b7847f66206a2a33e4bd497750bf074384f; its detached checkout stays clean.
  - Attempt 6 and its new frozen control both start exactly at Bean 357eee4fd8c29c33a949adbe3a0ffa80c874bf42. Control HEAD, complete porcelain-status digest, and tracked-diff digest remain identical.
  - The disposable attempt-6 checkout is the only authorized write root. Control changes, overlapping roots, non-target observed writes, unsupported attribution, or a changed target omitted from observed writes block.
  - Bean primary is a live observation only. Unrelated drift is watch-only; a pilot command or write targeting it blocks. Attempts 1–5, Autofolio, and Allimbot remain observation-only and unwritten.
  - Core plus web-content selection, v2 ownership, safe apply, lock, doctor, immediate reconcile, and post-registration reconcile complete with zero conflicts and exact Runtime/template provenance.
  - A no-STATUS host passes pointer continuity; default claims leave Bean HEAD unchanged and pointer, claim, sidecars, state-sync, RBAC, parallel, continuity, completed taskset, and Owner governance agree.
  - Bean README.md, AGENTS.md, CLAUDE.md, BACKLOG.md, editorial SSOT, configured specialist assets, coffee-flavor-wheel.html, generated article index, and complete src/content manifest retain matching before/after SHA-256 values.
  - Exactly three local task, unit, and claim traces complete: worker_low adoption, worker_standard read-only editorial review, and worker_low restart/Compound/Scribe. Requested and selected tiers, resolved provider, execution surface, observed model, usage, token, cost, and savings fields remain distinct and truthful.
  - Exactly one editorial specialist reads every required Bean editorial input, writes one bounded review artifact, and changes neither src/content nor a generated content index. Its editorial publication decision is reported separately from Runtime harness acceptance.
  - One intentional negative fixture creates a task-linked Compound record; a later semantic lookup retrieves that exact record first with no unrelated match.
  - Two distinct local processes resume the same restart claim; Scribe writes only its configured projection and never edits BACKLOG.md.
  - Raw v1 isolation validates canonical absolute disjoint roots and target-contained writes. Deterministic sanitization emits a v2 projection with no local path, exact raw byte digest, zero-block decision, checkout identities, snapshots, attribution, and observed-write identity.
  - A new strict `bean-wiki` plus `bean-wiki-v080-green-attempt-6` contract binds exact semantic evidence and isolation artifact digests. Historical red and attempt-5 fixtures continue to pass only their existing contracts.
  - Final classifier, state-sync, taskset, reconcile, host/content, diff, editorial, raw isolation, sanitized isolation, and local Runtime acceptance checks pass.
  - Publish, deploy, origin push, consumer commit, credential read, network delivery, dependency installation, provider-live execution, and content mutation counters are integer zero.
  - Canonical W4a and fresh independent W4b pass with no P0/P1 before Allimbot or release work starts.
verification:
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/bean-wiki/isolation-green-attempt-6.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-6.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json --check --json
  - python -m pytest tests/test_pilot_isolation_gate.py tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_taskset_dispatcher.py tests/test_task_claim_dispatcher.py tests/test_work_item_classifier.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
handoff: Report exact Runtime product/lifecycle and Bean baselines, product/template/scripts trees, target/control/live-observation identities and immutable snapshots, raw and sanitized isolation decisions and digests, selection and ownership counts, every preserved digest, continuity and managed-contract proof, delayed taskset proof, three trace/routing records, exact Compound retrieval, restart process identities, Scribe projection, editorial outcome separated from Runtime outcome, Bean validation, Git HEAD invariants, integer-zero external effects, contract identity and semantic digest, W4a, and independent W4b.
stop_condition: Stop immediately on any P0 or P1, Runtime product drift, consumer commit, frozen-control mutation, observed write outside attempt 6, unsupported causality attribution, host/content overwrite, missing or ambiguous Runtime/template provenance, continuity fail-open, host-document workaround, unverified claim, missing or extra task trace, more than one editorial specialist, unrelated Compound retrieval, unsupported model/cost claim, raw validation failure, sanitized-path leak, contract ambiguity, dependency installation, provider-live call, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-016 - Bean Wiki Green Replay Attempt 6

## Context

Replay the independently approved versioned-contract Runtime product in one
new disposable Bean checkout. A second new Bean checkout is the immutable
control. Prior attempts are historical evidence; the live primary is an
observation surface whose unrelated drift is not pilot-caused.

## Inputs

- Runtime product: `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`
- Runtime product tree: `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`
- Runtime template tree: `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f`
- Runtime packaged-scripts tree: `62311b7847f66206a2a33e4bd497750bf074384f`
- Runtime lifecycle baseline: `57c7ba45ad5d7c56fed2d7bf5cebb4aee60e58ae`
- Bean baseline: `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`
- Disposable target: `.pilot-worktrees/bean-wiki-task-ar-648-green-6`
- Frozen control: `.pilot-worktrees/bean-wiki-task-ar-648-control-6`

## Scope

Adopt exact `core+web-content` into only the attempt-6 disposable worktree.
Capture a new frozen-control and live-primary baseline before target writes.
Run exactly three offline traces and make no Runtime product, Bean content,
frozen checkout, Allimbot, or external-system change.

## Target Files

- Runtime attempt-6 acceptance contract plus acceptance and isolation fixtures
- Runtime attempt-6 pilot report, W4a, and fresh independent W4b
- Runtime task, unit, pointer, plan assumptions, classifier, board, Compound
  index, runtime sidecars, archive index, and review index
- Disposable Bean Runtime projection and bounded local pilot evidence only

## Steps

1. Register this unit and T3 assumptions; prove readiness and canonical
   selection before claiming it.
2. Create the exact detached Runtime product, fresh control, and disposable
   target; capture physical isolation baselines before writes.
3. Install `core+web-content` into only the target and prove adoption,
   ownership, lock, doctor, parity, and preservation.
4. Run exactly three traces, using low routing for deterministic work and one
   standard editorial specialist for judgment.
5. Prove Compound retrieval, two-process restart, Scribe, delayed taskset
   freshness, continuity, Owner governance, and causal isolation.
6. Validate raw isolation, produce the path-free bound projection, register
   the exact attempt-6 acceptance contract, and obtain W4a plus independent
   W4b on the exact evidence.

## Acceptance Criteria

- Exact Runtime and Bean provenance, fresh control immutability, and causal
  isolation pass.
- Adoption, lock, doctor, reconcile, taskset, continuity, Scribe, Compound,
  Owner governance, and exactly three trace records pass.
- Host, editorial, and content bytes plus Bean HEAD are preserved; all
  external-effect counters are integer zero.
- Raw isolation passes before a deterministic path-free projection is
  persisted and bound by exact digest.
- The attempt-6 contract accepts only its semantic evidence; red and attempt-5
  contracts retain exact historical behavior.
- W4a and fresh independent W4b approve with no Runtime P0/P1.

## Verification

- Attempt-6 raw and sanitized isolation validation
- Attempt-6, attempt-5, and historical-red exact acceptance validation
- Focused Runtime isolation, adoption, claim, continuity, and ownership tests
- Exact Runtime mirror, asset-usage, Owner-governance, and sanitizer gates
- Bean editorial/content/diff checks and installed taskset completion gate

## Handoff

Return exact product and consumer provenance, snapshots and attribution,
adoption counts, preservation digests, the three routing traces, editorial
verdict, Compound/restart/Scribe evidence, raw and sanitized evidence digests,
exact contract and semantic digest, zero-effect counters, W4a, and fresh
independent W4b.

## Promotion Rule

Bean becomes independently green only if both review stages approve with no
Runtime P0/P1. The separate article review may still request editorial
revision; it cannot be misreported as a Runtime harness failure or publication
approval.

## Stop Boundary

- No Bean primary, prior attempt, frozen control, Autofolio, or Allimbot write.
- No article, generated content index, editorial SSOT, or dependency change.
- No provider-live execution or unsupported model/cost/savings observation.
- No consumer commit and no release, version, tag, package, remote, publish,
  or deployment action.
