---
id: TASK-AR-20260611-2230-UI-STALE-GUARD
display_id: TASK-AR-20260611-2230-UI-STALE-GUARD
task_uid: 22bcdf63-b7df-4691-b2b0-2027e5616005
registered_at: 2026-06-11T22:28:32+09:00
created_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
title: UI stale install and long-running server guard
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-CONSOLE
tags:
  - ui-console
  - doctor
  - stale-process
  - guard
---

# TASK-AR-20260611-2230-UI-STALE-GUARD - UI stale install and long-running server guard

## Goal

- Prevent a stale installed package or old `ui-console` process from hiding current UI changes.

## Scope

- Add `agent_runtime doctor` or equivalent check for non-editable/site-packages imports when running from a checkout.
- Surface git SHA/build source in `/api/state` and visible UI chrome.
- Detect long-running `ui-console` processes on the target port and report restart guidance before claiming UI verification.

## Acceptance Criteria

- A stale install is detectable without reading Python import internals manually.
- The UI shows enough version/source data to compare screen state against the current checkout.
- The guard warns before killing or restarting any process automatically.

## Evidence Targets

- `src/agent_runtime/cli.py`
- `src/agent_runtime/ui_state.py`
- `src/agent_runtime/ui_console.py`
- focused UI/server verification
