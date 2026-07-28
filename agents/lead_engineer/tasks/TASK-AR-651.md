---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-651
display_id: TASK-AR-651
task_uid: ca64bb99-2bc8-4be6-a9fb-8e764a1724f1
work_id: TASK-AR-651
work_uid: ca64bb99-2bc8-4be6-a9fb-8e764a1724f1
kind: task
parent_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
registered_at: 2026-07-28T16:36:01+09:00
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
title: Prepare v0.8.0 release candidate from pilot evidence
status: planned
priority: P0
difficulty: L
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-651/UNIT-TASK-AR-651-001.md
reservation_id: RES-20260728-163601-b8c2a87a-13
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Produce an exact, installable v0.8.0-rc.1 candidate whose release claims are backed by clean-host, pilot, migration, and browser evidence.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-651 - Prepare v0.8.0 release candidate from pilot evidence

## Goal

- Produce an exact, installable v0.8.0-rc.1 candidate whose release claims are backed by clean-host, pilot, migration, and browser evidence.

## Scope

- Run version/document cascade, tag freshness, clean-tag installs, mandatory browser smoke, release council gates, and prepare but do not publish the final release without Owner approval.

## Acceptance Criteria

- README, package, module, template, lock, and release metadata agree on v0.8.0-rc.1.
- Tag discovery cannot silently use stale local refs.
- Clean installs from the exact candidate tag pass lifecycle and browser smoke.
- Bean Wiki, Allimbot, and Autofolio evidence is linked from release readiness.

## Verification

- `python -m pytest tests -q`
- `RUN_BETA_EXPLORATION=1 python -m pytest tests/test_ui_console_beta_exploration.py -q`
- `python scripts/release_readiness_summary.py --check`
- `python scripts/release_execution_gate.py --check`
