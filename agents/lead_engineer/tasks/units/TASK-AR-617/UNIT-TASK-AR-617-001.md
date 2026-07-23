---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-617-001
work_uid: aade884e-1c20-44e6-adc6-f3d965a82211
kind: unit
parent_id: TASK-AR-617
unit_id: UNIT-TASK-AR-617-001
task_id: TASK-AR-617
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
initiative_id: INIT-AR-WORK-CLI-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-23T08:40:51+09:00
updated_at: 2026-07-23T08:42:50+09:00
started_at: 2026-07-23T08:42:50+09:00
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
created_by: codex-root-planner
summary: Implement round-trip-safe work frontmatter emission
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
  - ambiguity
context: Completed task lifecycle commands reproduced silent truncation because scripts/work.py::_frontmatter emits raw values while the canonical reader treats an unquoted hash marker as a comment.
inputs:
  - reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
  - scripts/work.py
  - scripts/backlog_board.py
  - scripts/org_model_gate.py
  - scripts/work_schema_gate.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
target_files:
  - scripts/work.py
  - scripts/backlog_board.py
  - src/agent_runtime/templates/project/scripts/backlog_board.py
  - scripts/org_model_gate.py
  - scripts/work_schema_gate.py
  - src/agent_runtime/templates/project/scripts/work_schema_gate.py
  - tests/test_work_registration.py
  - tests/test_work_verify.py
  - tests/test_work_close.py
  - tests/test_backlog_board_tasksets.py
  - tests/test_org_model_gate.py
  - tests/test_attention_inbox.py
  - tests/test_dispatch_gate.py
  - tests/test_work_schema_gate.py
  - tests/fixtures/host/agent_runtime.lock.json
scope: Add a deterministic unsafe-scalar emitter and one shared marker decoder across backlog, org-model, and root/template work-schema readers, then prove preservation at registration, mutation, attention, and dispatch boundaries.
acceptance:
  - Every failure-first value parses identically before and after each lifecycle mutation.
  - No existing focused work CLI test changes its expected lifecycle semantics.
  - The implementation does not modify the shared comment scanner.
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
  - python scripts/work_schema_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Provide the failure-first commit, a value-by-value round-trip matrix, changed-file summary, focused test output, and any parser compatibility limitation.
stop_condition: Stop if exact value preservation requires replacing the shared parser or changing canonical work schema; record the incompatible examples for replan.
---

# UNIT-TASK-AR-617-001 - Implement round-trip-safe work frontmatter emission

## Context

Completed task lifecycle commands reproduced silent truncation because scripts/work.py::_frontmatter emits raw values while the canonical reader treats an unquoted hash marker as a comment.

## Inputs

- reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
- scripts/work.py
- scripts/backlog_board.py
- scripts/org_model_gate.py
- scripts/work_schema_gate.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py

## Target Files

- scripts/work.py
- scripts/backlog_board.py
- src/agent_runtime/templates/project/scripts/backlog_board.py
- scripts/org_model_gate.py
- scripts/work_schema_gate.py
- src/agent_runtime/templates/project/scripts/work_schema_gate.py
- tests/test_work_registration.py
- tests/test_work_verify.py
- tests/test_work_close.py
- tests/test_backlog_board_tasksets.py
- tests/test_org_model_gate.py
- tests/test_attention_inbox.py
- tests/test_dispatch_gate.py
- tests/test_work_schema_gate.py
- tests/fixtures/host/agent_runtime.lock.json

## Scope

Add a deterministic unsafe-scalar emitter and one shared marker decoder across backlog, org-model, and root/template work-schema readers, then prove preservation at registration, mutation, attention, and dispatch boundaries.

## Steps

1. Add failure-first registration, verification, and close cases for literal hash and quote-bearing values.
2. Implement the smallest compatible scalar emission rule without adding a YAML dependency.
3. Run focused modules and schema checks, then inspect historical compatibility fixtures.

## Acceptance Criteria

- Every failure-first value parses identically before and after each lifecycle mutation.
- No existing focused work CLI test changes its expected lifecycle semantics.
- The implementation does not modify the shared comment scanner.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q`
- `python scripts/work_schema_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Provide the failure-first commit, a value-by-value round-trip matrix, changed-file summary, focused test output, and any parser compatibility limitation.

## Stop Boundary

Stop if exact value preservation requires replacing the shared parser or changing canonical work schema; record the incompatible examples for replan.
