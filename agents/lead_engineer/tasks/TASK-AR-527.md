---
id: TASK-AR-527
display_id: TASK-AR-527
task_uid: 92a2232e-5142-4532-85ba-cefb3704f177
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
started_at: 2026-06-14T10:00:00+09:00
updated_at: 2026-06-14T10:10:00+09:00
completed_at: 2026-06-14T10:10:00+09:00
status: completed
priority: P1
difficulty: L
est_hours: 8
est_tokens: 7000
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - council
  - seminar
  - blind-delphi
  - guardrails
---

# TASK-AR-527 - Blind-Delphi council/seminar deliberation harness + diversity guardrails

## Goal

- Reactivate the currently-dormant council/seminar device so queued host feedback is actually deliberated (심의 → 합의), using blind Delphi to mitigate groupthink, with hard guardrails so deliberation informs but never overrides the Owner. (GH #131 steps 2-3)

## Scope

- Run a queued item through the diversity council (see `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`) and/or a seminar record, producing independent notes before synthesis (blind Delphi: collect viewpoints before cross-exposure).
- Encode guardrails: (a) perspective diversity to prevent same-model false consensus; (b) product direction is Owner-only — a majority cannot set product direction (host-owned IP); (c) safety / order boundary is always a human (R3).
- Output a structured verdict per the protocol's verdict fields (`decision: pass|watch|block|no_action`, score, reason, owner_boundary, minority concerns).

## Acceptance Criteria

- A deliberation produces a council/seminar record with participating viewpoints, minority concerns, and a verdict — not a single-voice opinion.
- Guardrails are explicit in the record: vote is a priority signal, not a direction decider; Owner boundary and safety/R3 boundary are stated.
- The harness is repeatable for any queued item, not a one-off.

## Acceptance Criteria — boundary

- This is the deliberation *capability*. Which feedback items get adopted/deferred/rejected is decided by running this harness (see TASK-AR-529/530/531/532 candidates), not pre-baked here.

## Evidence Targets

- A council/seminar record under `reviews/` for the first deliberation cycle.
- `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md` (viewpoints + verdict contract referenced).
- Source: GH ycpiglet/agent_runtime#131 (deliberation + guardrails).

## Completion Evidence

- First blind-Delphi deliberation run: 5 independent viewpoints (skeptic, pragmatist, systems-thinker, user-impact-reviewer, stabilizer) evaluated the 4 candidates without seeing each other, then synthesis. Record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md` (per DIVERSITY-COUNCIL-PROTOCOL output contract: candidate ids, viewpoints, minority concerns, per-candidate verdict + priority, guardrails, next action + owner boundary).
- Guardrails enforced: vote = priority signal (not direction); Owner alone decides product direction; safety/order = human (R3).
- Outcomes written back to `agents/project/work-items/HOST-FEEDBACK-QUEUE.json` (triage -> accepted with verdict + priority). The deliberation materially changed candidate scope (529 block flag-gated; 530 RSI gate advisory; 531 work_cli rejected as already-built; 532 verify-first as #21/#20 appear already fixed).
- Repeatable: re-run the council for the next intake batch (the consumption end of the GH #131 pipeline).

## Verification Results

- W4a: HOST-FEEDBACK-QUEUE check passes; owner_doc_format_gate green on the council record; governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-527.md` — verifies the record against the council protocol output contract, blind-Delphi divergence, explicit guardrails, queue consistency, and that the deliberation changed scope (not theater).
