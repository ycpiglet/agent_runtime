---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-662
display_id: TASK-AR-662
task_uid: 29cd97fe-92b2-4a40-a736-faf840d0354d
work_id: TASK-AR-662
work_uid: 29cd97fe-92b2-4a40-a736-faf840d0354d
kind: task
parent_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
registered_at: 2026-07-30T11:25:17+09:00
created_at: 2026-07-30T11:25:17+09:00
updated_at: 2026-07-30T11:25:17+09:00
title: Strengthen semantic verification and baseline governance
status: planned
priority: P1
difficulty: L
est_hours: 18
est_tokens: 37000
owner: lead-engineer
team: evaluation-office
initiative_id: INIT-AR-AUTONOMOUS-EXECUTION-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-AUTONOMOUS-EXECUTION-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-662/UNIT-TASK-AR-662-001.md
reservation_id: RES-20260730-112517-91ed5cf4-08
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-parallel-goal-session-failure-audit.md
created_by: codex-root-session-isolation-planner
summary: Prevent mechanically green integration from restoring old designs, mixing incompatible implementations, or laundering regressions into new baselines.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
tags:
  - work-cli-created
acceptance:
  - Critical user journeys have semantic assertions independent of snapshots.
  - Design-system ownership and shared component contracts are checked across parallel branches.
  - Baseline updates require separate justification, before/after evidence, and non-author independence.
  - Verifier identity and tool evidence are bound to the candidate SHA.
  - A green unit suite cannot override a failed journey, accessibility, or protected design contract.
verification:
  - python -m pytest -q tests/test_semantic_integration_gate.py tests/test_baseline_governance.py tests/test_verifier_attestation.py
  - python scripts/owner_governance_gate.py
---

# TASK-AR-662 - Strengthen semantic verification and baseline governance

## Goal

- Prevent mechanically green integration from restoring old designs, mixing incompatible implementations, or laundering regressions into new baselines.

## Scope

- Add contract, journey, responsive, accessibility, visual, and verifier-attestation requirements plus independent ownership for baseline and gate changes.

## Acceptance Criteria

- Critical user journeys have semantic assertions independent of snapshots.
- Design-system ownership and shared component contracts are checked across parallel branches.
- Baseline updates require separate justification, before/after evidence, and non-author independence.
- Verifier identity and tool evidence are bound to the candidate SHA.
- A green unit suite cannot override a failed journey, accessibility, or protected design contract.

## Verification

- `python -m pytest -q tests/test_semantic_integration_gate.py tests/test_baseline_governance.py tests/test_verifier_attestation.py`
- `python scripts/owner_governance_gate.py`
