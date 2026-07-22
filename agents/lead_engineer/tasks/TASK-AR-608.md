---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-608
display_id: TASK-AR-608
task_uid: d8884a2d-8a9b-4766-bf41-5ed53f470880
work_id: TASK-AR-608
work_uid: d8884a2d-8a9b-4766-bf41-5ed53f470880
kind: task
parent_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
registered_at: 2026-07-22T17:45:00+09:00
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T17:45:00+09:00
title: Preserve quoted hashes in frontmatter scalars
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 7000
owner: lead-engineer
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-608/UNIT-TASK-AR-608-001.md
reservation_id: RES-20260722-174500-dbaf8585-06
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Close GitHub #298 by making comment stripping quote-aware while preserving existing unquoted comment behavior.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - github-298
  - frontmatter
  - parser
---

# TASK-AR-608 - Preserve quoted hashes in frontmatter scalars

## Goal

- Close GitHub #298 by making comment stripping quote-aware while preserving existing unquoted comment behavior.

## Scope

- Close GitHub #298 by making comment stripping quote-aware while preserving existing unquoted comment behavior.

## Acceptance Criteria

- Quoted # characters, escaped quotes, and flow-list values survive parsing.
- Unquoted comments retain current behavior.
- Malformed quotes fail or degrade deterministically without silent corruption.

## Verification

- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/regen_host_lock_if_needed.py --check`
