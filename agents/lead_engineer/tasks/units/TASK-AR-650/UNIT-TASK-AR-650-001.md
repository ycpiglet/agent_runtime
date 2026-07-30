---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-650-001
work_uid: 181ee6f3-421b-4508-80ef-f80c7befa641
kind: unit
parent_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_id: TASK-AR-650
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-083649-task-ar-650-ar650001.json
evidence_refs:
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080-GREEN-ATTEMPT-3.md
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/W4A-2026-07-30-unit-task-ar-650-001.md
  - reviews/W4B-2026-07-30-unit-task-ar-650-001.md
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-30T12:10:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Execute and document the Autofolio migration rehearsal
horizon: unit
model_tier: planner_high
escalation_triggers:
  - ambiguity
  - data_integrity
  - cross_cutting
risk_tier: high
context: Autofolio is pinned to v0.6.0 and uses the right framework/overlay/seam design. Its exact config carries 20, not 21, unmanaged entries. Bean Wiki attempt 6 and Allimbot attempt 1 are independently green. Autofolio attempt 1 proved exact Runtime product 4929415d is not an RC because its Owner, continuity, taskset, wave, and hook contracts regress the downstream host. Attempt 2 proved c110e6df repairs those paths but is still not an RC because direct task_claim bypasses the shared T0/readiness preflight. Both red attempts are immutable evidence; attempt 3 must use the newly committed direct-claim repair and entirely new product, target, and control worktrees.
inputs:
  - reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t4-replan.md
  - reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t3-replan.md
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-1.md
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-2.md
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-6.md
  - reviews/PILOT-ALLIMBOT-v080-GREEN-ATTEMPT-1.md
  - docs/configuration-v2.md
  - docs/pilot-acceptance-contract.md
  - docs/pilot-isolation-contract.md
  - agent-runtime-red-product@4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2
  - agent-runtime-red-product@c110e6df355b960a3c32bd8187eb792b26c8f18f
  - agent-runtime-lifecycle@dd741b23
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71:agent_runtime.yml
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71:docs/AGENT_RUNTIME_INTEGRATION.md
  - autofolio@ca88433cf155fd03d616584fda7ed4aa3d33fd71:docs/agent_runtime_feedback.md
target_files:
  - scripts/work.py
  - scripts/status_alias.py
  - scripts/parallel_worktree_gate.py
  - scripts/task_claim_dispatcher.py
  - scripts/taskset_dispatcher.py
  - scripts/wave_dispatcher.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py
  - src/agent_runtime/templates/project/scripts/status_alias.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
  - src/agent_runtime/templates/project/scripts/wave_dispatcher.py
  - src/agent_runtime/templates/project/scripts/work.py
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - tests/test_work_registration.py
  - tests/test_status_alias.py
  - tests/test_parallel_worktree_gate.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_taskset_dispatcher.py
  - tests/test_wave_dispatcher.py
  - tests/test_doctor.py
  - tests/test_owner_governance_consumer_host.py
  - tests/host_contracts
  - scripts/pilot_acceptance.py
  - tests/test_pilot_acceptance.py
  - tests/host_contracts/test_autofolio_task_claim_dispatcher.py
  - new:tests/fixtures/pilots/autofolio/evidence-green-attempt-3.json
  - new:tests/fixtures/pilots/autofolio/isolation-green-attempt-3.json
  - new:tests/fixtures/pilots/autofolio/seam-ledger-green-attempt-3.json
  - new:tests/fixtures/pilots/contracts/autofolio-v080-green-attempt-3.json
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-1.md
  - reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-2.md
  - new:reviews/PILOT-AUTOFOLIO-MIGRATION-v080-GREEN-ATTEMPT-3.md
  - new:reviews/W4A-2026-07-30-unit-task-ar-650-001.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-650-001.md
  - reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t3-replan.md
  - reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t4-replan.md
  - agents/lead_engineer/tasks/TASK-AR-650.md
  - agents/lead_engineer/tasks/TASK-AR-651.md
  - agents/lead_engineer/tasks/units/TASK-AR-650/UNIT-TASK-AR-650-001.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/TASKSET-DEFINITIONS.json
scope: First preserve work-registration task order in the canonical taskset registry and prove the current lane selects TASK-AR-650 before TASK-AR-651. Preserve exact Runtime 4929415d attempt 1 and c110e6df attempt 2 as red evidence, promote the direct-claim T0/readiness contract into Runtime, and pin a new clean repair candidate. Then, from an entirely fresh attempt-3 target and same-commit control at Autofolio ca88433c, migrate v0.6 config/lock/ownership to that candidate's full-runtime profile, classify every one of the 20 legacy unmanaged paths, and apply only safe Runtime updates. Protect all product, trading, broker, credential, migration, dependency, database, workflow, and deploy surfaces. Do not implement or alter investment-product behavior.
acceptance:
  - Work registration persists exact ordered task membership; old registry rows remain readable; invalid membership fails closed; the live taskset selects TASK-AR-650 and TASK-AR-651 depends on it.
  - Work registration preserves declared task dependencies into worker units and rejects missing, invalid, duplicate, self, and cyclic dependencies before writes.
  - Attempts 1 and 2 remain pinned respectively to exact Runtime 4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2 and c110e6df355b960a3c32bd8187eb792b26c8f18f as red evidence; attempt 3 is pinned to a later exact clean repair candidate and its product, template, and scripts trees. All product checkouts stay clean.
  - Target and control start at Autofolio ca88433cf155fd03d616584fda7ed4aa3d33fd71. The control never changes and primary drift is observation-only.
  - The exact v0.6 source contains 20 unmanaged paths. Every path has one evidenced managed, seed_once, host_owned, generated, or temporary_conflict disposition; no stale 21-path claim remains.
  - V2 full-runtime selection, host context, role/state/risk overlays, ownership manifest, safe apply, lock v2, doctor, and two reconciles complete with zero conflicts.
  - At least one temporary downstream repair returns to managed Runtime. No reduction claim is based only on renaming unmanaged to host_owned.
  - A second plan/apply is idempotent and the clean-commit migration is reproducible.
  - Protected app, web, Supabase, database, dependency, trading, credential, workflow, and deployment inventories and bytes retain matching before/after digests.
  - Compound and Scribe use task-linked/generated state, preserve legacy compound/status sources, and restart/continuity evidence remains local.
  - No-install host tests and Runtime migration, adoption, sync, isolation, and exact acceptance tests pass.
  - Publish, deploy, migration, origin push, consumer commit, credential read/change, network/provider call, notification, broker call, order, package install, and product mutation counters are integer zero.
  - Canonical W4a and fresh independent W4b pass with no Runtime P0/P1 before TASK-AR-651.
