---
id: TASK-AR-526
display_id: TASK-AR-526
task_uid: f98765de-5e13-4982-a75d-bcbba475e60d
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
status: planned
priority: P1
difficulty: M
est_hours: 5
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - intake
  - triage
  - dogfooding
---

# TASK-AR-526 - Host feedback intake + triage classifier

## Goal

- Treat host (autofolio) feedback issues as first-class, non-ignorable input: ingest them, classify each into `관계 / 결함 / 설계 / 프로세스`, and queue them for deliberation instead of letting them rot as unconsumed GitHub issues. (GH #131 step 1)

## Scope

- Define an intake source: open issues authored/labelled as host feedback (seed set: #121, #125, #128, #131; bug lane: #19, #20, #21).
- Classify each item into a category (relationship / defect / design / process) and attach a deliberation-queue entry with a stable id, source issue link, and category.
- Make the queue the single Owner-facing surface that says "this host feedback is pending deliberation" (no scatter across chat or ad-hoc notes).

## Acceptance Criteria

- Every seed issue lands in the queue with a category and a back-link to its GitHub issue.
- The queue is re-runnable: re-ingesting does not duplicate already-queued items.
- The classification is auditable (category + reason recorded), not implicit.

## Evidence Targets

- A queue/registry artifact under `agents/project/` (or `agents/runtime/`) holding categorized host-feedback items.
- `reviews/MEETING-2026-06-14-host-feedback-intake-registration.md` (this taskset's registration + deliberation agenda).
- Source: GH ycpiglet/agent_runtime#131 (intake pipeline request), #121/#125/#128 (first inputs).
