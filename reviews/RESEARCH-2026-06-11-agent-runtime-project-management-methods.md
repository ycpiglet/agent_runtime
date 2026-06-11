---
type: research
id: RESEARCH-2026-06-11-agent-runtime-project-management-methods
audience: owner
status: pass
signal: pass
score: 91
priority: High
tags: [project-management, task-decomposition, model-routing, research]
---

# Project Management Methods Research

## Bottom Line

- Summary: the best fit for `agent_runtime` is a hybrid PM model: Linear-style project/task hierarchy, Scrum-style refinement and Definition of Done, Shape Up-style appetite/no-go boundaries, Kanban-style WIP/flow controls, and AI-assisted task splitting with human or high-tier planner oversight.
- Output: this research backs the new `project -> taskset -> task -> unit` contract and `TASKSET-AR-PM-OPERATING-SYSTEM`.
- Boundary: this is method research and registration evidence, not a claim that executable gates are already implemented.

## Signal

| Source | Useful idea | Runtime decision |
| --- | --- | --- |
| Scrum Guide 2020 | Product Backlog is ordered work; refinement breaks items into smaller precise items; Definition of Done controls completion | Keep backlog metadata ordered, but require detailed task/unit specs and verification |
| Shape Up | Set appetite, write pitches with problem/appetite/solution/risks/no-gos, use circuit breakers | Add explicit horizon/appetite, no-go, and scope-stop fields to taskset plans |
| Kanban Guide 2025.5 | Define workflow, WIP control, explicit policies, SLE, and flow metrics | Add WIP and worker-ready policy gates before dispatch |
| Linear Projects docs | Projects are clear outcomes with dates, docs, issues; project lead writes spec and team splits issues | Map `project -> taskset -> task -> unit` and keep taskset plans as specs |
| AI task-splitting research | AI helps produce granular tasks but needs human oversight to filter irrelevant work | Use high-tier planner review before low-tier worker assignment |

## Insight

- Backlog-only management is too shallow for agent execution. It is useful for routing and prioritization, but it does not preserve enough context for lower-capability models.
- The lowest useful execution atom is not a task; it is a unit that contains context, target files, acceptance criteria, verification commands, and stop boundaries.
- Model routing should be encoded as tiers and escalation reasons. Hard-coding a specific model name into task records will age poorly.
- The most important enforcement is not a prettier hierarchy; it is a readiness gate that blocks low-tier dispatch until the unit is precise enough.

## Decision

- Decision: adopt `project -> taskset -> task -> unit` as the canonical hierarchy.
- Decision: treat `BACKLOG.md` and `BACKLOG-BOARD.md` as metadata/index surfaces only.
- Decision: assign planning/decomposition to `planner_high`; assign routine verified units to `worker_low` or `worker_standard`.
- Decision: implement gates that reject worker dispatch when detail specs, model tiers, scope boundaries, or verification evidence are missing.

## Action Board

| Action | Owner | Evidence |
| --- | --- | --- |
| Register PM operating-system taskset | lead-engineer | `TASKSET-AR-PM-OPERATING-SYSTEM` |
| Add hierarchy contract | lead-engineer | `agents/project/PROJECT-MANAGEMENT-CONTRACT.md` |
| Add detailed unit template and gate | agent-runtime-core | planned `TASK-AR-343` / `TASK-AR-344` |
| Add model routing metadata | planning-office | planned `TASK-AR-345` |
| Add WIP/flow enforcement | agent-runtime-core | planned `TASK-AR-347` |

## Risks / Blockers

- Risk: too many hierarchy levels can become ceremony unless gates and templates make them fast to use.
- Risk: low-cost model routing can save tokens but increase rework if readiness criteria are weak.
- Risk: WIP limits need real flow data before SLE values become reliable.
- Blocker: none for research and registration.

## Next Steps

- Implement the unit spec template first, then the readiness gate.
- Extend dispatcher claims only after the unit schema is stable.
- Add board/project views after task metadata and gates are in place.

## Sources

| Source | URL |
| --- | --- |
| Scrum Guide 2020 | https://scrumguides.org/scrum-guide.html |
| Shape Up, Basecamp | https://basecamp.com/shapeup |
| Kanban Guide 2025.5 | https://kanbanguides.org/the-kanban-guide/2025.5/ |
| Linear Projects docs | https://linear.app/docs/projects |
| Pavlic et al., AI task splitting, arXiv 2605.07320 | https://arxiv.org/abs/2605.07320 |

