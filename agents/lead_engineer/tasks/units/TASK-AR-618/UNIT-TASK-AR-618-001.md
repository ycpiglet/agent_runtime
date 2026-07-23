---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-618-001
work_uid: cdfd3e0b-3534-4931-b18c-ef38fe38894e
kind: unit
parent_id: TASK-AR-618
unit_id: UNIT-TASK-AR-618-001
task_id: TASK-AR-618
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
initiative_id: INIT-AR-WORK-CLI-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-23T08:40:51+09:00
updated_at: 2026-07-23T12:39:00+09:00
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
created_by: codex-root-planner
summary: Implement exact work-item selector precedence
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - ambiguity
context: Independent verification for TASK-AR-594 and the TASK-AR-612 lifecycle both showed that an exact TASK ID expands to its task file plus descendant units and exits as ambiguous.
inputs:
  - reviews/W4B-2026-07-19-TASK-AR-594-RECHECK.md
  - scripts/work.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
  - tests/test_work_assign.py
  - tests/test_work_criteria.py
target_files:
  - scripts/work.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
  - tests/test_work_assign.py
  - tests/test_work_criteria.py
scope: Separate task identity from descendant unit discovery in the shared candidate resolver and pin the behavior across every generic command consumer.
acceptance:
  - Task commands no longer require an explicit path solely because units exist.
  - Unit commands never fall through to the parent task.
  - Duplicate or missing canonical records remain visible with stable error text.
verification:
  - python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q
  - python scripts/work_schema_gate.py --check
handoff: Provide the failure-first commit, selector precedence table, focused test output, and confirmation that no command-specific semantics changed.
stop_condition: Stop if deterministic exact-ID selection requires changing work hierarchy or accepting duplicate canonical task records; escalate with the conflicting paths.
verified_at: 2026-07-23T12:28:00+09:00
verified_by: /root/task-ar-618
evidence_refs:
  - reviews/VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800.json
resolution: done
completed_at: 2026-07-23T12:39:00+09:00
closed_by: /root/task-ar-618
actual_hours: 1.5
actual_tokens: 7000
---

# UNIT-TASK-AR-618-001 - Implement exact work-item selector precedence

## Context

Independent verification for TASK-AR-594 and the TASK-AR-612 lifecycle both showed that an exact TASK ID expands to its task file plus descendant units and exits as ambiguous.

## Inputs

- reviews/W4B-2026-07-19-TASK-AR-594-RECHECK.md
- scripts/work.py
- tests/test_work_verify.py
- tests/test_work_close.py
- tests/test_work_assign.py
- tests/test_work_criteria.py

## Target Files

- scripts/work.py
- tests/test_work_verify.py
- tests/test_work_close.py
- tests/test_work_assign.py
- tests/test_work_criteria.py

## Scope

Separate task identity from descendant unit discovery in the shared candidate resolver and pin the behavior across every generic command consumer.

## Steps

1. Add failure-first cases for a task with multiple units across verify, close, assign, and criteria.
2. Refine exact-ID candidate construction while preserving unit glob ambiguity and explicit paths.
3. Run focused consumers and schema checks, then document selector precedence.

## Acceptance Criteria

- Task commands no longer require an explicit path solely because units exist.
- Unit commands never fall through to the parent task.
- Duplicate or missing canonical records remain visible with stable error text.

## Verification

- `python -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q`
- `python scripts/work_schema_gate.py --check`

## Handoff

Provide the failure-first commit, selector precedence table, focused test output, and confirmation that no command-specific semantics changed.

## Stop Boundary

Stop if deterministic exact-ID selection requires changing work hierarchy or accepting duplicate canonical task records; escalate with the conflicting paths.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T12:39:00+09:00`
- Resolution: `done`
- Actual hours: `1.5`
- Actual tokens: `7000`
- Closed by: `/root/task-ar-618`
- Evidence:
  - `reviews/VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800.json`
<!-- work-close:end -->
