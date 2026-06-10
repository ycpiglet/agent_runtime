---
completed_at: 2026-06-10T22:56:04+09:00
id: TASK-AR-242
status: completed
verification_status: passed
owner: lead-engineer
priority: P1
difficulty: L
est_hours: 16
est_tokens: 2600
task_set_id: TASKSET-AR-RSI-PLANNING
tags:
  - rsi
  - agent-departments
  - diversity-council
  - governance
audit_log:
  - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
  - agents/project/ORG.md
  - agents/project/TEAMS.md
  - agents/project/PLANNING-LOOP-CONTRACT.md
  - schemas/planning-proposal.schema.json
  - agents/project/PLANNING-GUARDRAILS.yml
  - scripts/planning_loop.py
  - scripts/verify_rsi_planning_taskset.py
  - reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md
  - agents/planning/scans/SCAN-20260610-rsi-planning.json
  - scripts/close_rsi_planning_taskset.py
  - reviews/RSI-PLANNING-TASKSET-VERIFY.json
created: 2026-06-10
---

## Goal

Define an agent department and diversity council model so similar topics are reviewed through different values, temperaments, and operating lenses.

## Scope

- Define departments: planning office, release integrity, RSI lab, evaluation office, risk and safety, diversity council.
- Define viewpoints: skeptic, advocate, explorer, stabilizer, pragmatist, systems thinker, user-impact reviewer, evidence librarian.
- Define debate protocol: independent notes, structured disagreement, premortem, advocate case, skeptic case, synthesis, verdict.
- Avoid role proliferation without clear routing and output contracts.

## Completion Criteria

- `agents/project/ORG.md` and `TEAMS.md` define the departments and boundaries.
- Every department has a canonical context and output type.
- The council protocol preserves disagreement but resolves to pass/watch/block and next action.
- C-mode promotion requires diversity council review for high-impact planning rule changes.

## State Machine Mapping

- cycle: planned
- task: TASK-AR-242 planned
- review: draft
- gate: pending
## RSI Planning Loop Implementation Slice (2026-06-10)

- Implementation evidence: `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md`.
- Runtime path: `scripts/planning_loop.py`.
- Verification wrapper prepared but not run in this slice: `scripts/verify_rsi_planning_taskset.py`.
- Current boundary: implementation is patched and proposal artifacts exist, but task-set completion is pending explicit verification execution.

## RSI Planning Taskset Closeout (2026-06-10T22:53:49+09:00)

- Verification report: `reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Completion boundary: local RSI planning loop implementation, proposal-only B-mode, UI Planner visibility, guardrails, and C-mode blocking.
- External release, remote publication, dependency install, secret/prod-data, destructive changes, and owner-only decisions remain out of scope.
