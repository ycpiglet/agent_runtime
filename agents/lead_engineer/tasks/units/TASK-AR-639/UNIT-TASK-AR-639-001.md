---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-639-001
work_uid: bf59859d-1524-4e16-910f-312c3f1bd886
kind: unit
parent_id: TASK-AR-639
unit_id: UNIT-TASK-AR-639-001
task_id: TASK-AR-639
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T17:36:56+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Align work registration output with verify and close consumers
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-631 exposed that work.py new renders acceptance and verification only in task body text while work.py verify consumes frontmatter. The same registered task therefore cannot use the advertised lifecycle without manual repair.
inputs:
  - scripts/work.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - reviews/ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B.md
target_files:
  - scripts/work.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
scope: Persist executable acceptance/verification metadata at registration, preserve legacy body fallback, and add regression coverage. Do not redesign the full work schema.
acceptance:
  - New task frontmatter contains acceptance and verification.
  - Legacy tasks with valid body verification remain executable.
  - Unsupported commands fail visibly rather than being silently skipped.
  - Historical unknown metrics are not coerced to zero.
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
handoff: Report the failing-before/passing-after round trip and the compatibility behavior for existing task records.
stop_condition: Stop if the fix requires changing work-item identity or rewriting historical completed records.
verified_at: 2026-07-28T17:09:13+09:00
verified_by: le-20260728-170130-kst-codexroot-v080-639-001
evidence_refs:
  - reviews/VERIFY-2026-07-28-unit-task-ar-639-001-20260728170913.json
  - reviews/W4B-2026-07-28-unit-task-ar-639-001.md
resolution: done
completed_at: 2026-07-28T17:36:56+09:00
closed_by: codex-root-v080-w6
measurement_unavailable_reason: Pilot work spanned lifecycle recovery, CI, independent verification, and manual projection reconciliation before reliable per-unit time and token metering was available.
---

# UNIT-TASK-AR-639-001 - Align work registration output with verify and close consumers

## Context

TASK-AR-631 exposed that work.py new renders acceptance and verification only in task body text while work.py verify consumes frontmatter. The same registered task therefore cannot use the advertised lifecycle without manual repair.

## Inputs

- scripts/work.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- reviews/ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B.md

## Target Files

- scripts/work.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py

## Scope

Persist executable acceptance/verification metadata at registration, preserve legacy body fallback, and add regression coverage. Do not redesign the full work schema.

## Steps

1. Add a failing registration-to-verify round-trip test.
2. Persist task acceptance and verification lists in frontmatter.
3. Add a safe legacy body fallback for existing tasks.
4. Prove closeout accepts real evidence and an explicit unavailable-measurement reason.

## Acceptance Criteria

- New task frontmatter contains acceptance and verification.
- Legacy tasks with valid body verification remain executable.
- Unsupported commands fail visibly rather than being silently skipped.
- Historical unknown metrics are not coerced to zero.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`

## Handoff

Report the failing-before/passing-after round trip and the compatibility behavior for existing task records.

## Stop Boundary

Stop if the fix requires changing work-item identity or rewriting historical completed records.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T17:36:56+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Pilot work spanned lifecycle recovery, CI, independent verification, and manual projection reconciliation before reliable per-unit time and token metering was available.
- Closed by: `codex-root-v080-w6`
- Evidence:
  - `reviews/VERIFY-2026-07-28-unit-task-ar-639-001-20260728170913.json`
  - `reviews/W4B-2026-07-28-unit-task-ar-639-001.md`
<!-- work-close:end -->
