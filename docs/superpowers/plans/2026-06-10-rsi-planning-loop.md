# RSI Planning Loop Implementation Plan

## Goal

Register a bounded recursive self-improvement planning loop for `agent_runtime`.
The first implementation path is proposal-first automation, then a gated promotion
path to bounded auto-apply for low-risk planning changes.

## Strategy

- Phase B1: read-only planning scan that compares task state, roadmap, status,
  reviews, evals, traces, releases, and owner docs.
- Phase B2: proposal outbox that writes draft tasks, plan changes, and risk notes
  without mutating canonical docs.
- Phase B3: approval/apply path that reconciles approved proposals into
  `BACKLOG.md`, task files, state machines, and Owner-facing briefs.
- Phase C1: bounded auto-apply only for low-risk planning hygiene where gates,
  budgets, dedupe, trace IDs, and rollback paths exist.
- Phase C2: department/council workflow for competing viewpoints, critique,
  advocacy, release/version integrity, and retro/compound synthesis.
- Phase C3: promotion gate for more autonomous loops after eval, trace, grader,
  owner-doc, state-machine, and release consistency gates pass repeatedly.

## Work Items

1. `TASK-AR-234`: planning loop contract and state machine.
2. `TASK-AR-235`: read-only planning scan JSON.
3. `TASK-AR-236`: proposal outbox and draft task writer.
4. `TASK-AR-237`: planning gate, hook, schedule, and UI trigger integration.
5. `TASK-AR-238`: UI planner panel and proposal review.
6. `TASK-AR-239`: approved proposal apply/verify flow.
7. `TASK-AR-240`: version and release consistency steward.
8. `TASK-AR-241`: review/compound/retro synthesizer.
9. `TASK-AR-242`: agent department and diversity council model.
10. `TASK-AR-243`: trace/eval/grader evidence integration.
11. `TASK-AR-244`: stability, budget, drift, and non-divergence guardrails.
12. `TASK-AR-245`: long-term C-mode promotion gate.

## Guardrails

- No canonical mutation in scan mode.
- No auto-apply for release, version bump, external publication, secret, prod-data,
  destructive, dependency install, or owner-only changes.
- Every proposal needs source refs, trace IDs when available, risk tier, dedupe key,
  affected docs, estimated cost, expected value, rollback path, and verifier list.
- Recursive improvement may create work, critique plans, and propose doc changes;
  it must not weaken its own gates without explicit review.

## Verification

- Regenerate `BACKLOG-BOARD.md`.
- Run owner governance gate and state-machine gate.
- Confirm Owner-facing BRIEF/review entries pass `owner_doc_format_gate.py`.
- Keep the implementation path documented in `AGENT_RUNTIME_RSI_PLANNING_BRIEF.md`
  and `reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md`.
