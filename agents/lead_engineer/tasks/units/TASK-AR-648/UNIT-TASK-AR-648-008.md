---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-008
work_uid: 183265b6-c7d8-45e3-9193-4d1a00f80dc0
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-008
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-29T23:34:46+09:00
updated_at: 2026-07-30T00:23:19+09:00
started_at: 2026-07-30T00:22:20+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md
created_by: codex-root-v080-planner
summary: Close the portable pointer, claim, sidecar, and gate continuity contract before any new consumer replay
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-002220-task-ar-648-648008.json
escalation_triggers:
  - cross_cutting
  - data_integrity
  - repeated_failure
context: Bean Wiki attempt 2 proved that a fresh core installation can create a valid default claim and then block its own parallel-worktree gate because no STATUS candidate is installed or diagnosed. Independent W4b confirmed P0. The Runtime already installs a canonical NEXT-SESSION-POINTER plus claim handoff/log sidecars and already projects claim identity through state-sync and RBAC gates, so this unit closes that existing contract without creating a second monolithic status source.
inputs:
  - reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md
  - reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md
  - reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-remediation-registration.md
  - agents/project/knowledge/compounds/records/COMPOUND-20260729-233100-portable-continuity-must-close-the-adoption-to-f-d70d307c6cef.json
  - agent-runtime@573b3cdfbcc5e7255bbb2a503b7568e723c946a6
target_files:
  - scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - tests/test_parallel_worktree_gate.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - tests/test_task_claim_dispatcher.py
  - src/agent_runtime/doctor.py
  - tests/test_doctor.py
  - src/agent_runtime/templates/project/agents/project/NEXT-SESSION-POINTER.yml
  - src/agent_runtime/templates/project/scripts/check_agent_docs.py
  - tests/test_template_smoke.py
  - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - src/agent_runtime/templates/project/docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md
  - tests/test_inventory_sync_sanitize.py
  - tests/fixtures/host/agent_runtime.lock.json
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-008.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-008.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-008.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Implement a strict pointer-plus-claim-sidecar continuity fallback for hosts without a STATUS ledger, extend deterministic projection data only as required, add doctor and installed-doc diagnostics, and prove the complete fresh-core adoption-to-first-claim journey. Do not mutate any consumer repository or broaden into UI, release, profile thinning, provider telemetry, or legacy document-store redesign.
acceptance:
  - The current product fails a deterministic RED journey at the same status-missing finding observed in frozen Bean attempt 2.
  - A present STATUS candidate retains the existing handoff-marker validation and an invalid STATUS cannot be bypassed by a valid pointer.
  - With both STATUS candidates absent, only a canonical fresh pointer whose active claim paths and current-agent fields exactly match all active claims can satisfy continuity.
  - Missing, placeholder, malformed, stale, duplicate, extra, partial, or mismatching pointer state blocks with a stable reason code.
  - Every active claim still requires existing handoff and log sidecars.
  - Claim creation remains claim-only and default working_tree persistence leaves HEAD unchanged; the serial projection command emits every field the strict pointer contract needs.
  - Doctor explicitly reports the effective continuity path and blocks a missing or structurally unusable pointer before first work.
  - Installed check_agent_docs no longer reports a missing mandatory STATUS board when the strict pointer path is available, without weakening unrelated document checks.
  - Root and packaged parallel gate and claim dispatcher copies are byte-identical; selected template, lock, sanitizer, and dependency-closure checks pass.
  - A clean installed core host completes default claim, projection, parallel gate, state-sync, RBAC, and owner-governance checks without a STATUS seed.
  - Focused W4a, routing checks, full suite, and a fresh independent W4b pass on one exact product SHA with no P0/P1.
verification:
  - python -m pytest tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_template_smoke.py tests/test_inventory_sync_sanitize.py -q
  - python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Report the original RED command and finding, the exact pointer/claim field matrix and negative cases, doctor path decision, installed-host journey, source-template hashes, unchanged default SCM behavior, focused/routing/full counts, exact product SHA, Compound retrieval, W4a evidence, and independent W4b verdict.
