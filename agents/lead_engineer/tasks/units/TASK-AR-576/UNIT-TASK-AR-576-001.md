---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-576-001
work_uid: 9894e8cb-28ae-46a3-b6bf-e5f2b93473bc
kind: unit
parent_id: TASK-AR-576
unit_id: UNIT-TASK-AR-576-001
task_id: TASK-AR-576
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
initiative_id: INIT-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-06-17T17:15:00+09:00
updated_at: 2026-06-17T18:34:59+09:00
origin_type: owner_request
origin_ref: reviews/REPORT-2026-06-17-self-improvement-maturity.md
created_by: codex-planner
summary: Measure remediation delta and update handoff surfaces
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The first cycle established a baseline but did not improve metrics. This unit decides whether remediation produced measurable improvement.
inputs:
  - reviews/REPORT-2026-06-17-self-improvement-maturity.md
  - scripts/self_improvement_cycle.py
  - STATUS.md
  - agents/project/NEXT-SESSION-POINTER.yml
target_files:
  - scripts/self_improvement_cycle.py
  - STATUS.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - reviews/INDEX.md
scope: Publish the delta and next state. Do not edit thresholds to make the result look better.
acceptance:
  - A delta report exists and is indexed.
  - Goal state is truthful: mature, improving, or still active.
  - Verification commands prove report freshness.
verification:
  - python scripts/self_improvement_cycle.py report --dry-run --json
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE --check
  - python scripts/evidence_index_generator.py --check
handoff: State the before/after metrics and whether the persistent self-improvement goal remains open.
stop_condition: Stop after the delta report and handoff surfaces are committed.
verified_at: 2026-06-17T18:34:59+09:00
verified_by: lead-engineer-20260617-remediation-delta-576
evidence_refs:
  - reviews/VERIFY-2026-06-17-unit-task-ar-576-001-20260617183459.json
---

# UNIT-TASK-AR-576-001 - Measure remediation delta and update handoff surfaces

## Context

The first cycle established a baseline but did not improve metrics. This unit decides whether remediation produced measurable improvement.

## Inputs

- reviews/REPORT-2026-06-17-self-improvement-maturity.md
- scripts/self_improvement_cycle.py
- STATUS.md
- agents/project/NEXT-SESSION-POINTER.yml

## Target Files

- scripts/self_improvement_cycle.py
- STATUS.md
- agents/project/NEXT-SESSION-POINTER.yml
- reviews/INDEX.md

## Scope

Publish the delta and next state. Do not edit thresholds to make the result look better.

## Steps

1. Run assessment and report commands after remediation work is merged.
2. Compare score, role_gaps, asset_gaps, waiver_debt, and scribe_state against the first report.
3. Update status and next-session pointer with true goal state.
4. Register or queue the next cycle if the target_next threshold is not reached.

## Acceptance Criteria

- A delta report exists and is indexed.
- Goal state is truthful: mature, improving, or still active.
- Verification commands prove report freshness.

## Verification

- `python scripts/self_improvement_cycle.py report --dry-run --json`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE --check`
- `python scripts/evidence_index_generator.py --check`

## Handoff

State the before/after metrics and whether the persistent self-improvement goal remains open.

## Stop Boundary

Stop after the delta report and handoff surfaces are committed.
