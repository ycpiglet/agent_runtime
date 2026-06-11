---
id: TASK-AR-300
display_id: TASK-AR-300
task_uid: 6fd3e4b4-ee09-4f63-8288-dcf6b6f27350
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-11T12:10:00+09:00
title: Define evidence-to-proposal engine contract
status: planned
priority: P0
difficulty: L
est_hours: 3
est_tokens: 1200
owner: planning-coordinator
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - proposal-engine
  - planning-loop
  - evidence
---

# TASK-AR-300 - Define evidence-to-proposal engine contract

## Goal

- Define how normalized evidence becomes task, plan, doc, eval, release, or skill proposals without direct canonical mutation.

## Scope

- Create an evidence-to-proposal contract that consumes the evidence inbox, evaluation registry, verification registry, and casebook.
- Extend the existing `planning_loop` proposal model only where current schema cannot express dedupe keys, quantitative confidence, or failure-regression links.
- Keep B-mode proposal-only behavior as the default.
- Define proposal quality scoring before any C-mode promotion.

## Acceptance Criteria

- Proposal records include evidence IDs, dedupe key, affected owner boundary, expected verification command, risk tier, estimated blast radius, and rejection reason when applicable.
- Proposal output can be task, plan, doc, eval, release, skill, or "no action".
- Rejected proposals remain useful as negative examples for precision tracking.
- No proposal engine path writes to canonical backlog/status/task files without the apply gate.

## Evidence Targets

- `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`
- `schemas/planning-proposal.schema.json`
- `scripts/planning_loop.py`