stop_condition: Stop on a fail-open pointer fallback, stale or partial state acceptance, automatic claim-time pointer mutation, weakened present-STATUS validation, source/template drift, missing RED evidence, new P0/P1, consumer mutation, Allimbot work, release/version/tag/package action, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-008 - Portable Continuity Contract

## Context

Frozen Bean attempt 2 exposed a cross-layer bootstrap contradiction after a
valid no-commit claim. Independent review rejected the product and selected a
strict canonical-pointer fallback over a static STATUS seed.

## Inputs

- `reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md`
- `reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md`
- `reviews/REVIEW-2026-07-30-task-ar-648-portable-continuity-t3-replan.md`
- `agents/project/knowledge/compounds/records/COMPOUND-20260729-233100-portable-continuity-must-close-the-adoption-to-f-d70d307c6cef.json`
- Agent Runtime baseline `a3a5eebe0584a7d5359a15c43f205b9770b7cbce`

## Target Files

- Root and packaged `parallel_worktree_gate.py`
- Root and packaged `task_claim_dispatcher.py`
- `src/agent_runtime/doctor.py`
- Installed pointer and document-check templates
- Parallel-gate, claim, doctor, template-smoke, inventory, and routing tests
- Host lock, Runtime protocol, W4a/W4b, and lifecycle evidence

## Scope

Implement and verify a strict pointer-plus-claim-sidecar continuity fallback
inside Agent Runtime. Preserve present-STATUS behavior, default claim
non-persistence, source/template parity, and every consumer/external-effect
stop boundary. Do not implement unrelated readiness-dispatch, UI, profile
thinning, evidence-history, or provider work in this unit.

## Decision

Use the artifacts already owned by portable core: one live pointer, exact
claim records, and existing claim handoff/log sidecars. STATUS remains an
optional host-owned richer ledger and, when present, keeps its current strict
validation.

## Steps

1. Reproduce the frozen Bean failure in a deterministic fresh-core RED test.
2. Add negative contract tests before changing production code.
3. Extend deterministic claim projection fields without writing the pointer.
4. Implement strict pointer fallback in root and template parallel gates.
5. Add doctor and installed document-check diagnostics.
6. Run a clean installed-host claim/projection/governance journey.
7. Run focused, routing, ownership, sanitizer, governance, and full W4a.
8. Obtain a fresh independent W4b on the exact product SHA.

## Acceptance Criteria

- Preserve a deterministic RED reproduction of the frozen Bean status-missing
  failure before product changes.
- A present invalid STATUS blocks even when a valid pointer exists.
- With no STATUS, only an exact fresh pointer matching all active non-overlay
  claims and current-agent fields passes.
- Missing, placeholder, malformed, stale, duplicate, extra, partial, or
  mismatching pointer state fails with stable reason codes.
- Every active claim continues to require handoff and log sidecars.
- Claim creation stays claim-only; projection emits required fields without
  writing the pointer or moving HEAD.
- Doctor and installed document checks report the effective continuity path.
- A clean installed core host completes the claim-to-governance journey
  without a STATUS seed.
- Root/template parity, lock, inventory, sanitizer, focused, routing, full
  W4a, and independent W4b all pass on one exact SHA with no P0/P1.

## Verification

- `python -m pytest tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py tests/test_doctor.py tests/test_template_smoke.py tests/test_inventory_sync_sanitize.py -q`
- `python -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/owner_governance_gate.py`
- `PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check`
- `python -m pytest -q`

## Handoff

Record the original RED, pointer/claim field matrix, all stable negative
reasons, present-STATUS precedence, doctor decision, installed-host journey,
source/template hashes, unchanged default SCM behavior, exact product SHA,
focused/routing/full counts, Compound retrieval, W4a evidence, and independent
W4b verdict.

## Deliberate Exclusions

- No Bean or Allimbot worktree is created, repaired, or mutated.
- No generic STATUS placeholder is seeded.
- No provider usage, token, cost, or savings claim is inferred.
- No release, version, tag, package, push, publish, or deploy action occurs.

## Stop Boundary

Any fail-open continuity result or independent P0/P1 freezes this unit and
requires another separately claimed repair before consumer replay.
