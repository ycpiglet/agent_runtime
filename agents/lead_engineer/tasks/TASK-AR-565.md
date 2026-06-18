---
id: TASK-AR-565
display_id: TASK-AR-565
task_uid: 6b69101b-e12e-47f8-948e-8cd9c37890e1
registered_at: 2026-06-15T17:43:04+09:00
created_at: 2026-06-15T17:43:04+09:00
updated_at: 2026-06-16T21:04:00+09:00
started_at: 2026-06-16T20:50:31+09:00
completed_at: 2026-06-16T21:04:00+09:00
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

# TASK-AR-565 - Nav prune (67 -> core 7 + More)

## Goal

- Group the 67 nav routes under core 7 (Home/Work/Agents/Decisions/Records/Search/More); no dead links.

## Refs

- Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md
- Review: reviews/REVIEW-2026-06-16-task-ar-565-nav-prune-core7.md
- Visual evidence: reviews/artifacts/task-ar-565-nav-core7.png

## Verification

- `python -m pytest tests/test_ui_console.py -q` -> 148 passed
- `python -m pytest tests/test_ui_console_e2e.py -q` -> 8 passed
- Python Playwright visual check against `http://127.0.0.1:8766/` -> core labels Home, Work, Agents, Decisions, Records, Search, More; More closed by default; no sidebar route missing a target view
