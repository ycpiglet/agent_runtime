---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-015
work_uid: 13771fb3-fa13-42f4-af50-0f778504c535
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-015
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-30T05:37:59+09:00
updated_at: 2026-07-30T06:21:13+09:00
started_at: 2026-07-30T05:45:22+09:00
completed_at: 2026-07-30T06:21:13+09:00
origin_type: defect_remediation
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-014.md
created_by: codex-root-v080-planner
summary: Replace the single red-only pilot oracle with a fail-closed versioned contract registry and bind sanitized isolation projections to validated raw evidence
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-054522-task-ar-648-ar648015.json
escalation_triggers:
  - data_integrity
  - repeated_failure
  - cross_cutting
context: Bean attempt 5 completed adoption, three bounded traces, preservation, delayed taskset freshness, and causal isolation, but independent W4b found two Runtime P1s. Pilot acceptance is keyed only by host and embeds one historical red execution, while raw isolation proof requires absolute roots that the public sanitizer forbids. The consumer is frozen and must not be patched. This Runtime-only unit preserves the original red evidence, registers the truthful green execution declaratively, and establishes an explicit raw-to-portable evidence boundary before any sixth Bean replay.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-5.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-014.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-014.md
  - agents/project/knowledge/compounds/records/COMPOUND-20260730-053118-pilot-acceptance-must-select-an-immutable-run-co-316cbd00f97e.json
  - agents/project/knowledge/compounds/records/COMPOUND-20260730-053119-isolation-evidence-needs-a-verifiable-sanitized-e1fd6062dba6.json
  - tests/fixtures/pilots/bean-wiki/evidence.json
  - tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json
  - tests/fixtures/pilots/bean-wiki/isolation-green-attempt-5.json
  - agent-runtime-lifecycle@25ef558d602fda4685b40af39a57f3be4a3c2dab
target_files:
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - new:tests/fixtures/pilots/contracts/bean-wiki-v080-red-pilot.json
  - new:tests/fixtures/pilots/contracts/bean-wiki-v080-green-attempt-5.json
  - scripts/pilot_isolation_gate.py
  - tests/test_pilot_isolation_gate.py
  - tests/fixtures/pilots/bean-wiki/isolation-green-attempt-5.json
  - new:docs/pilot-acceptance-contract.md
  - docs/pilot-isolation-contract.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-015.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-015.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-015.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - agents/project/knowledge/compounds/INDEX.json
  - agents/runtime/a2a/messages.jsonl
  - new:agents/runtime/instances/codex-root-task-ar-648-015.json
  - agents/runtime/pane_events/pane-events.jsonl
  - new:agents/runtime/task_claims/CLAIM-20260730-054522-task-ar-648-ar648015.handoff.md
  - new:agents/runtime/task_claims/CLAIM-20260730-054522-task-ar-648-ar648015.json
  - new:agents/runtime/task_claims/CLAIM-20260730-054522-task-ar-648-ar648015.log.md
  - BACKLOG-BOARD.md
  - ARCHIVE-INDEX.md
  - reviews/INDEX.md
