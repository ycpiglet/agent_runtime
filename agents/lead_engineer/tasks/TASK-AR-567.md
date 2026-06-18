---
id: TASK-AR-567
display_id: TASK-AR-567
task_uid: b924243c-6c8b-4f73-8ac4-370591088812
registered_at: 2026-06-15T17:43:04+09:00
created_at: 2026-06-15T17:43:04+09:00
started_at: 2026-06-16T22:31:44+09:00
updated_at: 2026-06-16T22:45:01+09:00
completed_at: 2026-06-16T22:45:01+09:00
status: completed
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-DECISION-FIRST-CONSOLE-IA
tags:
  - ui
  - decision-first
  - ia
---

# TASK-AR-567 - Work state board (secondary hero)

## Goal

- Initiative->Taskset->Unit waiting/active/done board + drill-down (reuse org_read_api.work_state).

## Refs

- Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md

## W4a Self Verification

- Implemented `work_state` UI state resource backed by `scripts/org_read_api.py::work_state`.
- Added `/api/work_state` and `/api/work-state` routes.
- Added Home `Work state` secondary hero with compact counts and task drill-down.
- Verification:
  - `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 151 passed.
  - `PYTHONPATH=src python -m pytest tests/test_org_read_api.py -q` -> 3 passed.
  - `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 11 passed.
