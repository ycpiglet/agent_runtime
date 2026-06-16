---
id: TASK-AR-569
display_id: TASK-AR-569
task_uid: 4a0e922b-6b9d-4888-8091-14a60c99dbde
registered_at: 2026-06-15T17:43:04+09:00
created_at: 2026-06-15T17:43:04+09:00
started_at: 2026-06-16T23:28:33+09:00
updated_at: 2026-06-16T23:33:38+09:00
completed_at: 2026-06-16T23:33:38+09:00
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

# TASK-AR-569 - E2E + DOM budget regression

## Goal

- E2E asserting home <= 2 screens / DOM <= ~1500 + maturity behaviors (responsive/a11y/SSE/i18n/validation) preserved.

## Refs

- Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md

## W4a Self Verification

- Added an E2E regression that exercises the real console server and asserts the decision-first home remains under the DOM budget (`<= 1500` initial elements).
- Added a decision-shell budget check (`<= 320` elements before the work surface) as the CI-safe proxy for preserving the 1-2 screen home cockpit.
- Asserted progressive disclosure remains intact with exactly one active view and hidden inactive views.
- Asserted maturity behaviors remain present in the same E2E path: responsive CSS, skip-link/landmarks/ARIA, SSE client/route, KO/EN i18n resource, and form validation signals.
- Verification:
  - `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 13 passed.
  - `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.
