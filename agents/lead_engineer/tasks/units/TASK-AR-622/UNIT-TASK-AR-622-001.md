---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-622-001
work_uid: 322e41f5-d11a-4eee-adb7-6004fcc64031
kind: unit
parent_id: TASK-AR-622
unit_id: UNIT-TASK-AR-622-001
task_id: TASK-AR-622
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
initiative_id: INIT-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-engineer
created_at: 2026-07-23T15:01:03+09:00
updated_at: 2026-07-24T16:11:54+09:00
origin_type: verification_audit_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
created_by: codex-root-planner
summary: Define and test lossless work scalar serialization
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
  - runtime
context: TASK-AR-602 W4a exposed silent truncation when legacy unquoted origin_ref and context values contained hash-prefixed issue references and were parsed before lifecycle rewrite; parser-visible round trips alone cannot detect a suffix that was already discarded.
inputs:
  - reviews/REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md
  - reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
  - reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK.md
  - scripts/work.py
  - scripts/backlog_board.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
target_files:
  - scripts/work.py
  - scripts/backlog_board.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
  - reviews/
scope: Define a lossless frontmatter scalar contract, cover registration plus verify/close round trips, fail closed on unsafe legacy raw scalars or require an explicitly reviewed migration, and implement the smallest compatible parser/serializer change.
acceptance:
  - Hash-bearing origin_ref and context values survive registration and lifecycle rewrites exactly.
  - A legacy unquoted raw scalar with a hash suffix cannot pass verification or close after silent parser truncation; the operation fails before rewrite unless an explicit reviewed migration supplies the intended value.
  - Existing scalar encoding compatibility and evidence schema remain unchanged.
  - Historical work records and evidence are not bulk rewritten.
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
  - python scripts/owner_governance_gate.py
handoff: Report the reproduction, chosen scalar contract, legacy fail-closed or reviewed-migration behavior, exact round-trip assertions, focused test results, governance result, and compatibility notes.
stop_condition: Stop before bulk-rewriting historical work records, changing the evidence schema, inferring a discarded suffix, or accepting silent value normalization.
verified_at: 2026-07-24T16:01:43+09:00
verified_by: /root/task-ar-622
evidence_refs:
  - reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051.json
  - reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415.json
  - reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724160143.json
resolution: done
completed_at: 2026-07-24T16:11:54+09:00
closed_by: /root/task-ar-622
actual_hours: 0.8
actual_tokens: 16000
---

# UNIT-TASK-AR-622-001 - Define and test lossless work scalar serialization

## Context

TASK-AR-602 W4a exposed silent truncation when legacy unquoted origin_ref and context values contained hash-prefixed issue references and were parsed before lifecycle rewrite. A parser-visible round trip alone cannot detect a suffix that was already discarded.

## Inputs

- reviews/REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md
- reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
- reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK.md
- scripts/work.py
- scripts/backlog_board.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py

## Target Files

- scripts/work.py
- scripts/backlog_board.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py
- reviews/

## Scope

Define a lossless frontmatter scalar contract, cover registration plus verify/close round trips, fail closed on unsafe legacy raw scalars or require an explicitly reviewed migration, and implement the smallest compatible parser/serializer change.

## Steps

1. Reproduce literal hash truncation from a registered work record.
2. Add a raw-record regression proving verify/close refuse a legacy unquoted hash suffix before rewrite unless a reviewed migration provides the intended value.
3. Add exact-value round-trip regressions across registration, verify, and close.
4. Implement parser-safe scalar handling and run focused plus governance verification.

## Acceptance Criteria

- Hash-bearing origin_ref and context values survive registration and lifecycle rewrites exactly.
- A legacy unquoted raw scalar with a hash suffix cannot pass verification or close after silent parser truncation; the operation fails before rewrite unless an explicit reviewed migration supplies the intended value.
- Existing scalar encoding compatibility and evidence schema remain unchanged.
- Historical work records and evidence are not bulk rewritten.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`
- `python scripts/owner_governance_gate.py`

## Handoff

Report the reproduction, chosen scalar contract, legacy fail-closed or reviewed-migration behavior, exact round-trip assertions, focused test results, governance result, and compatibility notes.

## Stop Boundary

Stop before bulk-rewriting historical work records, changing the evidence schema, inferring a discarded suffix, or accepting silent value normalization.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-24T16:11:54+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `16000`
- Closed by: `/root/task-ar-622`
- Evidence:
  - `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051.json`
  - `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415.json`
  - `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724160143.json`
<!-- work-close:end -->
