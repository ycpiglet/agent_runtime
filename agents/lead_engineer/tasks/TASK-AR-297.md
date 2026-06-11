---
id: TASK-AR-297
display_id: TASK-AR-297
task_uid: 1570ec36-9aa1-4b83-bd62-ca6478e8d11e
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
started_at: 2026-06-11T13:10:53+09:00
completed_at: 2026-06-11T13:12:23+09:00
updated_at: 2026-06-11T13:12:23+09:00
title: Register evidence inbox and conversation capture contract
status: completed
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - evidence
  - conversation-record
  - governance
---

# TASK-AR-297 - Register evidence inbox and conversation capture contract

## Goal

- Create the canonical place to capture trace, eval, grader, A2A, correction, review, retro, failure, compound, and Owner conversation evidence before it becomes a proposal.

## Scope

- Promote `agents/project/evidence/README.md` as the evidence registry entrypoint.
- Define `agents/project/evidence/inbox/` as the landing zone for normalized evidence records.
- Record the 2026-06-11 RSI operating-system registration conversation in `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md`.
- Keep raw chat summaries as evidence, not as direct implementation authority.

## Acceptance Criteria

- Evidence records define source type, source path, task/taskset link, observed failure or signal, owner boundary, and proposed routing.
- The conversation record states the Owner request: record this dialogue, add evaluation/verification record management, add failure/compound casebooks, preserve C as a latent future option, and register A as a taskset.
- The inbox contract routes evidence to proposal generation only after dedupe and quality checks.

## Evidence Targets

- `agents/project/evidence/README.md`
- `agents/project/evidence/inbox/README.md`
- `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md`
