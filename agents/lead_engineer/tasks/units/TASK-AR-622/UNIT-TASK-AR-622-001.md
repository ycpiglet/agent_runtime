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
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-23T15:01:03+09:00
updated_at: 2026-07-23T15:01:03+09:00
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
context: TASK-AR-602 W4a exposed silent truncation when unquoted origin_ref and context values contained hash-prefixed issue references and were parsed/re-emitted during verification.
inputs:
  - reviews/REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md
  - reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
  - scripts/work.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
target_files:
  - scripts/work.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
  - reviews/
scope: Define a lossless frontmatter scalar contract, cover registration plus verify/close round trips, and implement the smallest compatible serializer change.
acceptance:
  - Hash-bearing origin_ref and context values survive registration and lifecycle rewrites exactly.
  - Existing scalar encoding compatibility and evidence schema remain unchanged.
  - Historical work records and evidence are not bulk rewritten.
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
  - python scripts/owner_governance_gate.py
handoff: Report the reproduction, chosen scalar contract, exact round-trip assertions, focused test results, governance result, and compatibility notes.
stop_condition: Stop before bulk-rewriting historical work records, changing the evidence schema, or accepting silent value normalization.
---

# UNIT-TASK-AR-622-001 - Define and test lossless work scalar serialization

## Context

TASK-AR-602 W4a exposed silent truncation when unquoted origin_ref and context values contained hash-prefixed issue references and were parsed/re-emitted during verification.

## Inputs

- reviews/REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md
- reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
- scripts/work.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py

## Target Files

- scripts/work.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py
- reviews/

## Scope

Define a lossless frontmatter scalar contract, cover registration plus verify/close round trips, and implement the smallest compatible serializer change.

## Steps

1. Reproduce literal hash truncation from a registered work record.
2. Add exact-value round-trip regressions across registration, verify, and close.
3. Implement parser-safe scalar serialization and run focused plus governance verification.

## Acceptance Criteria

- Hash-bearing origin_ref and context values survive registration and lifecycle rewrites exactly.
- Existing scalar encoding compatibility and evidence schema remain unchanged.
- Historical work records and evidence are not bulk rewritten.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`
- `python scripts/owner_governance_gate.py`

## Handoff

Report the reproduction, chosen scalar contract, exact round-trip assertions, focused test results, governance result, and compatibility notes.

## Stop Boundary

Stop before bulk-rewriting historical work records, changing the evidence schema, or accepting silent value normalization.
