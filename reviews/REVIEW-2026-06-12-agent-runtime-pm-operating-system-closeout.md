---
type: review
id: REVIEW-2026-06-12-agent-runtime-pm-operating-system-closeout
audience: owner
status: pass
signal: pass
score: 94
priority: High
tags: [project-management, taskset, closeout, worker-ready, model-routing]
---

# PM Operating System Closeout Review

## Bottom Line

- Summary: implemented and closed `TASKSET-AR-PM-OPERATING-SYSTEM`.
- Result: project/taskset/task/unit hierarchy now has a worker-ready unit template, unit schema, readiness gate, model-tier routing, dispatcher claim metadata, WIP-aware board output, template propagation, and a focused verification wrapper.
- Boundary: this closeout covers the PM operating-system taskset only; Vision, Ops Feedback, and RSI tasksets remain separate workflow closures.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Hierarchy contract | pass | `agents/project/PROJECT-MANAGEMENT-CONTRACT.md` |
| Unit schema/template | pass | `schemas/task-unit.schema.json`, `agents/lead_engineer/tasks/units/README.md` |
| Readiness gate | pass | `scripts/task_unit_readiness_gate.py`, `tests/test_task_unit_readiness_gate.py` |
| Model routing | pass | `scripts/model_routing.py`, `tests/test_model_routing.py` |
| Dispatcher metadata | pass | `scripts/taskset_dispatcher.py`, `scripts/task_claim_dispatcher.py` |
| Board hierarchy/WIP view | pass | `scripts/backlog_board.py`, `BACKLOG-BOARD.md` |
| Template propagation | pass | `src/agent_runtime/templates/project/scripts/task_unit_readiness_gate.py`, `src/agent_runtime/templates/project/schemas/task-unit.schema.json` |
| Closeout wrapper | pass | `scripts/verify_pm_operating_system_taskset.py` |

## Insight

- The backlog remains a decision index; detailed execution context now lives in linked unit specs.
- Low-tier execution is blocked unless a unit carries context, inputs, target files, scope, acceptance, verification, handoff, and stop boundary.
- Dispatcher claims now carry PM metadata so a worker can recover `project_id`, `unit_id`, model tier, WIP slot, and stop condition from the claim record itself.

## Decision

- Decision: treat `project -> taskset -> task -> unit` as the runtime PM contract.
- Decision: use `planner_refine_required` for units that cannot safely route to a worker.
- Decision: keep concrete provider model names outside task records; route through abstract tiers.

## Action Board

| Task | State | Evidence |
| --- | --- | --- |
| `TASK-AR-342` | done | hierarchy metadata contract |
| `TASK-AR-343` | done | unit README and example unit |
| `TASK-AR-344` | done | readiness gate and tests |
| `TASK-AR-345` | done | model routing helper and tests |
| `TASK-AR-346` | done | dispatcher/claim metadata |
| `TASK-AR-347` | done | WIP metrics from active claim records |
| `TASK-AR-348` | done | project/unit links in board output |
| `TASK-AR-349` | done | host-template mirrors |
| `TASK-AR-350` | done | verification wrapper and this review |

## Risks / Blockers

- Risk: legacy tasks may lack unit specs until migrated; the readiness gate reports this in migration mode instead of breaking all old work at once.
- Risk: WIP age metrics depend on local claim timestamps and do not represent external provider queues.
- Blocker: none for PM taskset closeout.

## Next Steps

- Continue the Owner-requested sequence with `TASKSET-AR-VISION-GAP-CLOSURE`.
- Run `python scripts/verify_pm_operating_system_taskset.py --check` when revalidating PM closeout.
- Use `python scripts/task_unit_readiness_gate.py --task-id <TASK-ID> --require-ready --check` before low-tier worker dispatch.
