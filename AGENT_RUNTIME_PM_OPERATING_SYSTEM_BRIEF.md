---
type: brief
id: AGENT_RUNTIME_PM_OPERATING_SYSTEM_BRIEF
audience: owner
status: pass
signal: pass
score: 94
priority: High
tags: [project-management, taskset, model-routing, decomposition]
---

# Agent Runtime PM Operating System Brief

## Bottom Line

- Summary: implemented `TASKSET-AR-PM-OPERATING-SYSTEM` to turn high-level planning into detailed worker-ready units.
- Result: future work should flow through `initiative -> taskset -> task -> unit`, with `project_id` reserved for host/repository lanes and backlog files acting as metadata indexes rather than full task specifications.
- Boundary: AGENTS rules, research, contract, taskset registration, executable unit gates, dispatcher metadata, board view, template propagation, and closeout verification are complete for this taskset.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| PM hierarchy contract | pass | `agents/project/PROJECT-MANAGEMENT-CONTRACT.md` |
| External method research | pass | `reviews/RESEARCH-2026-06-11-agent-runtime-project-management-methods.md` |
| Implementation plan | pass | `docs/superpowers/plans/2026-06-11-project-management-operating-system.md` |
| Taskset registration | pass | `TASK-AR-342` through `TASK-AR-350` |
| Executable gate enforcement | pass | `scripts/task_unit_readiness_gate.py`, `scripts/verify_pm_operating_system_taskset.py` |
| Dispatcher PM metadata | pass | `scripts/taskset_dispatcher.py`, `scripts/task_claim_dispatcher.py` |
| Template propagation | pass | `src/agent_runtime/templates/project/scripts/task_unit_readiness_gate.py` |

## Insight

- The current board is already taskset-first, but it still treats `TASK-*.md` as the smallest meaningful record.
- Lower-cost worker models need a smaller and more explicit unit: context, target files, scope, acceptance, verification, and stop boundary.
- Planning quality should be concentrated in high-tier planner roles; routine implementation should be cheap only after the planner has made the unit precise.

## Decision

- Decision: use `initiative -> taskset -> task -> unit` as the canonical Owner-facing PM hierarchy; keep `project_id` for host/project identity and legacy routing.
- Decision: keep backlog/board metadata compact and move detailed execution instructions into linked specs.
- Decision: use model-tier metadata and readiness gates before dispatching low-tier workers.
- Decision: keep executable enforcement as a taskset-backed runtime contract rather than chat guidance.

## Action Board

| Task | Action | Owner | Evidence |
| --- | --- | --- | --- |
| `TASK-AR-342` | Project hierarchy SSoT | done | contract/schema updates |
| `TASK-AR-343` | Unit spec template | done | unit README/templates |
| `TASK-AR-344` | Unit readiness gate | done | gate + tests |
| `TASK-AR-345` | Model-tier routing metadata | done | task/unit metadata |
| `TASK-AR-346` | Dispatcher unit claims | done | claim JSON updates |
| `TASK-AR-347` | WIP and flow policy | done | board/gate metrics |
| `TASK-AR-348` | Board/project hierarchy views | done | board output/tests |
| `TASK-AR-349` | Template propagation | done | template mirrors |
| `TASK-AR-350` | Verification closeout | done | wrapper + review |

## Risks / Blockers

- Risk: extra hierarchy can slow work unless unit templates are quick to fill.
- Risk: lower-cost routing can increase rework if readiness checks are weak.
- Risk: dispatcher edits touch active multi-pane infrastructure and need careful isolation.
- Blocker: none for PM closeout.

## Next Steps

- Continue the Owner-requested sequence with `TASKSET-AR-VISION-GAP-CLOSURE`.
- Run `task_unit_readiness_gate` before low-tier unit dispatch.
- Run `python scripts/verify_pm_operating_system_taskset.py --check` for PM revalidation.