scope: Modify only the Runtime acceptance and isolation-evidence lifecycle. Keep shared safety checks executable and move run-specific immutable expectations to strict declarative contracts selected by both host and pilot_id. Add a sanitized isolation projection that contains no local root but is bound to the SHA-256 of a raw v1 artifact that already passed physical-root validation. Preserve historical red semantics and accept attempt 5 only through its own exact green contract. No consumer repository, provider, dependency, package, version, release, or external system action is allowed.
acceptance:
  - Contract records use a versioned schema and are selected by the exact host plus pilot_id pair; unknown hosts, unknown pilots, duplicate pairs, malformed records, unsafe paths, cross-host reuse, and invalid digests fail closed.
  - Shared evidence invariants remain code-owned: host/content preservation, claim identity, routing truth, Compound/restart/Scribe proof, required integer-zero external effects, and P0 blocking behavior cannot be disabled by a contract.
  - Run-specific values are declarative and strict: semantic evidence digest, result, baselines, selection/content counts, reconcile conflicts, exact task identities, finding priorities, verification counters, and required external-effect keys.
  - The historical red fixture remains byte- and semantic-identical at semantic SHA-256 e8a6119f3c6cef815c352600188f57c48e669e9d650b3e4e1b67f751a1d8582e and passes only its red contract.
  - The attempt-5 fixture remains truthful at semantic SHA-256 8a56c8e5a89bfb5bbd7c6224be70f1ec69e41c339dcfe5b0c542b0b26361c39f and passes only its green contract.
  - Semantic mutation of either fixture, including unknown fields, wrong task/claim status, downgraded findings, unverified model usage, or nonzero external effects, remains rejected.
  - Raw v1 isolation validation continues to require canonical absolute disjoint roots and contained observed writes.
  - A deterministic sanitized v2 projection removes every local root, retains checkout IDs, roles, snapshots, attribution, and observed-write identity, and binds them to raw evidence SHA-256 761b236f6ad9f1fd99cb88e688ffefb75422e0e177e5fc8422b1738fbcfd52b1 plus the recorded zero-block raw decision.
  - Sanitized v2 validation rejects missing or malformed raw binding, unknown or duplicate checkout IDs, observed writes not mapped to disposable targets, snapshot/attribution drift, absolute-path leakage, or an asserted raw decision with blockers.
  - Contract-bound artifact verification detects any sanitized isolation projection drift; diagnostics name the selected contract and do not hard-code red-pilot language.
  - Historical red, truthful green, unknown/duplicate/malformed/cross-host contract, semantic tamper, absolute-path, raw/projection binding, and CLI regressions pass.
  - Repository sanitizer, exact mirror, asset usage, Owner governance, focused suites, and full suite pass on one exact Runtime product before W4a and fresh independent W4b.
  - Bean attempts, controls, primary, Autofolio, Allimbot, version, tag, package, push, publish, deployment, credential, network, and provider-live counters remain zero.
verification:
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence.json --check --json
  - python scripts/pilot_acceptance.py --host bean-wiki --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json --check --json
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/bean-wiki/isolation-green-attempt-5.json --check --json
  - python -m pytest tests/test_pilot_acceptance.py tests/test_pilot_isolation_gate.py -q
  - python scripts/compound_record.py check
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report exact pre/post product commits and trees, both contract identities and semantic digests, unchanged historical red bytes, green acceptance output, raw and sanitized isolation digests and proof scopes, every fail-closed adversarial result, sanitizer/mirror/asset/Owner results, focused and full test totals, W4a, fresh independent W4b, zero consumer/external actions, and the exact next-product boundary for a new Bean attempt 6.
stop_condition: Stop immediately on any P0 or P1, weakened shared invariant, red evidence drift, green evidence falsification, ambiguous contract selection, fail-open registry or projection behavior, local path leakage, raw/projection binding loss, fixture mutation outside the declared conversion, consumer repository write, dependency installation, provider-live call, external effect, Allimbot worktree creation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
verified_at: 2026-07-30T06:21:13+09:00
verified_by: codex-root-task-ar-648-015
evidence_refs:
  - reviews/W4A-2026-07-30-unit-task-ar-648-015.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-015.md
review_refs:
  - reviews/W4A-2026-07-30-unit-task-ar-648-015.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-015.md
resolution: done
closed_by: codex-root-task-ar-648-015
measurement_unavailable_reason: UNIT-015 execution occurred inside the broader TASK-AR-648 remediation session without reliable per-unit wall-clock or provider token/cost metering; actual provider usage remained unverified and no savings claim was made.
---

# UNIT-TASK-AR-648-015 - Versioned Pilot Evidence Contracts

## Context

