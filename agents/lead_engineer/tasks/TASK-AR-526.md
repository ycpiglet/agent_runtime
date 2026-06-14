---
id: TASK-AR-526
display_id: TASK-AR-526
task_uid: f98765de-5e13-4982-a75d-bcbba475e60d
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
started_at: 2026-06-14T09:30:00+09:00
updated_at: 2026-06-14T09:38:00+09:00
completed_at: 2026-06-14T09:38:00+09:00
status: completed
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

## Completion Evidence

- `agents/project/work-items/HOST-FEEDBACK-QUEUE.json`: 7 seed items (4 feedback issues #131/#121/#125/#128 + 3 bugs #21/#20/#19), each classified (relationship/defect/design/process), `status: triage`, back-linked to its GitHub issue + the canonical TASK-AR-NNN.
- `scripts/host_feedback_intake.py`: `--check` (validates schema/unique-ids/category/status/source/title) + `--write` (renders the Owner-facing queue view); re-runnable, idempotent, dedup by id.
- `agents/project/work-items/HOST-FEEDBACK-QUEUE.md`: generated view. `tests/test_host_feedback_intake.py`: 3 tests.

## Verification Results

- W4a: `host_feedback_intake.py --check` findings=0; `pytest tests/test_host_feedback_intake.py` 3 passed; governance gate exit 0.
- W4b (independent, verifier != worker): APPROVE — `reviews/W4B-2026-06-14-TASK-AR-526.md`. All 5 criteria PASS; verifier confirmed all 7 source issues exist + OPEN on GitHub; intake never auto-decides (deliberation owns adoption).
