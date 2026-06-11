---
id: TASK-AR-301
display_id: TASK-AR-301
task_uid: 8a5e638a-7f0c-4528-aaa2-5fb2c07323b0
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-11T12:10:00+09:00
title: Add council review and quantitative proposal metrics
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 1000
owner: diversity-council
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - council
  - metrics
  - review
---

# TASK-AR-301 - Add council review and quantitative proposal metrics

## Goal

- Make the council layer measurable: different viewpoints should improve proposal quality, not add untracked prose.

## Scope

- Define skeptic, advocate, stabilizer, explorer, release-steward, and evaluator verdict fields.
- Add quantitative metrics for proposal precision, accepted-proposal recall, eval regression rate, repeated-failure closure rate, and false-positive proposal rate.
- Ensure council disagreements resolve to pass, watch, block, or no-action with a score.
- Link council outcomes back to proposal IDs and verification records.

## Acceptance Criteria

- Every council verdict has a role, evidence reference, decision, score, and reason.
- Metrics can be computed over accepted, rejected, and deferred proposals.
- A proposal with unresolved block verdicts cannot enter apply-gate execution.
- Diversity viewpoints are preserved as structured data, not only narrative text.

## Evidence Targets

- `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`
- `agents/project/evidence/evaluations/README.md`
- `scripts/planning_loop.py`

