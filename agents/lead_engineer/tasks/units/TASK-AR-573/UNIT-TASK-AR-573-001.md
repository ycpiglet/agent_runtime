---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-573-001
work_uid: acc67c07-5956-4cd5-bbbd-c25ccf7964db
kind: unit
parent_id: TASK-AR-573
unit_id: UNIT-TASK-AR-573-001
task_id: TASK-AR-573
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T17:26:02+09:00
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Prove scribe usage before waiver burn-down
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The maturity report shows scribe_state unknown and waiver_debt 1. This unit should create real evidence rather than editing metrics directly.
inputs:
  - reviews/REPORT-2026-06-17-self-improvement-maturity.md
  - agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json
  - scripts/collaboration_governance_gate.py
target_files:
  - agents/runtime/task_claims
  - agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json
  - scripts/collaboration_governance_gate.py
  - reviews/INDEX.md
scope: Create or route real scribe evidence through the existing lifecycle. Avoid synthetic evidence and do not weaken the governance gate.
acceptance:
  - The scribe debt is measurably reduced or a concrete blocker is recorded.
  - No waiver is removed without a passing gate or explicit review decision.
  - The evidence survives git clean/reset because it is committed.
verification:
  - python scripts/collaboration_governance_gate.py --check
  - python scripts/self_improvement_cycle.py assess
  - python scripts/evidence_index_generator.py --check
handoff: State whether scribe_state changed and cite the exact evidence/waiver decision.
stop_condition: Stop after scribe evidence is real and indexed, or after a blocker review explains why the waiver cannot yet be removed.
verified_at: 2026-06-17T17:26:02+09:00
verified_by: scribe-20260617-172500-kst-573
evidence_refs:
  - reviews/VERIFY-2026-06-17-unit-task-ar-573-001-20260617172602.json
---

# UNIT-TASK-AR-573-001 - Prove scribe usage before waiver burn-down

## Context

The maturity report shows scribe_state unknown and waiver_debt 1. This unit should create real evidence rather than editing metrics directly.

## Inputs

- reviews/REPORT-2026-06-17-self-improvement-maturity.md
- agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json
- scripts/collaboration_governance_gate.py

## Target Files

- agents/runtime/task_claims
- agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json
- scripts/collaboration_governance_gate.py
- reviews/INDEX.md

## Scope

Create or route real scribe evidence through the existing lifecycle. Avoid synthetic evidence and do not weaken the governance gate.

## Steps

1. Inspect how collaboration_governance_gate detects scribe waiver debt.
2. Route a scribe-role evidence record through the claim/log path or document a blocker if the dispatcher cannot represent the role.
3. Remove or update the waiver only after the gate proves the evidence is sufficient.
4. Index the resulting evidence.

## Acceptance Criteria

- The scribe debt is measurably reduced or a concrete blocker is recorded.
- No waiver is removed without a passing gate or explicit review decision.
- The evidence survives git clean/reset because it is committed.

## Verification

- `python scripts/collaboration_governance_gate.py --check`
- `python scripts/self_improvement_cycle.py assess`
- `python scripts/evidence_index_generator.py --check`

## Handoff

State whether scribe_state changed and cite the exact evidence/waiver decision.

## Stop Boundary

Stop after scribe evidence is real and indexed, or after a blocker review explains why the waiver cannot yet be removed.