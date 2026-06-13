---
type: initiative
id: INIT-AR-HOST-FEEDBACK-INTAKE
status: planned
owner: lead_engineer
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
priority: High
task_sets:
  - TASKSET-AR-HOST-FEEDBACK-INTAKE
---

# Host Feedback Intake Initiative

## Purpose

Make host (autofolio) dogfooding feedback a first-class, non-ignorable input
that the platform deliberates and reflects, instead of GitHub issues that pile
up unconsumed. A framework with no real-use host drifts on its own criteria;
consuming host feedback through a live loop is the core of dogfooding.

## Decision

- The intake/deliberation/reply-back loop (TASK-AR-526/527/528) is the canonical
  platform capability and is built regardless of any single feedback item.
- The feedback-derived work items (TASK-AR-529 footprint gate, TASK-AR-530
  self-eval/RSI, TASK-AR-531 host-fit, TASK-AR-532 open bugs) are pre-registered
  as candidates so nothing is lost, but their adopt/defer/reject decision is the
  OUTPUT of the first deliberation cycle — not pre-baked here (GH #131 guardrail:
  no forced rule; recommendation + debate/vote).
- Guardrails: perspective diversity (no same-model false consensus); product
  direction is Owner-only (a majority cannot set product direction — host-owned
  IP); safety/order boundary is always a human (R3); votes are a priority
  signal, never a direction decider.

## Scope

- Host feedback intake + triage classifier (TASK-AR-526).
- Blind-Delphi council/seminar deliberation harness + diversity guardrails
  (TASK-AR-527).
- Decision -> issue reply-back + traceability loop (TASK-AR-528).
- Post-hoc actual-vs-declared footprint verification gate — candidate
  (TASK-AR-529, GH #125).
- Cross-version self-eval harness + RSI fitness gate — candidate
  (TASK-AR-530, GH #128).
- Host-fit gap closures — candidate (TASK-AR-531, GH #121).
- Open BUG triage routing + fixes — candidate (TASK-AR-532, GH #19/#20/#21).

## Out Of Scope

- Pre-deciding which candidate feedback items are adopted (that is the first
  deliberation cycle's job).
- Letting deliberation override the Owner on product direction or safety/order
  boundaries.
- Treating votes as a direction decider rather than a priority signal.

## Source

- GH ycpiglet/agent_runtime#131 (intake pipeline request; this initiative is its
  first test input), #121 (relationship + host-fit), #125 (footprint safety),
  #128 (self-eval/RSI), #19/#20/#21 (open bugs).
- Host counterparts: autofolio `docs/AGENT_RUNTIME_RELATIONSHIP.md`,
  `docs/AGENT_RUNTIME_EVAL_METRICS.md`, `docs/agent_runtime_feedback.md`.
