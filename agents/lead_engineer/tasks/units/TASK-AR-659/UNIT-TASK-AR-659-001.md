---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-659-001
work_uid: 4eac3cc2-e0b7-4e0d-80d2-c0e3102053ff
kind: unit
parent_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
task_id: TASK-AR-659
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: done
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260803-143123-task-ar-659-cfc8.json
verification_status: passed
completed_at: 2026-08-03T16:38:00+09:00
resolution: done
w4b_acceptance: true
w4b_ref: reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md
owner: lead-engineer
created_at: 2026-08-03T14:21:57+09:00
updated_at: 2026-08-03T16:09:06+09:00
origin_type: defect
origin_ref: reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
created_by: owner-manual-recovery
summary: Implement owner-bound legacy claim bootstrap, rotation, and terminalization RED-first
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - repeated_failure
context: A claim that expires while missing mutation_revision/scope_binding is unreachable by every registered command, and claim_reaper skips orchestrator-mode claims before it ever tests liveness. On 2026-08-03 this deadlocked TASK-AR-655 against its own task set and required an Owner-authorized manual JSON mutation to clear. This is the 4th recurrence in the claim-authority defect family.
inputs:
  - reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
  - reviews/W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
  - scripts/claim_reaper.py
  - scripts/task_claim_dispatcher.py
  - scripts/claim_lease.py
target_files:
  - scripts/claim_lease.py
  - src/agent_runtime/templates/project/scripts/claim_lease.py
  - scripts/claim_reaper.py
  - src/agent_runtime/templates/project/scripts/claim_reaper.py
  - scripts/task_claim_dispatcher.py
  - src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
  - tests/test_claim_lease.py
  - tests/test_claim_reaper.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_claim_store.py
  - scripts/deadlock_watchdog.py
  - src/agent_runtime/templates/project/scripts/deadlock_watchdog.py
  - scripts/claim_reaper_hook.py
  - src/agent_runtime/templates/project/scripts/claim_reaper_hook.py
scope: Local claim-store authority only. Do not introduce a network or distributed lease dependency, do not add a claim-release or acceptance path, and do not touch consumer projects.
acceptance:
  - A pre-mutation-field claim is adoptable by an owner-bound command; the same command refuses an unidentified caller.
  - An expired claim is terminalizable regardless of mode, and a live claim is never terminalizable.
  - claim_reaper classifies orchestrator claims by status and liveness rather than skipping on mode.
  - Every mutation records owner identity, before/after digest, and reason.
  - No new command grants release, acceptance, or external-release authority.
  - A new worktree can activate its claim store through a registered command without a consumer agent_runtime.yml.
verification:
  - PYTHONPATH=src python -m pytest tests/test_claim_reaper.py tests/test_claim_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py -q
  - PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q
  - python scripts/template_mirror_gate.py --check
  - python scripts/rbac_write_gate.py --check
handoff: Attach the RED commits, the owner-identity refusal proof, the live-claim refusal proof, before/after digests, the template mirror diff, the Compound record, and an independent W4b.
stop_condition: Stop before introducing a network lease dependency, auto-committing host state, recovering a claim without owner identity, mutating unregistered consumers, dispatching CI, or performing version, tag, push, publish, deploy, claim-release, or external-release actions.
verified_at: 2026-08-03T16:09:06+09:00
verified_by: le-20260803-143123-kst-cfc8
evidence_refs:
  - reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803150038.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803150906.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803153038.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803155106.json
  - reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803160906.json
---

# UNIT-TASK-AR-659-001 - Implement owner-bound legacy claim bootstrap, rotation, and terminalization RED-first

## Context

A claim that expires while missing `mutation_revision` / `scope_binding` is
unreachable by every registered command, and `claim_reaper` skips
orchestrator-mode claims before it ever tests liveness. On 2026-08-03 this
deadlocked TASK-AR-655 against its own task set and required an
Owner-authorized manual JSON mutation to clear. This is the 4th recurrence in
the claim-authority defect family.

