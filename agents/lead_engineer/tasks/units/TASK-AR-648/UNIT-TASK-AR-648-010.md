---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-010
work_uid: 207de6ba-28dd-49ed-97b9-e07ead9cf2ac
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-010
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-30T01:58:46+09:00
updated_at: 2026-07-30T02:27:30+09:00
started_at: 2026-07-30T02:02:55+09:00
origin_type: pilot_finding
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-009.md
created_by: codex-root-v080-planner
summary: Make the installed continuity documentation contract ownership-aware without weakening portable pointer enforcement
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-020255-task-ar-648-648010.json
escalation_triggers:
  - data_integrity
  - repeated_failure
context: Bean attempt 3 proved the repaired no-STATUS pointer path but independently found a P1 in the next Owner-governance layer. The installed continuity contract unconditionally requires Agent Runtime source-repository wording in Bean README.md, AGENTS.md, and CLAUDE.md even though the latter two are explicitly host-owned and README is not a selected Runtime asset. Consumer edits are prohibited; the Runtime core must distinguish source-repository documentation checks from a lock- and config-proven consumer contract while keeping the pointer and claim journey fail-closed.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-009.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-009.md
  - scripts/continuity_contract_gate.py
  - src/agent_runtime/templates/project/scripts/continuity_contract_gate.py
  - src/agent_runtime/templates/project/AGENT_RUNTIME.md
  - scripts/agent_runtime/config.py
  - tests/test_continuity_contract_gate.py
  - tests/test_owner_governance_consumer_host.py
target_files:
  - scripts/continuity_contract_gate.py
  - src/agent_runtime/templates/project/scripts/continuity_contract_gate.py
  - src/agent_runtime/templates/project/AGENT_RUNTIME.md
  - tests/test_continuity_contract_gate.py
  - tests/test_owner_governance_consumer_host.py
  - tests/fixtures/host/agent_runtime.lock.json
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-010.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-010.md
  - reviews/VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400.json
  - agents/project/knowledge/compounds/INDEX.json
  - new:agents/project/knowledge/compounds/records/COMPOUND-20260730-022253-portable-governance-must-respect-consumer-docume-7f2adb565808.json
  - reviews/PILOT-BEAN-WIKI-v080-GREEN.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-010.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Repair only the portable documentation boundary exposed by Bean attempt 3. Preserve the strict Runtime source-repository contract. In a generated consumer, activate ownership-aware behavior only when v2 config and v2 lock agree, use a managed Runtime entry/contract surface instead of imposing wording on unmanaged or host-owned project docs, and continue validating the pointer schema in every mode. Add fail-closed regressions for missing/malformed config, lock, managed contract, and pointer. Do not mutate any Bean checkout while implementing or verifying this unit.
acceptance:
  - Runtime source-repository README, protocol-document, and pointer checks remain byte-for-byte strict in behavior.
  - A generated consumer with valid v2 config and lock may preserve explicitly host-owned AGENTS.md and CLAUDE.md and an unmanaged README without continuity findings.
  - The consumer path validates equivalent common Runtime entry and self-improvement rules from a lock-proven managed Runtime document.
  - Consumer mode is unavailable when config or lock is missing, malformed, mismatched, or does not prove ownership; such cases block rather than skip.
  - Pointer schema and required fields are checked in source and consumer modes, including when all project protocol docs are host-owned.
  - Unowned or seed-once protocol documents retain strict validation.
  - Root and packaged gate copies are byte-identical, the host lock fixture is fresh, and clean Bean-style installed Owner governance passes after canonical classifier projection.
  - Focused, routing, asset, sanitizer, owner-governance, and full Runtime suites pass before independent W4b.
verification:
  - python -m pytest tests/test_continuity_contract_gate.py tests/test_owner_governance_consumer_host.py -q
  - cmp -s scripts/continuity_contract_gate.py src/agent_runtime/templates/project/scripts/continuity_contract_gate.py
  - python -m pytest tests/test_template_smoke.py tests/test_adoption.py tests/test_config_v2.py tests/test_doctor.py -q
  - python -m pytest tests/test_task_claim_dispatcher.py tests/test_state_sync_gate.py tests/test_parallel_worktree_gate.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Return the exact pre/post product commits and trees, consumer-mode proof requirements, source strictness regressions, pointer fail-closed cases, root/template parity, lock freshness, clean installed-host journey, complete verification counts, W4a, and independent W4b.
stop_condition: Stop on any source-repository weakening, blanket consumer skip, pointer fail-open, ownership decision without valid config-and-lock agreement, consumer document workaround, Bean mutation, unsupported provider/model/cost claim, Allimbot action, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
verified_at: 2026-07-30T02:24:00+09:00
verified_by: codex-root-task-ar-648-010
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400.json
---

# UNIT-TASK-AR-648-010 - Ownership-aware Consumer Continuity Contract

## Context

Bean attempt 3 passed the previously repaired standby and active pointer path.
It then failed the next Owner-governance layer because a source-repository
documentation policy was imposed on host-owned consumer documents. Independent
W4b classified the defect P1 and prohibited a Bean-side workaround.

## Inputs

- `reviews/PILOT-BEAN-WIKI-v080-GREEN.md`
- `reviews/W4A-2026-07-30-unit-task-ar-648-009.md`
- `reviews/W4B-2026-07-30-unit-task-ar-648-009.md`
- Root and packaged `scripts/continuity_contract_gate.py`
- Packaged `AGENT_RUNTIME.md`
- Runtime configuration parser and focused consumer-host tests

## Target Files

- Root and packaged continuity contract gates
- Packaged managed Runtime entry document
- Focused continuity and consumer-owner-governance regressions
- Host lock fixture if template hashes change
- UNIT-010 W4a, independent W4b, verification, and lifecycle projections

## Scope

Separate the source-repository documentation contract from the installed
consumer contract. A consumer exemption must be proven by valid v2 config and
v2 lock ownership, and common Runtime rules must remain on a managed Runtime
surface. Pointer structure is mandatory in every mode.

## Steps

1. Add RED tests for Bean-style host ownership, malformed config/lock, managed
   Runtime contract absence, strict unowned docs, and missing/malformed pointer.
2. Implement lock-and-config-agreed consumer mode in both gate copies.
3. Put the portable common entry and self-improvement contract in the managed
   `AGENT_RUNTIME.md` template.
4. Refresh lock/registry evidence and run the focused installed-host journey.
5. Run canonical W4a and obtain fresh independent W4b on the exact product.

## Acceptance Criteria

- Source mode remains strict.
- Consumer mode is narrow, provenance-backed, and fail-closed.
- Host-owned docs remain byte-identical.
- Common Runtime rules and pointer enforcement remain active.
- All declared verification passes before any fresh Bean replay.

## Verification

- Focused continuity and consumer-host tests
- Root/package parity
- Template smoke, adoption, config, and doctor tests
- Claim, state-sync, and parallel-worktree regressions
- Runtime asset, Owner governance, sanitizer, and full test suite

## Handoff

Return exact product provenance, consumer proof requirements, source strictness,
pointer fail-closed evidence, installed-host Owner-gate result, full test
counts, W4a, and independent W4b.

## Stop Boundary

Do not weaken pointer enforcement, add a blanket host skip, edit a Bean
checkout, touch Allimbot, or perform any release/external action.
