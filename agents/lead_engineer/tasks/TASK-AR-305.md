---
id: TASK-AR-305
display_id: TASK-AR-305
task_uid: d273c1a0-c436-49df-a325-5b88a1400d2c
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-11T12:10:00+09:00
title: Add RSI operating-system verification and Owner handoff
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 1000
owner: lead_engineer
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - verification
  - owner-handoff
  - taskset
---

# TASK-AR-305 - Add RSI operating-system verification and Owner handoff

## Goal

- Close the A안 taskset only after the registries, casebook, proposal contract, council metrics, A2A fixture, latent C-mode boundary, and skill layer have direct verification evidence.

## Scope

- Add a named verification wrapper for `TASKSET-AR-RSI-OPERATING-SYSTEM`.
- Run owner-doc, task identity, backlog board, taskset, and focused RSI OS checks.
- Publish an Owner-facing closeout review with remaining watch items.
- Keep implementation closeout separate from this registration review.

## Acceptance Criteria

- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-RSI-OPERATING-SYSTEM --require-complete --check` passes before closeout.
- Owner-facing closeout review lists verification commands and exact status.
- Any remaining C-mode department runtime work is explicitly watch/planned, not implied complete.
- `BACKLOG.md`, `BACKLOG-BOARD.md`, `STATUS.md`, `owner-docs.yml`, and `NEXT-SESSION-POINTER.yml` agree on taskset state.

## Evidence Targets

- `scripts/verify_rsi_operating_system_taskset.py`
- `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-closeout.md`
- `BACKLOG-BOARD.md`

