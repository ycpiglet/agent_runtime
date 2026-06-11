---
id: TASK-AR-304
display_id: TASK-AR-304
task_uid: 023a2874-3b90-47ee-810d-913a5d348b63
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-11T12:10:00+09:00
title: Package RSI operating-system skill layer
status: planned
priority: P1
difficulty: L
est_hours: 3
est_tokens: 1200
owner: lead_engineer
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - skill
  - failure-to-regression
  - session-continuity
---

# TASK-AR-304 - Package RSI operating-system skill layer

## Goal

- Add the missing skill layer so future sessions follow the RSI operating process without rediscovering it from scattered scripts and reviews.

## Scope

- Add or update `skills/rsi-planning-loop/SKILL.md`.
- Add `skills/failure-to-regression/SKILL.md`.
- Reconcile the existing `skills/session-closeout/` scope with a future `parallel-session-closeout` or pointer skill if duplication appears.
- Keep skills concise and route to scripts, registries, and gates rather than re-embedding long process text.

## Acceptance Criteria

- Skills state when to use them and which scripts/docs to read first.
- Failure-to-regression flow requires a casebook entry, a reproduction command or explicit non-repro reason, and a gate or task proposal.
- RSI planning skill routes through evidence inbox, proposal engine, council review, and apply gate.
- Session/parallel closeout behavior stays consistent with the existing closeout automation taskset.

## Evidence Targets

- `skills/rsi-planning-loop/SKILL.md`
- `skills/failure-to-regression/SKILL.md`
- `skills/session-closeout/SKILL.md`

