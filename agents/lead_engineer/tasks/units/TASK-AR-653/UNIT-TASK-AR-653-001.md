---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-653-001
work_uid: 84a6a07d-54de-446f-967e-7571d418218d
kind: unit
parent_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
task_id: TASK-AR-653
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-31T01:50:19+09:00
started_at: 2026-07-30T23:20:37+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Implement active-aware Scribe planning, receipt, and closure semantics
horizon: unit
model_tier: worker_standard
escalation_triggers:
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-225027-task-ar-653-ar653001.json
  - agents/runtime/task_claims/CLAIM-20260730-231354-task-ar-653-ar653002.json
  - agents/runtime/task_claims/CLAIM-20260730-232037-task-ar-653-ar653003.json
  - agents/runtime/task_claims/CLAIM-20260730-234934-task-ar-653-ar653004.json
context: Runtime currently has 769 hot items and Autofolio had 272, yet both become ready after writing a ten-item projection. The Scribe skill promises mandatory archive work above 15 items, so implementation and policy disagree.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/W4B-2026-07-30-unit-task-ar-653-001-preimplementation-supersession.md
  - src/agent_runtime/state_projection.py
  - src/agent_runtime/templates/project/agents/scribe/SKILL.md
  - src/agent_runtime/templates/project/scripts/closure_gate.py
target_files:
  - src/agent_runtime/state_projection.py
  - scripts/agent_runtime/state_projection.py
  - src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py
  - src/agent_runtime/doctor.py
  - scripts/scribe_due.py
  - src/agent_runtime/templates/project/scripts/scribe_due.py
  - scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/templates/project/agents/scribe/SKILL.md
  - tests/test_scribe_due.py
  - tests/test_closure_gate.py
  - tests/test_session_continuity_hooks.py
  - tests/test_doctor.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Add deterministic planning and verification. Do not autonomously rewrite host-owned canonical state or choose meaning when records conflict.
acceptance:
  - Projection freshness alone cannot satisfy overdue closure.
  - Current work is never dropped from the bounded continuity view.
  - Canonical host state changes require an explicit bounded Scribe task.
  - Receipts are replayable without raw prompt or secret content.
verification:
  - python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q
  - python scripts/template_mirror_gate.py --check
handoff: Attach the state matrix, active-coverage negative, cleanup plan/receipt fixture, no-touch proof, template parity, and independent W4b.
stop_condition: Stop before automatically rewriting host-owned state, compressing active records, or making product/editorial decisions.
verified_at: 2026-07-31T01:50:19+09:00
verified_by: le-20260730-234934-kst-ar653004
evidence_refs:
  - reviews/VERIFY-2026-07-30-unit-task-ar-653-001-20260730235407.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731000019.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731003459.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731011752.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-653-001-20260731015019.json
---

# UNIT-TASK-AR-653-001 - Implement active-aware Scribe planning, receipt, and closure semantics

## Context

Runtime currently has 769 hot items and Autofolio had 272, yet both become ready after writing a ten-item projection. The Scribe skill promises mandatory archive work above 15 items, so implementation and policy disagree.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- reviews/W4B-2026-07-30-unit-task-ar-653-001-preimplementation-supersession.md
- src/agent_runtime/state_projection.py
- src/agent_runtime/templates/project/agents/scribe/SKILL.md
- src/agent_runtime/templates/project/scripts/closure_gate.py

## Target Files

- src/agent_runtime/state_projection.py
- scripts/agent_runtime/state_projection.py
- src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py
- src/agent_runtime/doctor.py
- scripts/scribe_due.py
- src/agent_runtime/templates/project/scripts/scribe_due.py
- scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/templates/project/agents/scribe/SKILL.md
- tests/test_scribe_due.py
- tests/test_closure_gate.py
- tests/test_session_continuity_hooks.py
- tests/test_doctor.py
- tests/test_template_smoke.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Add deterministic planning and verification. Do not autonomously rewrite host-owned canonical state or choose meaning when records conflict.

## Steps

1. Add negatives for projection-only readiness and missing active-task coverage.
2. Separate projection status, source debt, coverage, and cleanup outcome.
3. Generate bounded no-touch-aware cleanup candidates.
4. Validate cleanup receipts and post-cleanup counts.
5. Update hooks, Doctor, skill contract, and templates.

## Acceptance Criteria

- Projection freshness alone cannot satisfy overdue closure.
- Current work is never dropped from the bounded continuity view.
- Canonical host state changes require an explicit bounded Scribe task.
- Receipts are replayable without raw prompt or secret content.

## Verification

- `python -m pytest tests/test_scribe_due.py tests/test_closure_gate.py tests/test_session_continuity_hooks.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `python scripts/template_mirror_gate.py --check`

## Handoff

Attach the state matrix, active-coverage negative, cleanup plan/receipt fixture, no-touch proof, three-way portable state parity, template parity, and a fresh independent implementation W4b. The administrative supersession report is not implementation acceptance.

## Stop Boundary

Stop before automatically rewriting host-owned state, compressing active records, or making product/editorial decisions.