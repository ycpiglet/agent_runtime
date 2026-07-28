---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-644
display_id: TASK-AR-644
task_uid: 5c9859e2-a377-4a6e-8954-bd008fce920c
work_id: TASK-AR-644
work_uid: 5c9859e2-a377-4a6e-8954-bd008fce920c
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T01:16:58+09:00
title: Provide cross-platform start, compact, and resume continuity hooks
status: planned
priority: P0
difficulty: L
est_hours: 10
est_tokens: 22000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-644/UNIT-TASK-AR-644-001.md
reservation_id: RES-20260728-163601-b8c2a87a-06
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Make the harness actually enter and re-enter its governance path on supported agent clients and operating systems.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-644 - Provide cross-platform start, compact, and resume continuity hooks

## Goal

- Make the harness actually enter and re-enter its governance path on supported agent clients and operating systems.

## Scope

- Replace Windows-only hook commands, add hook installation/doctor checks, and checkpoint/rebootstrap around compaction and interrupted sessions.

## Acceptance Criteria

- Linux and Windows hook command paths execute.
- SessionStart runs host context, active work, compound lookup, and resume checks.
- PreCompact checkpoints and PostCompact rebootstrap are installed where supported.
- Missing or stale hooks are visible in doctor.

## Verification

- `python -m pytest tests/test_session_continuity_hooks.py tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_interrupted_run_detector.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python -m pytest -q`
