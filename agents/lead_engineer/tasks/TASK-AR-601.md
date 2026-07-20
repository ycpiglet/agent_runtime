---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-601
display_id: TASK-AR-601
task_uid: 2aa3617a-9d42-4e59-86eb-767dafda2627
work_id: TASK-AR-601
work_uid: 2aa3617a-9d42-4e59-86eb-767dafda2627
kind: task
parent_id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
registered_at: 2026-07-20T12:56:05+09:00
created_at: 2026-07-20T12:56:05+09:00
updated_at: 2026-07-20T12:56:05+09:00
title: Repair portable hooks and clean the checkout
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 4000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-HOOK-PORTABILITY-CLEANUP
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-HOOK-PORTABILITY-CLEANUP
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-601/UNIT-TASK-AR-601-001.md
reservation_id: RES-20260720-125605-3b7049d9-01
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md
created_by: codex-root
summary: Fix Linux hook failures and restore a clean, synchronized checkout.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-601 - Repair portable hooks and clean the checkout

## Goal

- Replace platform-specific hook commands, enforce executable Git hook metadata, install the local hook configuration, and complete the claimed worktree lifecycle without stale worktrees or branches.

## Scope

- Codex hook command portability, Git hook executable metadata/configuration, regression coverage, environment bootstrap, and lifecycle cleanup only.

## Acceptance Criteria

- All commands in the live and host-template Codex hook manifests are free of machine-specific absolute paths and Windows-only command dependencies.
- Repository Git hooks are tracked executable and core.hooksPath points to .githooks.
- Focused hook, bootstrap, lock, parity, and governance tests pass.
- The final main checkout has no uncommitted changes, no stale task worktree, and no unmerged task branch from this work.

## Verification

- `python -m pytest tests/test_stop_hook_owner_governance.py tests/test_session_dashboard.py tests/test_lock_merge_driver.py tests/test_bootstrap_dev_env.py -q`
- `python scripts/lock_merge_driver.py pre-commit`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
- `python scripts/work.py status`
- `git status --short --branch`
