---
type: brief
id: AGENT_RUNTIME_PM_OPERATING_SYSTEM_BRIEF
audience: owner
status: watch
signal: watch
score: 88
priority: High
tags: [project-management, taskset, model-routing, decomposition]
---

# Agent Runtime PM Operating System Brief

## Bottom Line

- Summary: registered `TASKSET-AR-PM-OPERATING-SYSTEM` to turn high-level planning into detailed worker-ready units.
- Result: future work should flow through `project -> taskset -> task -> unit`, with backlog files acting as metadata indexes rather than full task specifications.
- Boundary: AGENTS rules, research, contract, and taskset registration are complete; executable unit gates and dispatcher changes are planned next.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| PM hierarchy contract | pass | `agents/project/PROJECT-MANAGEMENT-CONTRACT.md` |
| External method research | pass | `reviews/RESEARCH-2026-06-11-agent-runtime-project-management-methods.md` |
| Implementation plan | pass | `docs/superpowers/plans/2026-06-11-project-management-operating-system.md` |
| Taskset registration | pass | `TASK-AR-342` through `TASK-AR-350` |
| Executable gate enforcement | watch | planned, not implemented in this registration pass |

## Insight

- The current board is already taskset-first, but it still treats `TASK-*.md` as the smallest meaningful record.
- Lower-cost worker models need a smaller and more explicit unit: context, target files, scope, acceptance, verification, and stop boundary.
- Planning quality should be concentrated in high-tier planner roles; routine implementation should be cheap only after the planner has made the unit precise.

## Decision

- Decision: use `project -> taskset -> task -> unit` as the canonical PM hierarchy.
- Decision: keep backlog/board metadata compact and move detailed execution instructions into linked specs.
- Decision: add model-tier metadata and readiness gates before dispatching low-tier workers.
- Decision: register executable enforcement as a taskset rather than leaving this as chat guidance.

## Action Board

| Task | Action | Owner | Evidence |
| --- | --- | --- | --- |
| `TASK-AR-342` | Project hierarchy SSoT | planning-office | contract/schema updates |
| `TASK-AR-343` | Unit spec template | lead-engineer | unit README/templates |
| `TASK-AR-344` | Unit readiness gate | agent-runtime-core | gate + tests |
| `TASK-AR-345` | Model-tier routing metadata | planning-office | task/unit metadata |
| `TASK-AR-346` | Dispatcher unit claims | worktree-dispatcher | claim JSON updates |
| `TASK-AR-347` | WIP and flow policy | agent-runtime-core | board/gate metrics |
| `TASK-AR-348` | Board/project hierarchy views | ui-console | board output/tests |
| `TASK-AR-349` | Template propagation | doc-steward | template mirrors |
| `TASK-AR-350` | Verification closeout | lead-engineer | wrapper + review |

## Risks / Blockers

- Risk: extra hierarchy can slow work unless unit templates are quick to fill.
- Risk: lower-cost routing can increase rework if readiness checks are weak.
- Risk: dispatcher edits touch active multi-pane infrastructure and need careful isolation.
- Blocker: none for registration.

## Next Steps

- Start implementation at `TASK-AR-342` or `TASK-AR-343`; do not jump directly to dispatcher changes.
- Keep active RSI OS work pointer intact unless Owner explicitly switches lanes.
- Run `task_unit_readiness_gate` and named taskset verification after implementation exists.

