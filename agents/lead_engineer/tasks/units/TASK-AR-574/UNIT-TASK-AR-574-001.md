---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-574-001
work_uid: 40aff03e-3aec-471f-b27c-ecde6358a3a1
kind: unit
parent_id: TASK-AR-574
unit_id: UNIT-TASK-AR-574-001
task_id: TASK-AR-574
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T17:15:00+09:00
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Create monitored-role evidence packet
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The current maturity blockers include five monitored role gaps. This unit should route those roles through real governance records rather than changing thresholds.
inputs:
  - reviews/REPORT-2026-06-17-self-improvement-maturity.md
  - scripts/collaboration_governance_gate.py
  - agents/project/MULTIPANE-PROCESS-POLICY.yml
target_files:
  - reviews
  - agents/runtime/task_claims
  - agents/project/MULTIPANE-PROCESS-POLICY.yml
  - reviews/INDEX.md
scope: Create evidence for monitored roles using existing records and gates. Do not invent live dialogue or bypass role-monitor findings.
acceptance:
  - Role evidence is traceable to claim, review, council, or policy records.
  - The role_gaps metric decreases or a blocker review explains why it cannot.
  - The next cycle report can compare before/after role_gaps.
verification:
  - python scripts/collaboration_governance_gate.py --check
  - python scripts/self_improvement_cycle.py assess
  - python scripts/evidence_index_generator.py --check
handoff: List each monitored role and its evidence path or blocker.
stop_condition: Stop after the role gap state is measurable and indexed.
---

# UNIT-TASK-AR-574-001 - Create monitored-role evidence packet

## Context

The current maturity blockers include five monitored role gaps. This unit should route those roles through real governance records rather than changing thresholds.

## Inputs

- reviews/REPORT-2026-06-17-self-improvement-maturity.md
- scripts/collaboration_governance_gate.py
- agents/project/MULTIPANE-PROCESS-POLICY.yml

## Target Files

- reviews
- agents/runtime/task_claims
- agents/project/MULTIPANE-PROCESS-POLICY.yml
- reviews/INDEX.md

## Scope

Create evidence for monitored roles using existing records and gates. Do not invent live dialogue or bypass role-monitor findings.

## Steps

1. Read the collaboration gate role-monitor logic and current policy.
2. Create review/council evidence that assigns or records the monitored roles honestly.
3. Run the gate and document remaining monitored role gaps.
4. Index the evidence.

## Acceptance Criteria

- Role evidence is traceable to claim, review, council, or policy records.
- The role_gaps metric decreases or a blocker review explains why it cannot.
- The next cycle report can compare before/after role_gaps.

## Verification

- `python scripts/collaboration_governance_gate.py --check`
- `python scripts/self_improvement_cycle.py assess`
- `python scripts/evidence_index_generator.py --check`

## Handoff

List each monitored role and its evidence path or blocker.

## Stop Boundary

Stop after the role gap state is measurable and indexed.
