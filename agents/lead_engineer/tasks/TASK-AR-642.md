---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-642
display_id: TASK-AR-642
task_uid: b1117f99-eb93-4481-9e0d-35c08aa4954d
work_id: TASK-AR-642
work_uid: b1117f99-eb93-4481-9e0d-35c08aa4954d
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Make sync ownership-aware and explicitly reconcilable
status: planned
priority: P0
difficulty: L
est_hours: 12
est_tokens: 26000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-642/UNIT-TASK-AR-642-001.md
reservation_id: RES-20260728-163601-b8c2a87a-04
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Update safe runtime files without overwriting host state or allowing one expected seam to freeze every unrelated update.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-642 - Make sync ownership-aware and explicitly reconcilable

## Goal

- Update safe runtime files without overwriting host state or allowing one expected seam to freeze every unrelated update.

## Scope

- Apply profile-selected manifests and ownership modes, provide a non-mutating reconcile report, and permit explicit safe-only application without silent merge.

## Acceptance Criteria

- seed_once files stop being managed after installation.
- host_owned and generated files are never overwritten.
- Safe managed updates can be selected explicitly while conflicts remain reported.
- Pinned upstream ref, not the locally installed template version, drives comparison.

## Verification

- `python -m pytest tests/test_inventory_sync_sanitize.py tests/test_doctor.py tests/test_template_smoke.py -q`
