---
id: TASK-AR-556
display_id: TASK-AR-556
task_uid: 94b7419c-b340-4f22-ba4f-4f0b08aa85bc
registered_at: 2026-06-14T11:10:46+09:00
created_at: 2026-06-14T11:10:46+09:00
updated_at: 2026-06-15T13:45:18+09:00
status: completed
resolution: done
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - process-integrity
  - governance
  - closure-gate
  - stop-hook
started_at: 2026-06-15T13:45:18+09:00
completed_at: 2026-06-15T13:45:18+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-546-556.md
  - reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md
---

# TASK-AR-556 - Closure gate: enforce compound/review/retro for substantial work

## Goal

- Make the canonical closure steps (compound / review / retro) **non-skippable** for substantial work, via executable prevention rather than a prose reminder. Forward action #6 from `reviews/RETRO-2026-06-14-agent-runtime-process-integrity.md` (and `COMPOUND-2026-06-14-001`): this session skipped them and broke main.

## Scope

### Input
- `reviews/RETRO-2026-06-14-agent-runtime-process-integrity.md`, `agents/lead_engineer/compound_log.md` (COMPOUND-2026-06-14-001).
- Existing Stop hooks (`scripts/stop_hook_owner_governance.py`, `.codex/hooks.json`).

### Process
- Define "substantial work" (e.g. a merged feature PR / multi-file change touching code) and require linked records before closure: a compound entry when a recurring failure occurred, a closeout review, and a retro when the cycle deviated.
- Implement as a Stop-hook closure gate that blocks closure when substantial work lacks the required records; trivial/conversational turns are exempt. Pair with the merge-gate (branch protection: no merge before green CI) and the "author does not merge own PR" rule (roles.yml).

### Output
- A closure gate script + Stop-hook wiring + tests; a short checklist surfaced at closure time.

## Acceptance Criteria

- Closing substantial work without the required compound/review/retro records is blocked with an actionable message.
- Trivial work is not blocked (no false friction).
- The gate references the canonical cycle (plan→work→verification→compound→review→retro) and is covered by tests.

## Evidence Targets

- The closure gate script + Stop-hook entry + tests.
- Source: `reviews/RETRO-2026-06-14-agent-runtime-process-integrity.md` (forward action #6), `COMPOUND-2026-06-14-001`.
