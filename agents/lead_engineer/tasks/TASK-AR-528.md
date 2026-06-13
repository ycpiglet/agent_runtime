---
id: TASK-AR-528
display_id: TASK-AR-528
task_uid: 93e48db2-bbb5-4dc7-b0f0-90ea1dbd2a63
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
status: planned
priority: P2
difficulty: M
est_hours: 4
est_tokens: 3500
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - reply-back
  - traceability
---

# TASK-AR-528 - Decision -> issue reply-back + traceability loop

## Goal

- Close the loop so a deliberation outcome is written back to the originating host issue with its rationale, making the host able to track adoption/deferral/rejection. The consumption end (심의·반영) must actually run, or the intake is useless. (GH #131 step 4)

## Scope

- For each deliberated item, post the decision (채택 / 보류 / 기각) + grounded reason + evidence references back to the GitHub issue (e.g., `gh issue comment`), and link the council/seminar record.
- Keep traceability bidirectional: issue <-> queue entry <-> deliberation record <-> any spawned task.
- Treat votes/priority as a *priority signal* for sequencing, never as the product-direction decider (guardrail mirrors TASK-AR-527).

## Acceptance Criteria

- A deliberated seed issue receives a reply with decision + reason + record link.
- The decision is traceable from the issue to the deliberation record and back.
- Reply-back is idempotent/append-only (re-running does not spam duplicate verdicts).

## Evidence Targets

- A reply-back on at least one seed issue (#121/#125/#128/#131) referencing the deliberation record.
- The intake queue entry updated with the final decision.
- Source: GH ycpiglet/agent_runtime#131 (반영·회신).
