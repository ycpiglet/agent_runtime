---
id: TASK-AR-302
display_id: TASK-AR-302
task_uid: 0f90a9b0-18f2-4ac9-9b56-652c3e7e1242
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-12T02:17:42+09:00
started_at: 2026-06-12T02:17:42+09:00
completed_at: 2026-06-12T02:17:42+09:00
title: Verify A2A message lifecycle as planning evidence
status: completed
priority: P1
difficulty: L
est_hours: 3
est_tokens: 1200
owner: evaluation-office
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - a2a
  - trace
  - verification
---

# TASK-AR-302 - Verify A2A message lifecycle as planning evidence

## Goal

- Close the gap between A2A evidence fields existing in documents and an actual end-to-end message lifecycle being verified.

## Scope

- Add a minimal A2A lifecycle fixture that covers request, review, decision, correction, and proposal routing.
- Ensure lifecycle records include context ID, task ID, actor role, access boundary, retry/idempotency marker, and final reconstruction result.
- Feed the verified lifecycle record into the evidence inbox rather than bypassing it.
- Keep provider-live or external message transport out of scope until local deterministic fixtures pass.

## Acceptance Criteria

- A local deterministic command can reconstruct the lifecycle chain and produce pass/watch/block output.
- Missing request, review, decision, or correction events produce a block finding.
- The planning loop can cite an A2A lifecycle record as evidence for a proposal.
- The review record distinguishes "documented A2A shape" from "verified lifecycle execution".

## Evidence Targets

- `agents/project/evidence/inbox/README.md`
- `scripts/a2a_lifecycle_gate.py`
- `tests/test_a2a_lifecycle_gate.py`

## Completion Evidence

- Added deterministic lifecycle fixture: `agents/project/evidence/a2a/A2A-LIFECYCLE-2026-06-12.json`.
- Added `scripts/a2a_lifecycle_gate.py`; missing request/review/decision/correction/proposal-routing events block the gate.
- Verification: `python scripts/a2a_lifecycle_gate.py --check` passed and `tests/test_a2a_lifecycle_gate.py` covers a missing decision block case.
