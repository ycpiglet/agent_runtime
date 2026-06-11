---
id: TASK-AR-20260611-2230-STRUCT-HOOK-LOGS
display_id: TASK-AR-20260611-2230-STRUCT-HOOK-LOGS
task_uid: 493e8b6a-01d1-4905-b522-bf2f33763a5f
registered_at: 2026-06-11T22:28:32+09:00
created_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
title: Hook/runtime log SSoT and rotation policy
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-REPO-HYGIENE
tags:
  - structure
  - hook
  - logs
  - rotation
---

# TASK-AR-20260611-2230-STRUCT-HOOK-LOGS - Hook/runtime log SSoT and rotation policy

## Goal

- Unify hook/runtime log ownership so closeout, dirty-intake, and owner governance read one canonical log policy instead of split `.codex` and `agents/runtime` conventions.

## Scope

- Decide the canonical hook log destination and document what remains local-only.
- Add or update a rotation/retention command for ignored hook logs.
- Ensure stop-hook dirty-intake can distinguish real work residue from log-only residue.

## Acceptance Criteria

- The canonical log destination and retention rule are documented.
- Rotation can be run without deleting preserved evidence.
- Dirty-intake reports log-only residue as watch/log-only, not archive-required.

## Evidence Targets

- `scripts/dirty_intake.py`
- `.codex/hooks.json`
- `agents/runtime/hook-logs/` policy docs or generated retention notes
