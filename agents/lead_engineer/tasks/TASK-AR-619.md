---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-619
display_id: TASK-AR-619
task_uid: d4edfeb6-39a0-41de-b64b-6e952ca374ae
work_id: TASK-AR-619
work_uid: d4edfeb6-39a0-41de-b64b-6e952ca374ae
kind: task
parent_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
registered_at: 2026-06-20T01:08:00+09:00
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
title: Implement Taskset Board evidence review queue and split loading states
status: planned
priority: P1
difficulty: L
est_hours: 6
est_tokens: 14000
owner: interface-designer
team: ui-ux
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-619/UNIT-TASK-AR-619-001.md
reservation_id: RES-20260620-010800-10191c6d-01
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Make the Taskset Board stale/missing evidence lane actionable by deriving a grouped evidence review queue, visible caps, hidden counts, ordering reasons, latency labels, and selected evidence detail while preserving the accepted attention workspace.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-619 - Implement Taskset Board evidence review queue and split loading states

## Goal

- Make the Taskset Board stale/missing evidence lane actionable by deriving a grouped evidence review queue, visible caps, hidden counts, ordering reasons, latency labels, and selected evidence detail while preserving the accepted attention workspace.

## Scope

- Source mutation is limited to read-only Taskset Board state derivation, UI asset helpers, Taskset Board client rendering, and focused tests. Do not change task/claim persistence, write command execution, dispatcher release semantics, or unrelated console views.

## Acceptance Criteria

- `/api/tasksets_board` exposes `attention_workspace.evidence_review_queue` with `version`, `summary_loaded_at`, `detail_loading_state`, `groups`, selected group, visible count, hidden count, and ordering reason fields.
- Evidence groups classify stale, missing, unverified, blocked, and deferrable items without relying on color alone.
- Queue rows preserve taskset id/title, owner/team, progress, evidence freshness, evidence age, severity, claim state, claim phase, command readiness, and reason text.
- The rendered Taskset Board shows group filters, cap disclosure, queue rows, latency badge, selected detail, empty states, and retry/defer affordances using escaped text.
- Repeated UI is promoted into asset helpers rather than page-local string duplication; any temporary orientation copy is labelled one_off_for_now in the verification evidence.
- Desktop and 390x844 CSS anchors keep summary, queue, detail, and inactive containment stable without document-level horizontal overflow.
- Focused tests cover state schema, grouping/capping, escaped render helpers, keyboard/focus anchors, reduced-motion-safe labels, and design-system class anchors.

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_design_assets.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`
