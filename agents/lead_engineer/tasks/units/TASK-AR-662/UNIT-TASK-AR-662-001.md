---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-662-001
work_uid: 7b798e25-dcba-4ec4-b2e7-be85c9b62973
kind: unit
parent_id: TASK-AR-662
unit_id: UNIT-TASK-AR-662-001
task_id: TASK-AR-662
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Re-attest integrated Scribe behavior under collision-free authority
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: The V080 Scribe task completed with final independent approval, but its task/unit files were overwritten by an earlier canonical TASK-AR-653 during merge. Its implementation, reviews, claims, and commit history remain on main.
inputs:
  - reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
  - reviews/W4B-2026-07-31-unit-task-ar-653-001-invalid-runtime-config-final.md
  - agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
  - src/agent_runtime/state_projection.py
  - scripts/scribe_due.py
target_files:
  - tests/test_scribe_due.py
  - tests/test_closure_gate.py
  - tests/test_session_continuity_hooks.py
  - tests/test_doctor.py
  - tests/test_template_smoke.py
scope: Re-attestation first. Change implementation only when a current reproducible failure is found and record any expansion through T3 before editing.
acceptance:
  - Historical approval is context, never substituted for fresh W4b.
  - Active work cannot disappear from the bounded continuity view.
  - Projection freshness alone cannot clear overdue source debt.
  - No consumer project is mutated.
verification:
  - PYTHONPATH=src python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q
  - PYTHONPATH=src python scripts/scribe_due.py --root . --json
handoff: Attach collision-map proof, historical blob immutability, complete current suite evidence, any T3 repair, W4a, and fresh independent W4b.
stop_condition: Stop before rewriting historical artifacts, performing archive mutations without an explicit bounded Scribe decision, mutating consumers, external CI, push, tag, publish, or deploy.
depends_on:
  - TASK-AR-661
---

# UNIT-TASK-AR-662-001 - Re-attest integrated Scribe behavior under collision-free authority

## Context

The V080 Scribe task completed with final independent approval, but its task/unit files were overwritten by an earlier canonical TASK-AR-653 during merge. Its implementation, reviews, claims, and commit history remain on main.

## Inputs

- reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
- reviews/W4B-2026-07-31-unit-task-ar-653-001-invalid-runtime-config-final.md
- agents/project/work-items/WORK-IDENTITY-RECOVERIES.json
- src/agent_runtime/state_projection.py
- scripts/scribe_due.py

## Target Files

- tests/test_scribe_due.py
- tests/test_closure_gate.py
- tests/test_session_continuity_hooks.py
- tests/test_doctor.py
- tests/test_template_smoke.py

## Scope

Re-attestation first. Change implementation only when a current reproducible failure is found and record any expansion through T3 before editing.

## Steps

1. Claim the new task/unit normally and prove its recovery mapping resolves every old claim digest without resolving through the current TASK-AR-653 unit.
2. Run the full registered Scribe suite and command-level state projection checks on current main.
3. If red, register a T3 scope amendment and repair RED-first; otherwise keep the implementation tree unchanged.
4. Create fresh verification evidence, W4a, and independent W4b bound to TASK-AR-662.

## Acceptance Criteria

- Historical approval is context, never substituted for fresh W4b.
- Active work cannot disappear from the bounded continuity view.
- Projection freshness alone cannot clear overdue source debt.
- No consumer project is mutated.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `PYTHONPATH=src python scripts/scribe_due.py --root . --json`

## Handoff

Attach collision-map proof, historical blob immutability, complete current suite evidence, any T3 repair, W4a, and fresh independent W4b.

## Stop Boundary

Stop before rewriting historical artifacts, performing archive mutations without an explicit bounded Scribe decision, mutating consumers, external CI, push, tag, publish, or deploy.
