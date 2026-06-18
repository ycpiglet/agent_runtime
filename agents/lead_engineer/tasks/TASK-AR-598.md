---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-598
display_id: TASK-AR-598
task_uid: cd29a1c0-fab4-4f56-8ea3-2520d43a02ea
work_id: TASK-AR-598
work_uid: cd29a1c0-fab4-4f56-8ea3-2520d43a02ea
kind: task
parent_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
registered_at: 2026-06-19T00:00:00+09:00
created_at: 2026-06-19T00:00:00+09:00
updated_at: 2026-06-19T00:00:00+09:00
title: Wire UI/UX cycle into seminar and beta-tester artifacts
status: planned
priority: P2
difficulty: M
est_hours: 4
est_tokens: 8000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-UI-UX-CONTINUOUS-IMPROVEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
reservation_id: RES-20260619-000000-c51b5d19-02
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Make the UI/UX cycle able to record meeting/seminar/beta-tester artifact skeletons after each implementation round, preserving exploratory verification requirements.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-598 - Wire UI/UX cycle into seminar and beta-tester artifacts

## Goal

- Make the UI/UX cycle able to record meeting/seminar/beta-tester artifact skeletons after each implementation round, preserving exploratory verification requirements.

## Scope

- Extend the conductor after the read-only baseline lands. Do not fabricate live agent dialogue; create proposal/evidence shells only.

## Acceptance Criteria

- The cycle can plan seminar, meeting, and beta-tester evidence artifacts for a selected UI task.
- Beta-tester evidence requires exploratory user-like actions, recovery attempts, environment notes, and failure IDs.
- Generated artifacts are indexed and gated.

## Verification

- `python -m pytest tests/test_ui_ux_cycle.py tests/test_meeting_room.py -q`
- `python scripts/ui_ux_cycle.py --root . plan-review --task-id TASK-AR-583 --dry-run --json`
