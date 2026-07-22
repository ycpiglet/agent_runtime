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
updated_at: 2026-07-23T08:40:51+09:00
title: Preserve work frontmatter values across lifecycle rewrites
status: planned
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
summary: Serialize work frontmatter scalars so literal hash markers and quotes survive every parse and rewrite boundary.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-617 - Preserve work frontmatter values across lifecycle rewrites

## Goal

- Prevent work registration, verification, and close operations from truncating or changing canonical string and list metadata.

## Scope

- Change only scripts/work.py frontmatter emission and focused registration, verify, and close tests; retain the existing lightweight parser and deterministic output shape.

## Acceptance Criteria

- Scalar and list metadata containing literal hash markers retain their complete parsed values after registration, verification, and close rewrites.
- Quote-bearing values and ordinary existing metadata retain their exact parsed values without double escaping or type-like coercion.
- Frontmatter key ordering, list ordering, body content, evidence linkage, and existing lifecycle behavior remain unchanged.

## Verification

- `python -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q`
- `python scripts/work_schema_gate.py --check`