verification:
  - python scripts/pilot_isolation_gate.py --evidence tests/fixtures/pilots/autofolio/isolation-green-attempt-3.json --check --json
  - python scripts/pilot_acceptance.py --host autofolio --fixture tests/fixtures/pilots/autofolio/evidence-green-attempt-3.json --check --json
  - python -m pytest tests/test_work_registration.py tests/test_taskset_dispatcher.py tests/test_pilot_acceptance.py tests/test_pilot_isolation_gate.py -q
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/runtime_asset_usage.py --check
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
handoff: Attach exact Runtime/Autofolio provenance, taskset-order failing-before/passing-after proof, primary/target/control snapshots, all-20 seam ledger, migration/config/lock diff, ownership and safe-apply counts, idempotence proof, protected-product preservation, host tests, raw/portable isolation digests, exact acceptance identity, integer-zero effects, rollback, W4a, and independent W4b.
stop_condition: Stop on any plan drift, wrong task selection, primary/control/product write, unclassified seam, silent overwrite, conflict, protected product mutation, consumer commit, install, credential read/change, KIS/broker/order call, database migration, network/provider call, notification, deploy, release, version, tag, package, push, or publication action.
---

# UNIT-TASK-AR-650-001 - Execute and document the Autofolio migration rehearsal

## Context

Autofolio is pinned to v0.6.0 and uses the right framework/overlay/seam
design. Its exact pinned configuration carries 20 unmanaged entries, not the
stale registration count of 21. Bean Wiki and Allimbot are independently
green. Autofolio attempts 1 and 2 are immutable RED evidence. Attempt 1
exposed Owner, continuity, taskset, wave, and hook regressions. Attempt 2
showed those repairs work but exposed a direct-claim T0/readiness bypass.
Attempt 3 must use a newly committed Runtime repair and new target, control,
and product worktrees.

## Inputs

- Exact RED Runtime products `4929415d` and `c110e6df`
- Clean Runtime repair candidate produced from the attempt-2 direct-claim failure
- Runtime lifecycle baseline `dd741b23`
- Clean Autofolio baseline `ca88433cf155fd03d616584fda7ed4aa3d33fd71`
- T4 replan, v2 configuration contract, and completed Bean/Allimbot evidence

## Target Files

- Runtime order-preservation implementation and regression tests
- Runtime-only Autofolio seam ledger, evidence, isolation, exact contract,
  report, W4a, and W4b
- Disposable target Runtime projection and bounded local evidence only

## Scope

Preserve canonical taskset order, then create a clean target and frozen control
from the exact Autofolio commit. Rehearse config, ownership, lock, and safe
sync migration only in the target. Never copy the live primary's uncommitted
work and never mutate product or trading behavior.

## Steps

1. Persist registration order, prove failing-before/passing-after dispatch, and
   re-anchor/claim without bypass.
2. Create exact target/control/product checkouts and capture isolation before
   target writes.
3. Snapshot all 20 v0.6 unmanaged paths and protected product surfaces.
4. Preserve attempts 1 and 2 as red evidence, repair the shared direct-claim
   preflight contract, and pin a clean candidate without reusing either red
   target.
5. Generate v0.8 full-runtime config, ownership, host context, risk/state
   overlays, migration, and reconcile plans in a fresh attempt-3 target.
6. Apply only safe Runtime updates, write lock v2, and run a second idempotent
   reconcile/apply.
7. Run no-install host and Runtime verification, exact isolation/acceptance,
   W4a, and fresh independent W4b.

## Acceptance Criteria

- Registered task order is durable and 650 precedes 651.
- Registered task dependencies survive into worker units and invalid dependency graphs fail before writes.
- Migration is deterministic, conflict-free, and idempotent.
- Live host data and product/risk surfaces retain explicit ownership and exact
  before/after digests.
- Every one of the 20 old seams has one reasoned disposition and actual
  temporary forks decrease.
- Host tests and exact acceptance remain green without install or external
  effects.

## Verification

- Exact-product isolation and strict Autofolio acceptance
- Work registration/taskset-order regressions
- Runtime adoption/config/sync/template regressions
- Read-only Autofolio host tests with existing dependencies

## Handoff

Return exact provenance and snapshots, order regression proof, all-20 seam
ledger, migration/config/lock diff, ownership/apply counts, idempotence,
protected-product preservation, host tests, raw/portable evidence digests,
exact contract identity, zero-effect counters, rollback, W4a, and W4b.

## Stop Boundary

Stop before any primary/control/product mutation, unclassified seam, silent
overwrite, consumer commit, credential access, KIS/broker/order call, database
migration, install, network/provider/notification action, deploy, release,
version, tag, package, push, or publication.