Attempt 5 is useful, independently reviewed consumer evidence, but the Runtime
cannot truthfully accept or publicly preserve it. This unit repairs that
evidence boundary only. It does not rerun Bean or change the consumer.

## Inputs

- UNIT-014 pilot report, W4a, fresh independent W4b, and two Compound records
- Historical red and truthful attempt-5 green evidence fixtures
- Attempt-5 raw v1 isolation evidence and its recorded passing decision
- Runtime lifecycle baseline `25ef558d602fda4685b40af39a57f3be4a3c2dab`

## Target Files

- Pilot acceptance script, tests, and two new declarative contract records
- Pilot isolation script, tests, public attempt-5 projection, and contract docs
- UNIT-015 W4a/W4b plus canonical task, unit, pointer, assumptions, board,
  classifier, Compound index, runtime sidecars, and review index

## Scope

Repair only Runtime pilot-evidence selection and portability. No consumer,
provider, dependency, version, release, or remote surface is in scope.

## Design Boundary

Keep generic safety policy in executable validation. Store only immutable,
run-specific observations in contract records. Select one exact record by
`(host, pilot_id)` and reject ambiguity.

Keep raw checkout roots in local v1 isolation evidence long enough to validate
physical disjointness and write containment. Persist a v2 public projection
only after that raw gate passes; bind the projection to the raw byte digest and
retain every non-secret identity/snapshot/attribution field.

## Steps

1. Register and T3-anchor this unit; prove readiness and canonical selection
   before creating a default working-tree claim.
2. RED: preserve reproductions for the red-only lookup and raw/sanitizer
   conflict, plus adversarial registry/projection cases.
3. Implement strict declarative contract loading and exact pair selection
   without weakening shared pilot invariants.
4. Extend isolation evidence with a deterministic raw-to-sanitized projection
   and validate the attempt-5 projection against its bound raw digest.
5. Re-run both historical red and truthful green acceptance, focused
   adversarial tests, sanitizer, canonical governance, and the full suite.
6. Freeze one exact product, write W4a, and obtain fresh independent W4b.

## Acceptance Criteria

- Exact `(host, pilot_id)` selection accepts only the matching immutable
  contract and fails closed for unknown, duplicate, malformed, cross-host, or
  drifting records.
- Generic safety checks stay executable and cannot be disabled by a contract.
- Historical red and truthful attempt-5 green semantics remain unchanged and
  pass only their own records.
- The public isolation fixture contains no local root, is bound to the exact
  passing raw v1 evidence digest, and rejects identity, snapshot, attribution,
  write-target, or binding tamper.
- Focused adversarial tests, public sanitizer, governance gates, full suite,
  W4a, and fresh independent W4b pass on one exact product.

## Verification

- Both declared red and green `pilot_acceptance.py --check --json` commands
- Public attempt-5 `pilot_isolation_gate.py --check --json`
- Focused acceptance/isolation pytest suite and adversarial mutations
- Compound, mirror, runtime-asset, Owner-governance, and public-sanitizer gates
- Full pytest suite on the exact candidate

## Stop Boundary

- No Bean or Allimbot worktree creation or write
- No edit to Bean article, editorial assets, or consumer Runtime projection
- No dependency or provider-live execution
- No version, tag, package, push, publish, deployment, or release action

## Handoff

Return the exact product boundary and proof that both old red evidence and new
green evidence are accepted only by their own immutable contracts, while raw
local isolation data is replaced by a sanitized, digest-bound public
projection. A later unit must use that exact approved product for a completely
fresh Bean attempt 6.

## Outcome

Completed at exact Runtime product
`4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`, tree
`b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f`. Historical red and truthful
attempt-5 evidence each pass only their exact immutable contract. The public
v2 isolation projection contains no local root and is bound to the validated
raw v1 byte digest. Focused `41` and full `2739 passed, 3 skipped` verification,
W4a, and fresh independent W4b all report no P0/P1. Bean attempt 6 must be
registered separately; Allimbot and release remain blocked.
