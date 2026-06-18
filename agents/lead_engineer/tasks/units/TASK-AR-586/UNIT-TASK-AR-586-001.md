---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-586-001
work_uid: 65b910b6-9d9f-4239-9d22-eea2e3040db9
kind: unit
parent_id: TASK-AR-586
unit_id: UNIT-TASK-AR-586-001
task_id: TASK-AR-586
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Noncritical auto-release orchestrator
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: Cadence proposal is automatic but execution must be kicked off. release_council_gate passes only for criticality=noncritical with no CRITICAL_FLAGS; release_execution_gate accepts agent_council_approved as a no-Owner execution route. Compose these into one orchestrator.
inputs:
  - scripts/release_cadence_trigger.py
  - scripts/release_readiness_summary.py
  - scripts/release_council_gate.py
  - scripts/release_execution_gate.py
  - skills/release-conductor/SKILL.md (the 8-step flow)
target_files:
  - scripts/release_auto_noncritical.py
  - tests/test_release_auto_noncritical.py
scope: Decision + orchestration only; reuse existing readiness/council/execution scripts. Must refuse (exit non-zero, no mutation) when criticality is critical or any CRITICAL_FLAG is present, or when CI is not green.
acceptance:
  - Dry-run/test proves noncritical path reaches tag/push and critical path halts with owner-approval-required.
verification:
  - python -m pytest tests/test_release_auto_noncritical.py -q
handoff: Orchestrator ready; unit 2 wires it to the schedule.
stop_condition: Stop and request Owner review before enabling real tag/push if external publish (PyPI/host) blast radius is unclear.
---

# UNIT-TASK-AR-586-001 - Noncritical auto-release orchestrator

## Context

Cadence proposal is automatic but execution must be kicked off. release_council_gate passes only for criticality=noncritical with no CRITICAL_FLAGS; release_execution_gate accepts agent_council_approved as a no-Owner execution route. Compose these into one orchestrator.

## Inputs

- scripts/release_cadence_trigger.py
- scripts/release_readiness_summary.py
- scripts/release_council_gate.py
- scripts/release_execution_gate.py
- skills/release-conductor/SKILL.md (the 8-step flow)

## Target Files

- scripts/release_auto_noncritical.py
- tests/test_release_auto_noncritical.py

## Scope

Decision + orchestration only; reuse existing readiness/council/execution scripts. Must refuse (exit non-zero, no mutation) when criticality is critical or any CRITICAL_FLAG is present, or when CI is not green.

## Steps

1. Read the cadence proposal; proceed only if bump is patch/noncritical and no CRITICAL_FLAG applies.
2. Generate the readiness summary and an agent-council RELEASE-DECISION (status=agent_council_approved, approved_by=agent-release-council, W4b-independent role votes).
3. Run release_council_gate then release_execution_gate; abort on any block finding.
4. On pass: bump pyproject, tag, push; emit an Owner notification record.
5. Emit a clear 'owner-approval-required' result (no mutation) for critical/major-or-breaking.

## Acceptance Criteria

- Dry-run/test proves noncritical path reaches tag/push and critical path halts with owner-approval-required.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py -q`

## Handoff

Orchestrator ready; unit 2 wires it to the schedule.

## Stop Boundary

Stop and request Owner review before enabling real tag/push if external publish (PyPI/host) blast radius is unclear.
