---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-597
display_id: TASK-AR-597
task_uid: d6b061dd-580b-48ac-a7b1-2011022efee7
work_id: TASK-AR-597
work_uid: d6b061dd-580b-48ac-a7b1-2011022efee7
kind: task
parent_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
registered_at: 2026-06-19T00:00:00+09:00
created_at: 2026-06-19T00:00:00+09:00
updated_at: 2026-06-19T00:00:00+09:00
title: Add UI/UX cycle conductor
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 8000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-UI-UX-CONTINUOUS-IMPROVEMENT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md
reservation_id: RES-20260619-000000-c51b5d19-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Add a deterministic UI/UX cycle command that reads current design-system state, open UI tasks, recent meeting/seminar records, and beta-tester expectations, then emits a structured assessment and next-action plan without mutating UI source files.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-597 - Add UI/UX cycle conductor

## Goal

- Add a deterministic UI/UX cycle command that reads current design-system state, open UI tasks, recent meeting/seminar records, and beta-tester expectations, then emits a structured assessment and next-action plan without mutating UI source files.

## Scope

- Add a read-only script, focused tests, and documentation updates. Do not edit ui_console_assets.py or tests/test_ui_console.py while TASK-AR-593 owns overlapping UI footprints.

## Acceptance Criteria

- scripts/ui_ux_cycle.py has assess and report modes that summarize design-system gate status, open UI task candidates, role coverage, and beta-tester review requirements.
- The command identifies the next UI refactor action without touching files owned by active claims.
- The generated report explicitly covers typography, size, color, motion, effects, schema, and asset dimensions as a checklist.
- Focused tests prove deterministic output on fixture repos and no write side effects in assess mode.

## Verification

- `python -m pytest tests/test_ui_ux_cycle.py -q`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/ui_ux_cycle.py --root . report --dry-run --json`