## Inputs

- reviews/RECOVERY-2026-08-03-task-ar-655-owner-claim-terminalize.md
- reviews/W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
- scripts/claim_reaper.py
- scripts/task_claim_dispatcher.py
- scripts/claim_lease.py

## Target Files

- scripts/claim_lease.py
- src/agent_runtime/templates/project/scripts/claim_lease.py
- scripts/claim_reaper.py
- src/agent_runtime/templates/project/scripts/claim_reaper.py
- scripts/task_claim_dispatcher.py
- src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py
- tests/test_claim_lease.py
- tests/test_claim_reaper.py
- tests/test_task_claim_dispatcher.py
- tests/test_claim_store.py
- scripts/deadlock_watchdog.py (scope amendment, W4b P2)
- src/agent_runtime/templates/project/scripts/deadlock_watchdog.py
- scripts/claim_reaper_hook.py (scope amendment, W4b P2)
- src/agent_runtime/templates/project/scripts/claim_reaper_hook.py

## Scope

Local claim-store authority only. Do not introduce a network or distributed
lease dependency, do not add a claim-release or acceptance path, and do not
touch consumer projects.

## Steps

1. RED: a pre-mutation-field claim cannot be adopted by any registered command.
2. RED: an expired orchestrator-mode claim is never a reap candidate.
3. RED: no registered command terminalizes an unreachable expired claim.
4. RED: a recovery attempt without owner identity must be refused.
5. RED: a recovery attempt against a live claim must be refused.
6. RED: a freshly created worktree has an unusable claim store and no registered activation command in this repository.
7. Implement owner-bound bootstrap (adopt), rotate, and terminalize.
8. Replace the reaper's mode short-circuit with status/liveness classification.
9. Expose claim-store checkout activation without requiring a consumer `agent_runtime.yml`.
10. Mirror the surface into the runtime template and regenerate the host lock.
11. Record the Compound for the 4x-recurring defect family.

## Acceptance Criteria

- A pre-mutation-field claim is adoptable by an owner-bound command; the same command refuses an unidentified caller.
- An expired claim is terminalizable regardless of mode, and a live claim is never terminalizable.
- `claim_reaper` classifies orchestrator claims by status and liveness rather than skipping on mode.
- Every mutation records owner identity, before/after digest, and reason.
- No new command grants release, acceptance, or external-release authority.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_claim_reaper.py tests/test_claim_store.py tests/test_claim_lease.py tests/test_task_claim_dispatcher.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/rbac_write_gate.py --check`

### Environment (mandatory)

`PYTHONPATH=src` is required. The editable install resolves `agent_runtime`
to `.worktrees/TASK-AR-655/src`, so an unqualified `pytest` run in this
worktree silently exercises **another worktree's source**.

### Pre-existing baseline (deliberately excluded from `verification:`)

`tests/test_claim_guard.py` is **21 failed / 15 passed** on this clone's
`main`, verified in a throwaway detached worktree. It predates TASK-AR-655
and this unit: the blocking rule `task-claim:authorized-commit-not-persisted`
was introduced by TASK-AR-648 (commit `31b1a146`, already on `main`).

It is **not** listed under `verification:` because a unit must not claim a
verification command it cannot pass and does not own — that would either
block this unit forever or normalise a red bar. It is instead a standing
side-check: run
`PYTHONPATH=src python -m pytest tests/test_claim_guard.py -q`
and confirm the count has not worsened beyond 21 failed / 15 passed. This
unit's changes leave it at exactly that baseline.

## Handoff

Attach the RED commits, the owner-identity refusal proof, the live-claim
refusal proof, before/after digests, the template mirror diff, the Compound
record, and an independent W4b.

## Stop Boundary

Stop before introducing a network lease dependency, auto-committing host state,
recovering a claim without owner identity, mutating unregistered consumers,
dispatching CI, or performing version, tag, push, publish, deploy,
claim-release, or external-release actions.