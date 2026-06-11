---
id: TASK-AR-299
display_id: TASK-AR-299
task_uid: 4a99d83d-eed4-4d80-a768-dace8d7434c3
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-12T02:17:42+09:00
started_at: 2026-06-12T02:17:42+09:00
completed_at: 2026-06-12T02:17:42+09:00
title: Build failure and compound casebook registry
status: completed
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: rsi-lab
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - failure-registry
  - compound
  - regression
---

# TASK-AR-299 - Build failure and compound casebook registry

## Goal

- Convert scattered failure, compound, retro, and review notes into a single searchable casebook that can drive regression fixtures and proposal creation.

## Scope

- Create `agents/project/casebooks/README.md`.
- Create `agents/project/casebooks/failure-and-compound-casebook.md`.
- Define dedupe keys, reproduction commands, owner boundaries, recurrence count, linked regression fixture, and current prevention status.
- Link `agents/lead_engineer/compound_log.md` as the historical source, not the final query surface.

## Acceptance Criteria

- A repeated failure can be looked up by symptom, trigger, owner boundary, or affected gate.
- Each case records whether it has a regression fixture, a gate, a task proposal, or only a note.
- Compound entries that say "needs enforcement" must route to an executable follow-up task or an explicit accepted watch state.

## Evidence Targets

- `agents/project/casebooks/README.md`
- `agents/project/casebooks/failure-and-compound-casebook.md`
- `agents/lead_engineer/compound_log.md`

## Completion Evidence

- Casebook lookup fields, recurrence count, owner boundary, affected gate, regression fixture, and task proposal routing are defined in `agents/project/casebooks/README.md`.
- Seed cases were expanded into detailed case records in `agents/project/casebooks/failure-and-compound-casebook.md`.
- Verification: `pytest tests/test_rsi_operating_system_docs.py tests/test_a2a_lifecycle_gate.py tests/test_planning_loop.py -q` passed.
