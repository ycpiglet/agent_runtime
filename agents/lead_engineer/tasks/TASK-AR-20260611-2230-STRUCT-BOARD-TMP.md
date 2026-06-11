---
id: TASK-AR-20260611-2230-STRUCT-BOARD-TMP
display_id: TASK-AR-20260611-2230-STRUCT-BOARD-TMP
task_uid: 3f71b2b6-375d-45a4-8d6d-8f7ed7c6840c
registered_at: 2026-06-11T22:28:32+09:00
created_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
title: Board/template drift gate and temporary artifact lifecycle
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 3500
owner: lead_engineer
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - structure
  - backlog
  - template
  - tmp
---

# TASK-AR-20260611-2230-STRUCT-BOARD-TMP - Board/template drift gate and temporary artifact lifecycle

## Goal

- Prevent live/template backlog board drift and make `.tmp` retention predictable without losing preservation artifacts.

## Scope

- Add a gate that detects drift between live `scripts/backlog_board.py` and the host template copy when taskset definitions change.
- Clarify `BACKLOG.md` as narrative registry and `BACKLOG-BOARD.md` as generated board.
- Define `.tmp` classes: disposable cache, verification output, preservation archive, and active server log.

## Acceptance Criteria

- A changed taskset registry requires live and template board definitions to stay aligned.
- `.tmp` cleanup instructions preserve dirty-intake archives and active server logs.
- Board regeneration remains the only accepted path for `BACKLOG-BOARD.md` content changes.

## Evidence Targets

- `scripts/backlog_board.py`
- `src/agent_runtime/templates/project/scripts/backlog_board.py`
- `scripts/dirty_intake.py`
