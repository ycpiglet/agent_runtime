---
type: brief
id: AGENT_RUNTIME_RSI_PLANNING_BRIEF
audience: owner
status: watch
signal: watch
score: 82
priority: High
tags: [rsi, planning-loop, self-improvement, owner-brief]
---

# Agent Runtime RSI Planning Loop Brief

## Bottom Line

- Summary: registered the B-C long-term planning path for bounded recursive self-improvement.
- Result: `TASK-AR-234` through `TASK-AR-245` define the path from read-only planning scan to C-mode promotion gate.
- Boundary: the system may autonomously scan and propose, but canonical mutation stays gated until apply/verify rules exist.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| B path | watch | proposal-first loop: scan, proposal outbox, planning gate, UI review, approved apply |
| C path | watch | bounded auto-planning only after trace/eval/grader and stability gates pass repeatedly |
| Research grounding | pass | OpenAI trace/eval/grader, Codex automations/safety, A2A, hooks, NIST AI RMF, RSI, STOP, premortem, Delphi, double-loop learning |
| Project fit | pass | existing tasks, state machines, Owner BRIEFs, eval/correction/A2A evidence, and UI outbox provide the substrate |
| Parallel execution fit | pass | per-task worktrees and `task_claim` state keep worker edits isolated while allowing role instances such as `lead-engineer-A/B/C` |
| Risk posture | watch | no self-weakening gates, no release/version mutation, no external action, no destructive action without explicit approval |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Planned | Define planning loop contract/state machine | lead-engineer | planning-coordinator | `TASK-AR-234` |
| Planned | Add read-only planning scan JSON | lead-engineer | planning-coordinator | `TASK-AR-235` |
| Planned | Add proposal outbox/draft writer | lead-engineer | task-architect | `TASK-AR-236` |
| Planned | Add planning gate/hook/schedule/UI trigger | lead-engineer | risk-controller | `TASK-AR-237` |
| Planned | Add UI planner panel | lead-engineer | ui-runtime-operator | `TASK-AR-238` |
| Planned | Add approved proposal apply/verify | lead-engineer | planning-coordinator | `TASK-AR-239` |
| Planned | Add version/release consistency steward | release-integrity | version-steward | `TASK-AR-240` |
| Planned | Add review/compound/retro synthesizer | rsi-lab | retro-synthesizer | `TASK-AR-241` |
| Planned | Add diverse agent departments/council | diversity-council | council-facilitator | `TASK-AR-242` |
| Planned | Connect trace/eval/grader evidence | evaluation-office | trace-analyst | `TASK-AR-243` |
| Planned | Add stability/non-divergence guardrails | risk-and-safety | drift-guard | `TASK-AR-244` |
| Planned | Define C-mode promotion gate | lead-engineer | release-governor | `TASK-AR-245` |
| Planned | Add parallel worktree dispatcher/claim helpers | lead-engineer | worktree-dispatcher | `TASK-AR-246` |

## Risks / Blockers

- Risk: RSI can create low-value churn if proposal count, dedupe, evidence quality, and budget caps are not enforced.
- Risk: diversity roles can become noise unless every critique resolves to a structured verdict and next action.
- Risk: auto-planning can weaken release/version discipline if `TASK-AR-240` is not implemented before C-mode promotion.
- Risk: same-checkout parallel terminals can mix file edits and git index state unless `TASK-AR-246` claim/worktree discipline is enforced.
- Blocker: none for registration; implementation must start in proposal-only B-mode.

## Insight

- A second Codex pane is useful for visibility but should not be the architecture. The durable architecture is a repo-local planning loop with state, outbox, gates, and UI review.
- The existing runtime already has the right primitives: task frontmatter, reviews, Owner BRIEFs, state machines, eval/correction/A2A artifacts, `.ui_outbox`, and governance gates.
- Parallelism should be a dispatcher/runtime concern, not a terminal habit: the main checkout orchestrates; workers run in task worktrees with task claims.
- Productive RSI here means double-loop planning: improve tasks and plans, then occasionally improve the rules that create tasks and plans, under gate protection.
- Trace/eval/grader evidence should trigger task proposals when it shows regressions, repeated failure modes, missing acceptance criteria, or weak source grounding.

## Decision

- Decision: adopt B first, C later.
- Decision: create many-agent departments for planning, release integrity, RSI lab, evaluation evidence, risk/stability, and viewpoint diversity.
- Decision: treat `planning_loop` and `rsi_improvement` as state-machine domains before implementation.
- Decision: no automatic release/version/external/destructive/prod-data changes inside RSI loops.

## Next Steps

1. Start `TASK-AR-234` and define the planning loop state machine plus proposal schema.
2. Implement `TASK-AR-235` read-only scan before any mutating proposal writer.
3. Keep all canonical changes behind `TASK-AR-239` approval/apply/verify until C-mode promotion is explicitly earned.

## RSI Planning Loop Implementation Path (2026-06-10)

- Contract: `agents/project/PLANNING-LOOP-CONTRACT.md`.
- Schema: `schemas/planning-proposal.schema.json`.
- Guardrails: `agents/project/PLANNING-GUARDRAILS.yml`.
- C-mode checklist: `agents/project/C-MODE-PROMOTION-CHECKLIST.md`.
- Council protocol: `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`.
- Runtime path: `scripts/planning_loop.py` supports read-only scan, proposal outbox, draft task writer, planning gate, approved apply skeleton, retro synthesis, trace/eval ingestion, and C-mode gate.
- Release steward path: `scripts/release_version_consistency_steward.py` emits proposal-only release/version consistency reports.
- UI path: `planning.scan` command requests and the read-only Planner panel expose scan/proposal/request/draft/apply records without canonical mutation.
- Review: `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md`.

## Verification and Closeout Procedure

- Verification command: `python scripts/verify_rsi_planning_taskset.py --out reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Closeout dry run: `python scripts/close_rsi_planning_taskset.py --verification-report reviews/RSI-PLANNING-TASKSET-VERIFY.json --json`.
- Closeout apply after verification pass: `python scripts/close_rsi_planning_taskset.py --verification-report reviews/RSI-PLANNING-TASKSET-VERIFY.json --apply --json`.
- Final completion proof: closeout apply must report `status=pass`, including backlog board regeneration, named task-set require-complete gate, and owner governance gate.
- Boundary: no completion claim before this procedure passes.
