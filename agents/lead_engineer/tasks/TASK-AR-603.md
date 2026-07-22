---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-603
display_id: TASK-AR-603
task_uid: c67cb336-d52a-433c-9619-273e54b2e233
work_id: TASK-AR-603
work_uid: c67cb336-d52a-433c-9619-273e54b2e233
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T20:30:41+09:00
title: Unify canonical task ID producers and consumers
status: planned
priority: P0
difficulty: L
est_hours: 4
est_tokens: 18000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-603/UNIT-TASK-AR-603-001.md
reservation_id: RES-20260722-174500-dbaf8585-01
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Make allocator-generated timestamp IDs pass every canonical routing consumer without rewriting the ID.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_task_identity.py tests/test_taskset_dispatcher.py tests/test_conversation_work_audit.py -q
  - python scripts/regen_host_lock_if_needed.py --check
tags:
  - github-299
  - identity
  - cross-cutting
verification_status: passed
verified_at: 2026-07-22T20:30:41+09:00
verified_by: codex-root
evidence_refs:
  - reviews/VERIFY-2026-07-22-task-ar-603-20260722202126.json
  - reviews/VERIFY-2026-07-22-task-ar-603-20260722203041.json
---

# TASK-AR-603 - Unify canonical task ID producers and consumers

## Goal

- Close GitHub #299 by defining one case-compatible canonical task-ID contract used by allocation, dispatch, and conversation traceability.

## Scope

- Close GitHub #299 by defining one case-compatible canonical task-ID contract used by allocation, dispatch, and conversation traceability.

## Acceptance Criteria

- A default allocator result containing hexadecimal letters passes taskset plan and readiness unchanged.
- Lowercase and uppercase timestamp suffixes are interpreted consistently by canonical consumers.
- Numeric TASK-AR IDs and existing task records remain compatible.
- Root/template parity and host lock checks pass.

## Verification

- `python -m pytest tests/test_task_identity.py tests/test_taskset_dispatcher.py tests/test_conversation_work_audit.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`