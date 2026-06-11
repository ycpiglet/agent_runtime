---
id: TASK-AR-298
display_id: TASK-AR-298
task_uid: 7b4e4dc4-915f-49e5-af8d-5a18dfd66130
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
started_at: 2026-06-11T13:14:53+09:00
completed_at: 2026-06-11T13:16:20+09:00
updated_at: 2026-06-11T13:16:20+09:00
title: Create evaluation and verification record registry
status: completed
priority: P0
difficulty: M
est_hours: 2
est_tokens: 900
owner: evaluation-office
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - eval
  - verification
  - metrics
---

# TASK-AR-298 - Create evaluation and verification record registry

## Goal

- Make evaluation and verification evidence queryable instead of scattered across reviews, JSON reports, and ad hoc command output.

## Scope

- Define `agents/project/evidence/evaluations/` for eval, grader, prediction-score, and regression records.
- Define `agents/project/evidence/verification/` for gate runs, verification commands, expected outputs, and failure reasons.
- Specify quantitative RSI quality fields: proposal precision, proposal recall, eval regression rate, repeated-failure closure rate, and evidence-to-task latency.
- Link existing reports such as `reviews/RSI-PLANNING-TASKSET-VERIFY.json` and `reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json` as seed examples.

## Acceptance Criteria

- Registry docs explain how to add a new evaluation or verification record.
- Each record can identify the command or source that produced it.
- Metrics distinguish deterministic local gates from provider-live or remote evidence.
- Future proposal scoring can consume these records without scraping free-form reviews first.

## Evidence Targets

- `agents/project/evidence/evaluations/README.md`
- `agents/project/evidence/verification/README.md`
- `AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF.md`
