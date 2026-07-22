---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-616
display_id: TASK-AR-616
task_uid: 8bfdf2e2-d528-45e4-afd2-6edcf82f79c7
work_id: TASK-AR-616
work_uid: 8bfdf2e2-d528-45e4-afd2-6edcf82f79c7
kind: task
parent_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
registered_at: 2026-07-23T05:01:18+09:00
created_at: 2026-07-23T05:01:18+09:00
updated_at: 2026-07-23T05:29:52+09:00
started_at: 2026-07-23T05:14:06+09:00
title: Extend the exact fixture HEAD recovery window
status: in_progress
priority: P0
difficulty: S
est_hours: 1
est_tokens: 5000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-AUTO-FIXTURE-RECOVERY-WINDOW
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-616/UNIT-TASK-AR-616-001.md
reservation_id: RES-20260723-050118-d714d556-01
origin_type: ci_failure
origin_ref: reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md
created_by: codex-root-planner
summary: Lengthen the capped recovery window after the exact transient exhausted three short attempts in main CI.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
verification:
  - python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q
  - python -m pytest tests/test_backlog_board_tasksets.py -q
  - python scripts/taskset_work_gate.py --check
tags:
  - github-320
  - ci-flake
  - release-auto
  - test-fixture
  - repeated-failure
verification_status: passed
verified_at: 2026-07-23T05:29:52+09:00
verified_by: codex-root-task-ar-616
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-616-20260723052952.json
---

# TASK-AR-616 - Extend the exact fixture HEAD recovery window

## Goal

- Resolve the reopened GitHub issue 320 by recovering when three consecutive recognized pre-commit HEAD parse failures precede success.

## Scope

- Change only tests/test_release_auto_noncritical.py retry bound/backoff and focused regressions, plus the generated backlog taskset expectation. Preserve the exact retry classifier and all product behavior.

## Acceptance Criteria

- Three recognized pre-commit failures followed by success recover on the fourth attempt with deterministic capped delays.
- A permanent recognized failure exhausts at the new strict bound with sanitized attempts evidence.
- The exact classifier is unchanged and ambiguous or unrelated failures still stop on their first ambiguous result.
- A real fixture commit after three synthetic failures advances HEAD exactly once, and full regressions/gates pass.

## Verification

- `python -m pytest tests/test_release_auto_noncritical.py tests/test_release_cadence_trigger.py -q`
- `python -m pytest tests/test_backlog_board_tasksets.py -q`
- `python scripts/taskset_work_gate.py --check`