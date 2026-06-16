---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-572-001
work_uid: eea72925-4582-44ed-9ce2-82350990c5b3
kind: unit
parent_id: TASK-AR-572
unit_id: UNIT-TASK-AR-572-001
task_id: TASK-AR-572
task_set_id: TASKSET-AR-SELF-IMPROVEMENT-CADENCE
initiative_id: INIT-AR-SELF-IMPROVEMENT-CADENCE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-17T08:31:23+09:00
updated_at: 2026-06-17T08:31:23+09:00
origin_type: owner_request
origin_ref: owner-request:low-frequency-agent-skill-self-improvement-cycle
created_by: codex-planner
summary: Wire maturity reporting into governance surfaces
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner asked to report once the loop is mature or measurably improved. This unit defines the reporting threshold and makes the remaining state visible without chat-only closure.
inputs:
  - scripts/self_improvement_cycle.py cycle --json
  - BACKLOG-BOARD.md
  - STATUS.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - reviews/INDEX.md
target_files:
  - scripts/self_improvement_cycle.py
  - STATUS.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - reviews/INDEX.md
  - tests/test_self_improvement_cycle.py
scope: Update reporting surfaces and verification only after the assessment/cycle commands exist. Do not mark the persistent goal complete unless every explicit objective is verified.
acceptance:
  - The report gives numeric before/after or baseline/current metrics.
  - Remaining work is visible in task records and next-session pointer if maturity is not reached.
  - All relevant gates pass or have explicit watch-only residual risk.
verification:
  - python -m pytest tests/test_self_improvement_cycle.py -q
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-CADENCE --check
  - python scripts/evidence_index_generator.py --check
handoff: Final report states current maturity level, metric values, and whether the active thread goal remains open.
stop_condition: Stop after reporting maturity state; if metrics are not mature, leave the goal active with the next concrete cycle.
---

# UNIT-TASK-AR-572-001 - Wire maturity reporting into governance surfaces

## Context

The Owner asked to report once the loop is mature or measurably improved. This unit defines the reporting threshold and makes the remaining state visible without chat-only closure.

## Inputs

- scripts/self_improvement_cycle.py cycle --json
- BACKLOG-BOARD.md
- STATUS.md
- agents/project/NEXT-SESSION-POINTER.yml
- reviews/INDEX.md

## Target Files

- scripts/self_improvement_cycle.py
- STATUS.md
- agents/project/NEXT-SESSION-POINTER.yml
- reviews/INDEX.md
- tests/test_self_improvement_cycle.py

## Scope

Update reporting surfaces and verification only after the assessment/cycle commands exist. Do not mark the persistent goal complete unless every explicit objective is verified.

## Steps

1. Define maturity thresholds from score, unwaived blocks, waiver debt, monitored-role gaps, low-reuse assets, and cycle artifacts written.
2. Update status/pointer with current state and next cycle entrypoint.
3. Run governance and evidence gates.
4. Report whether the loop is still active, improving, or mature.

## Acceptance Criteria

- The report gives numeric before/after or baseline/current metrics.
- Remaining work is visible in task records and next-session pointer if maturity is not reached.
- All relevant gates pass or have explicit watch-only residual risk.

## Verification

- `python -m pytest tests/test_self_improvement_cycle.py -q`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-SELF-IMPROVEMENT-CADENCE --check`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Final report states current maturity level, metric values, and whether the active thread goal remains open.

## Stop Boundary

Stop after reporting maturity state; if metrics are not mature, leave the goal active with the next concrete cycle.
