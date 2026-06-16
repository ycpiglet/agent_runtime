---
id: TASK-AR-568
display_id: TASK-AR-568
task_uid: b9ffa27b-90a6-4912-9c63-06658ff454d6
registered_at: 2026-06-15T17:43:04+09:00
created_at: 2026-06-15T17:43:04+09:00
started_at: 2026-06-16T23:01:31+09:00
updated_at: 2026-06-16T23:13:09+09:00
completed_at: 2026-06-16T23:13:09+09:00
status: completed
priority: P1
difficulty: M
est_hours: 5
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-DECISION-FIRST-CONSOLE-IA
tags:
  - ui
  - decision-first
  - ia
---

# TASK-AR-568 - i18n KO/EN UI toggle

## Goal

- UI language toggle over the existing i18n layer (EN data/schema stays); localize inbox/group labels.

## Refs

- Spec: docs/superpowers/specs/2026-06-15-decision-first-console-ia-design.md

## W4a Self Verification

- Added KO/EN i18n resource keys for cockpit, inbox groups/actions/why display labels, and the work-state secondary hero.
- Wired HTML translation anchors for cockpit, drawer, language control, and work-state labels without changing API schema/data identifiers.
- Localized dynamic cockpit rendering in the browser display layer while preserving ids, status values, counts, and raw unknown data.
- Re-rendered cockpit/work-state surfaces when the language toggle changes.
- Verification:
  - `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.
  - `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 12 passed.
  - `PYTHONPATH=src python -m pytest tests/test_ui_state.py -q` -> 103 passed.
  - `PYTHONPATH=src python -m pytest tests/test_attention_inbox.py -q` -> 6 passed.
