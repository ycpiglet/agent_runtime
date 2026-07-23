---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-617
display_id: TASK-AR-617
task_uid: 2bc4aabb-cd0d-41a6-aaba-46a99b2be23d
work_id: TASK-AR-617
work_uid: 2bc4aabb-cd0d-41a6-aaba-46a99b2be23d
kind: task
parent_id: TASKSET-AR-WORK-CLI-INTEGRITY
registered_at: 2026-07-23T08:40:51+09:00
created_at: 2026-07-23T08:40:51+09:00
updated_at: 2026-07-23T09:57:31+09:00
started_at: 2026-07-23T08:42:50+09:00
title: Preserve work frontmatter values across lifecycle rewrites
status: completed
priority: P0
difficulty: M
est_hours: 3
est_tokens: 7500
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-WORK-CLI-INTEGRITY
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-WORK-CLI-INTEGRITY
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-617/UNIT-TASK-AR-617-001.md
reservation_id: RES-20260723-084051-a1975741-01
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
created_by: codex-root-planner
summary: Serialize unsafe work frontmatter scalars and preserve their semantic values across lifecycle and operational consumers.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
  - python scripts/work_schema_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-07-23T09:40:20+09:00
verified_by: codex-root-task-ar-617-type-rework
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-617-20260723091055.json
  - reviews/VERIFY-2026-07-23-task-ar-617-20260723091656.json
  - reviews/VERIFY-2026-07-23-task-ar-617-20260723093020.json
  - reviews/VERIFY-2026-07-23-task-ar-617-20260723094020.json
resolution: done
completed_at: 2026-07-23T09:57:31+09:00
closed_by: codex-root-task-ar-617
actual_hours: 1.25
actual_tokens: 60000
---

# TASK-AR-617 - Preserve work frontmatter values across lifecycle rewrites

## Goal

- Prevent work registration, verification, and close operations from truncating or changing canonical string and list metadata.

## Scope

- Change `scripts/work.py` frontmatter emission plus shared marker decoding in backlog, org-model, and root/template work-schema parsers, focused lifecycle and operational-consumer tests, and the generated-host lock. Do not change attention/dispatch production behavior, comment scanning, or add a YAML dependency.

## Acceptance Criteria

- Scalar and list metadata containing literal hash markers retain their complete parsed values after registration, verification, and close rewrites.
- Quote-bearing values and ordinary existing metadata retain their exact parsed values without double escaping or type-like coercion.
- Frontmatter key ordering, list ordering, body content, evidence linkage, and existing lifecycle behavior remain unchanged.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q`
- `python scripts/work_schema_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-23T09:57:31+09:00`
- Resolution: `done`
- Actual hours: `1.25`
- Actual tokens: `60000`
- Closed by: `codex-root-task-ar-617`
- Evidence:
  - `reviews/VERIFY-2026-07-23-task-ar-617-20260723091055.json`
  - `reviews/VERIFY-2026-07-23-task-ar-617-20260723091656.json`
  - `reviews/VERIFY-2026-07-23-task-ar-617-20260723093020.json`
  - `reviews/VERIFY-2026-07-23-task-ar-617-20260723094020.json`
<!-- work-close:end -->
