---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-661-001
work_uid: 8cd0295b-2371-4f08-9f3d-9563a4ad78b4
kind: unit
parent_id: TASK-AR-661
unit_id: UNIT-TASK-AR-661-001
task_id: TASK-AR-661
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Require provenance and exact-SHA attestation in the merge queue
horizon: unit
model_tier: worker_standard
depends_on:
  - UNIT-TASK-AR-658-001
  - UNIT-TASK-AR-659-001
  - UNIT-TASK-AR-660-001
escalation_triggers:
context: A strong local queue remains bypassable when remote branch policy is permissive or when an attestation is not cryptographically tied to the exact candidate and base.
inputs:
  - scripts/merge_queue.py
  - new:scripts/merge_queue_policy.py
  - new:scripts/session_scm_guard.py
  - .github/workflows
  - reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
target_files:
  - scripts/merge_queue.py
  - new:scripts/merge_queue_policy.py
  - new:scripts/remote_gate_attestation.py
  - new:scripts/gate_governance.py
  - new:.github/workflows/merge-queue.yml
  - tests/test_merge_queue.py
  - new:tests/test_merge_queue_policy.py
  - new:tests/test_remote_gate_attestation.py
  - new:tests/test_gate_governance.py
  - new:docs/integration-authority.md
scope: Add integration-role authorization, commit-chain provenance, latest-base revalidation, exact-SHA attestation, and protected gate governance. Do not weaken existing local checks.
acceptance:
  - A passing attestation cannot be replayed for another commit.
  - A candidate whose HEAD changes during verification is rejected.
  - Direct worker integration is denied.
  - Gate self-weakening cannot authorize itself.
verification:
  - python -m pytest -q tests/test_merge_queue.py tests/test_merge_queue_policy.py tests/test_remote_gate_attestation.py tests/test_gate_governance.py
  - python scripts/merge_queue_policy.py --check
handoff: Provide attestation schema, replay/tamper fixtures, branch-policy evidence, and a protected update trace.
stop_condition: Stop before modifying a live remote policy without explicit owner authorization.
---

# UNIT-TASK-AR-661-001 - Require provenance and exact-SHA attestation in the merge queue

## Context

A strong local queue remains bypassable when remote branch policy is permissive or when an attestation is not cryptographically tied to the exact candidate and base.

## Inputs

- scripts/merge_queue.py
- new:scripts/merge_queue_policy.py
- new:scripts/session_scm_guard.py
- .github/workflows
- reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md

## Target Files

- scripts/merge_queue.py
- new:scripts/merge_queue_policy.py
- new:scripts/remote_gate_attestation.py
- new:scripts/gate_governance.py
- new:.github/workflows/merge-queue.yml
- tests/test_merge_queue.py
- new:tests/test_merge_queue_policy.py
- new:tests/test_remote_gate_attestation.py
- new:tests/test_gate_governance.py
- new:docs/integration-authority.md

## Scope

Add integration-role authorization, commit-chain provenance, latest-base revalidation, exact-SHA attestation, and protected gate governance. Do not weaken existing local checks.

## Steps

1. Reject candidates with foreign, unattributed, or stale-fence commits.
2. Revalidate dependency, scope, lease release, and actual footprint at queue time.
3. Seal gate input and output to base SHA, candidate SHA, run, task, and gate bundle version.
4. Configure required remote check consumption and expected-old-SHA protected update.
5. Use protected-base policy when the candidate modifies a gate or baseline.

## Acceptance Criteria

- A passing attestation cannot be replayed for another commit.
- A candidate whose HEAD changes during verification is rejected.
- Direct worker integration is denied.
- Gate self-weakening cannot authorize itself.

## Verification

- `python -m pytest -q tests/test_merge_queue.py tests/test_merge_queue_policy.py tests/test_remote_gate_attestation.py tests/test_gate_governance.py`
- `python scripts/merge_queue_policy.py --check`

## Handoff

Provide attestation schema, replay/tamper fixtures, branch-policy evidence, and a protected update trace.

## Stop Boundary

Stop before modifying a live remote policy without explicit owner authorization.
