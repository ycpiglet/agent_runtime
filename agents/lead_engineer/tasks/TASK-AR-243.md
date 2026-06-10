---
id: TASK-AR-243
status: completed
completed_at: 2026-06-10T23:22:00+09:00
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 16
est_tokens: 3000
task_set_id: TASKSET-AR-QUALITY-LOOP
tags:
  - rsi
  - trace-grading
  - offline-eval
  - quality-gate
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
  - scripts/planning_evidence_link.py
  - tests/test_planning_evidence_link.py
  - reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json
  - reviews/REVIEW-2026-06-10-agent-runtime-task-ar-243-planning-evidence-link.md
created: 2026-06-10
---

## Goal

Connect trace, grader, eval, correction, live-review, and A2A evidence to planning proposals and acceptance criteria.

## Scope

- Normalize trace/eval/grader evidence into planning scan inputs.
- Map failed trace graders to proposal categories and task acceptance criteria.
- Link correction collector and live reviewer outputs to planning proposals.
- Use A2A `contextId`/`taskId` continuity for multi-cycle proposal lineage.

## Completion Criteria

- Planning scan can ingest local eval/correction/A2A artifacts and future trace records.
- Proposal records cite trace/eval/grader IDs when available.
- Eval regressions create watch/block proposals based on severity and recurrence.
- Tests cover trace evidence, grader output, correction proposal, and missing trace cases.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-243 completed
- gate: watch
- review: completed

## Completion Log (2026-06-10)

- Added executable linker: `scripts/planning_evidence_link.py`.
- Added regression tests: `tests/test_planning_evidence_link.py`.
- Generated final planning evidence report: `reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json`.
- Report result: `status=watch`, `proposal_count=2`; the watch proposals are correction proposals requiring owner approval, not release blockers.
- Closeout review: `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-243-planning-evidence-link.md`.
- Boundary: the linker creates proposal records and does not mutate canonical definitions or approve corrections.
