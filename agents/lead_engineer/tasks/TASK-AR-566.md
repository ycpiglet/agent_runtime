---
id: TASK-AR-566
display_id: TASK-AR-566
task_uid: 324b1b84-0709-43b0-960a-b63ce7758d0c
registered_at: 2026-06-15T17:43:04+09:00
created_at: 2026-06-15T17:43:04+09:00
updated_at: 2026-06-16T22:21:17+09:00
started_at: 2026-06-16T22:05:45+09:00
completed_at: 2026-06-16T22:21:17+09:00
status: completed
priority: P1
difficulty: L
est_hours: 8
est_tokens: 7000
owner: lead_engineer
task_set_id: TASKSET-AR-DECISION-FIRST-CONSOLE-IA
tags:
  - ui
  - decision-first
  - ia
---

# TASK-AR-566 - Progressive-disclosure detail panel

## Goal

- Counts/summaries on screen; detail opens in a keyboard-accessible side drawer on click (no inline full content). Home <= 2 screens, DOM budget.

## Refs

- Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md
- Review: reviews/REVIEW-2026-06-16-task-ar-566-progressive-disclosure.md

## Verification

- `$env:PYTHONPATH=(Resolve-Path src).Path; python -m pytest tests/test_ui_console.py -q` -> 149 passed
- `$env:PYTHONPATH=(Resolve-Path src).Path; python -m pytest tests/test_ui_console_e2e.py -q` -> 9 passed
