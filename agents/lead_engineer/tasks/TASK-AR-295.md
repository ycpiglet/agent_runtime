---
id: TASK-AR-295
display_id: TASK-AR-295
task_uid: b75fac0b-3f44-4b4d-96a1-98288a7c591f
registered_at: 2026-06-11T02:30:00+09:00
created_at: 2026-06-11T02:30:00+09:00
started_at: 2026-06-11T11:53:49+09:00
updated_at: 2026-06-11T11:53:49+09:00
completed_at: 2026-06-11T11:53:49+09:00
title: Wire closeout hooks and Owner-doc preflight
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION
tags:
  - hook
  - session-start
  - stop
  - owner-doc
---

# TASK-AR-295 - Wire closeout hooks and Owner-doc preflight

## Goal

- Wire the baseline and dirty-intake scripts into session lifecycle hooks without adding unsafe hidden side effects.

## Scope

- Update `.codex/hooks.json` to run baseline capture on SessionStart.
- Add a Stop hook that blocks completion claims when dirty-intake reports unresolved residue.
- Add fast Owner-doc preflight for manifest-listed docs after edits where supported.
- Keep the existing Owner governance Stop hook authoritative.

## Acceptance Criteria

- Hook commands use the verified Python interpreter path for this Windows environment.
- Stop hook output distinguishes block, watch, and preserved/archive states.
- Hook changes are tested directly with sample payloads and documented as requiring a fresh session to load.
- Owner-doc preflight catches missing `Risks / Blockers` or `Next Steps` before final Stop.

## Evidence Targets

- `.codex/hooks.json`
- `scripts/dirty_intake.py`
- `scripts/session_baseline.py`
- `tests/test_stop_hook_owner_governance.py`
- `tests/test_owner_doc_format_gate.py`
