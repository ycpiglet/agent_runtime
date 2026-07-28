---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-642-001
work_uid: e1da24f8-f250-43ba-af58-76a841827a80
kind: unit
parent_id: TASK-AR-642
unit_id: UNIT-TASK-AR-642-001
task_id: TASK-AR-642
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T23:17:35+09:00
started_at: 2026-07-28T22:14:34+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Implement ownership manifest and sync reconcile
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: At main eecb0dc4, sync and lock consume exact v1 unmanaged paths only while config v2 already projects four ownership modes. Autofolio v0.6 carries 20 unmanaged seams, and one conflict causes legacy apply to perform zero updates. Consumer repositories remain read-only.
inputs:
  - src/agent_runtime/sync.py
  - src/agent_runtime/lock.py
  - src/agent_runtime/config.py
  - src/agent_runtime/host_update.py
  - reviews/REVIEW-2026-07-28-task-ar-642-w0-t3-replan.md
target_files:
  - src/agent_runtime/sync.py
  - src/agent_runtime/lock.py
  - src/agent_runtime/cli.py
  - src/agent_runtime/host_update.py
  - src/agent_runtime/config.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Classify the current packaged template by effective ownership, add deterministic read-only reconcile text/JSON, add opt-in safe-only application, write/read lock v2 with seed completion, and keep exact-ref host update authoritative. Do not auto-merge host edits.
acceptance:
  - No host-owned or generated file enters an apply set.
  - Seed-once paths are created only without prior installation evidence and are never recreated after seed completion.
  - Safe-only apply is opt-in, can update safe managed paths while conflicts remain, reports those conflicts, and returns nonzero.
  - Legacy apply remains all-or-nothing and v1 unmanaged/lock inputs remain readable.
  - Reconcile JSON is deterministic and names ownership, action, reason, safety, lock migration, and configured pinned source.
  - Exact-ref host update compares with the isolated pinned installation; ambient package_version never selects the source.
  - No silent overwrite path is introduced.
verification:
  - python -m pytest tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
  - python -m pytest -q
handoff: Provide transition-matrix evidence, an Autofolio-shaped v1 migration fixture, deterministic reconcile/lock output, mixed safe/conflict apply evidence, and pinned-source host-update evidence.
stop_condition: Stop before automatic three-way merges, profile-specific file manifests, dependency closure, pilot mutation, claim-lifecycle fixes, or UI work.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260728-221434-task-ar-642-642001.json
verified_at: 2026-07-28T23:15:13+09:00
verified_by: codex-root-v080-w6
evidence_refs:
  - reviews/VERIFY-2026-07-28-unit-task-ar-642-001-20260728231513.json
  - reviews/W4B-2026-07-28-unit-task-ar-642-001-approved.md
resolution: done
completed_at: 2026-07-28T23:17:35+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: Work included ownership-mode implementation, two adversarial W4b repair rounds, apply-time boundary hardening, deterministic lock v2 migration, local and Python 3.10-3.12 matrix CI, claim release, PR integration, and lifecycle reconciliation before reliable per-unit time and token metering was available.
---

# UNIT-TASK-AR-642-001 - Implement ownership manifest and sync reconcile

## Context

At Agent Runtime `main` `eecb0dc4`, sync and lock consume exact v1
`sync.unmanaged` paths only while config v2 already projects `managed`,
`seed_once`, `host_owned`, and `generated`. Autofolio v0.6 carries 20
unmanaged seams, and one conflict causes legacy apply to perform zero updates.
Consumer repositories remain read-only.

## Inputs

- src/agent_runtime/sync.py
- src/agent_runtime/lock.py
- src/agent_runtime/config.py
- src/agent_runtime/host_update.py
- reviews/REVIEW-2026-07-28-task-ar-642-w0-t3-replan.md

## Target Files

- src/agent_runtime/sync.py
- src/agent_runtime/lock.py
- src/agent_runtime/cli.py
- src/agent_runtime/host_update.py
- src/agent_runtime/config.py
- tests/test_inventory_sync_sanitize.py
- tests/test_template_smoke.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Classify the current packaged template by effective ownership, add
deterministic read-only reconcile text/JSON, add opt-in safe-only application,
write/read lock v2 with seed completion, and keep exact-ref host update
authoritative. Do not auto-merge host edits.

## Steps

1. Build the effective manifest from the current packaged template and
   ownership config; report profiles without inventing profile file sets.
2. Separate managed updates, first-time seeds, preserved host-owned paths,
   producer-owned generated paths, and conflicts.
3. Add deterministic reconcile text/JSON and an explicit safe-only apply mode
   while preserving legacy apply semantics.
4. Read v1 locks and write deterministic v2 ownership/seed evidence.
5. Make exact-ref host update expose reconcile and use the isolated pinned
   installation for comparison.

## Acceptance Criteria

- No host-owned or generated file enters an apply set.
- Seed-once paths are created only without prior installation evidence and are
  never recreated after seed completion.
- Safe-only apply can update safe managed paths while conflicts remain,
  reports those conflicts, and returns nonzero.
- Legacy apply remains all-or-nothing and v1 unmanaged/lock inputs remain
  readable.
- Reconcile JSON is deterministic and names ownership, action, reason, safety,
  lock migration, and configured pinned source.
- Exact-ref host update compares with the isolated pinned installation;
  ambient `package_version` never selects the source.
- No silent overwrite path is introduced.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q`
- `python -m pytest -q`

## Handoff

Provide ownership transition-matrix evidence, an Autofolio-shaped v1 migration
fixture, deterministic reconcile/lock output, mixed safe/conflict apply
evidence, and pinned-source host-update evidence.

## Stop Boundary

Stop before automatic three-way merges, profile-specific file manifests,
dependency closure, pilot mutation, claim-lifecycle fixes, or UI work.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T23:17:35+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Work included ownership-mode implementation, two adversarial W4b repair rounds, apply-time boundary hardening, deterministic lock v2 migration, local and Python 3.10-3.12 matrix CI, claim release, PR integration, and lifecycle reconciliation before reliable per-unit time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-28-unit-task-ar-642-001-20260728231513.json`
  - `reviews/W4B-2026-07-28-unit-task-ar-642-001-approved.md`
<!-- work-close:end -->
