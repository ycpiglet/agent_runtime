---
id: TASK-AR-514
display_id: TASK-AR-514
task_uid: 5b5f167a-3a1c-4065-8b64-af69e8bba46a
registered_at: 2026-06-12T23:30:00+09:00
created_at: 2026-06-12T23:30:00+09:00
updated_at: 2026-06-12T23:30:00+09:00
title: Conversation-to-work traceability and registration audit
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - governance
  - traceability_gap
tags:
  - planning-record
  - conversation
  - backlog
  - traceability
---

# Conversation-to-work traceability and registration audit

## Goal
- Owner/Claude/Codex planning discussions must map to review records, task records, board rows, and next-session pointers so follow-up work is not hidden in chat.

## Context

- Owner reported that A2A and metadata follow-up discussions were not visible
  enough on `BACKLOG-BOARD.md`.
- Audit record:
  `reviews/MEETING-2026-06-12-work-metadata-a2a-registration-audit.md`.
- Existing planning trigger records hierarchy/workflow talk in `reviews/`, but
  it does not yet prove that every planning discussion has a task/board pointer.

## Scope

- Add a deterministic conversation-to-work audit command or gate that checks:
  review record exists, task records exist when follow-up work is required,
  `BACKLOG-BOARD.md` reflects the taskset, and `NEXT-SESSION-POINTER.yml`
  points to the intended continuation lane.
- Report unmapped planning records as watch/block with source paths.
- Cover Owner/Claude/Codex discussions, not only Codex-authored reviews.
- Keep automatic task creation behind B-mode proposal/approval boundaries.

## Out Of Scope

- Full chat transcript storage policy.
- Automatic backlog mutation from arbitrary conversation without review.

## Acceptance Criteria

- A fixture planning record without task links is reported as watch/block.
- A fixture with review + task + board + pointer links passes.
- `python scripts/owner_governance_gate.py` includes or calls the audit path
  without adding external side effects.

## Evidence Targets

- Audit script/gate + tests.
- Updated planning trigger guidance.
- Closeout review showing the audit catches this exact failure mode.
