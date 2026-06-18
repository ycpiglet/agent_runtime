---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-600
display_id: TASK-AR-600
task_uid: ea6e499e-86af-41cf-a2a5-76b53555b7e5
work_id: TASK-AR-600
work_uid: ea6e499e-86af-41cf-a2a5-76b53555b7e5
kind: task
parent_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
registered_at: 2026-06-19T08:18:00+09:00
created_at: 2026-06-19T08:18:00+09:00
updated_at: 2026-06-19T08:18:00+09:00
title: Run lead-designer UI direction seminar
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 5000
owner: lead-designer
team: ui-ux
initiative_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md
reservation_id: RES-20260619-081800-ff02ebb7-01
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Create the seminar artifact that decides what new visual direction should be explored next, instead of letting implementation workers repeat the current UI language by default.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-600 - Run lead-designer UI direction seminar

## Goal

- Create the seminar artifact that decides what new visual direction should be explored next, instead of letting implementation workers repeat the current UI language by default.

## Scope

- Planning and evidence only. Do not edit UI source files. The seminar must cover typography, size, color, motion, effects, schema, assets, accessibility, responsiveness, and interaction.

## Acceptance Criteria

- reviews/SEMINAR-2026-06-19-ui-ux-design-direction.md records lead-designer, design-system-steward, interface-designer, and ux-evaluator viewpoints.
- The seminar states the user problem, target screen or workflow, and why the current visual direction is insufficient.
- The seminar evaluates typography, size/spacing, color, motion, effects, schema, assets, accessibility, responsiveness, and interaction with concrete evidence requirements.
- The seminar selects one RFC direction and rejects at least one alternative with rationale.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`
