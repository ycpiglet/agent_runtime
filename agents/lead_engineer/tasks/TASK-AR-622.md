---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-622
display_id: TASK-AR-622
task_uid: 94fa1156-59b8-4012-b64d-df9af471ef30
work_id: TASK-AR-622
work_uid: 94fa1156-59b8-4012-b64d-df9af471ef30
kind: task
parent_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
registered_at: 2026-07-23T15:01:03+09:00
created_at: 2026-07-23T15:01:03+09:00
started_at: 2026-07-24T15:28:44+09:00
updated_at: 2026-07-24T16:13:17+09:00
title: Preserve literal work frontmatter scalars across rewrites
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 6000
owner: lead-engineer
initiative_id: INIT-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-622/UNIT-TASK-AR-622-001.md
reservation_id: RES-20260723-150103-538c9c74-01
origin_type: verification_audit_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
created_by: codex-root-planner
summary: Specify lossless scalar encoding plus fail-closed legacy detection and add regressions for hash-bearing provenance and context.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli
  - frontmatter
  - data-integrity
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
  - python scripts/owner_governance_gate.py
verification_status: passed
verified_at: 2026-07-24T16:12:22+09:00
verified_by: /root/task-ar-622
evidence_refs:
  - reviews/VERIFY-2026-07-24-task-ar-622-20260724161222.json
resolution: done
completed_at: 2026-07-24T16:13:17+09:00
closed_by: /root/task-ar-622
actual_hours: 0.8
actual_tokens: 16000
---

# TASK-AR-622 - Preserve literal work frontmatter scalars across rewrites

## Goal

- Ensure work registration and lifecycle rewrites round-trip scalar values containing YAML-significant characters without data loss, and refuse unsafe legacy raw scalars before they can be silently truncated.

## Scope

- Define parser-safe registration and rewrite behavior plus fail-closed detection or an explicitly reviewed migration path for legacy unquoted scalars whose raw `#` suffix would otherwise be lost.

## Acceptance Criteria

- Registration writes hash-bearing scalar metadata in a parser-safe representation.
- Verify and close rewrites preserve the exact parser-visible scalar value.
- Verify and close refuse a legacy unquoted hash-bearing raw scalar before rewrite unless an explicit reviewed migration preserves the intended source value.
- Focused registration, verify, close, and Owner governance tests pass.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`
- `python scripts/owner_governance_gate.py`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-24T16:13:17+09:00`
- Resolution: `done`
- Actual hours: `0.8`
- Actual tokens: `16000`
- Closed by: `/root/task-ar-622`
- Evidence:
  - `reviews/VERIFY-2026-07-24-task-ar-622-20260724161222.json`
<!-- work-close:end -->
