---
id: TASK-AR-528
display_id: TASK-AR-528
task_uid: 93e48db2-bbb5-4dc7-b0f0-90ea1dbd2a63
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
started_at: 2026-06-14T13:10:00+09:00
updated_at: 2026-06-14T13:20:00+09:00
status: in_progress
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

## Progress / Owner-gated step

- DELIVERED (local): `scripts/host_feedback_replyback.py` (`--check`/`--write-drafts`/`--post`) reads the queue verdicts and renders one traceable reply per source issue (decision + priority + rationale + deliberation-record link + guardrails). `--check` findings=0; 7 drafts in `agents/project/work-items/HOST-FEEDBACK-REPLIES.md`. Traceability is bidirectional: issue <-> queue entry <-> COUNCIL record <-> task.
- PENDING (owner-gated): the actual `gh issue comment` POST to #121/#125/#128/#131 + #19/#20/#21 is an outbound external write and was correctly blocked by the action classifier ("proceed with 528" does not authorize posting to those external destinations). The Owner closes the loop with one command: `python scripts/host_feedback_replyback.py --post` (or add a Bash permission rule). Status stays `in_progress` until the reply is posted.

## Verification Results

- W4a: `--check` findings=0; drafts render accurately from the queue verdicts; governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-528.md` (verifies the mechanism + draft accuracy; the post itself is owner-gated).
