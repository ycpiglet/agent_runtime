# Project Management Contract

## Purpose

This contract makes work executable by weaker or cheaper implementation models
without losing the intent created by stronger planning models.

## Hierarchy

```text
project -> taskset -> task -> unit
```

| Level | Purpose | Canonical record | Typical owner |
| --- | --- | --- | --- |
| Project | Long/mid/short objective, strategy, horizon, success signal | `agents/project/projects/<project_id>/PROJECT.md` or `agents/project/*.md` | lead-engineer / planning-office |
| Taskset | Coherent workflow bundle with one completion boundary | `docs/superpowers/plans/<date>-<taskset>.md` plus board metadata | lead-engineer |
| Task | Deliverable with one accountable owner and evidence target | `agents/lead_engineer/tasks/TASK-*.md` | assigned role/team |
| Unit | Smallest executable worker assignment | `agents/lead_engineer/tasks/units/<task_id>/UNIT-*.md` | worker agent |

Backlog and board files are routing surfaces. They should expose metadata,
progress, and links, but they should not carry the full execution context.

## Horizon Classes

| Horizon | Scope | Use |
| --- | --- | --- |
| Long | 6+ weeks or release/quarter scale | Vision, durable architecture, multi-taskset roadmap |
| Medium | 2-6 weeks | Feature/project slice, Shape Up-style appetite, milestone |
| Short | 1-2 weeks | Taskset execution plan, sprint/cycle candidate |
| Unit | hours to 1 day | Worker-ready implementation or verification step |

## Model Routing

| Work type | Default tier | Escalate when |
| --- | --- | --- |
| Research synthesis, architecture, risk classification, decomposition | `planner_high` | external policy, security, ambiguous ownership, repeated failure |
| Routine implementation | `worker_low` or `worker_standard` | cross-cutting code, high blast radius, flaky tests, unclear acceptance |
| Verification and audit | `reviewer_standard` | security, release, owner-facing correctness, regression uncertainty |
| Owner decision framing | `planner_high` | irreversible, external, cost-bearing, production, legal, secret boundary |

Concrete provider/model names are resolved by runtime routing. Task records
should store tiers and escalation reasons, not hard-code one vendor model unless
the Owner explicitly asks.

## Worker-Ready Unit Definition

A unit can be assigned to a lower-cost model only when all fields below are
present:

| Field | Required content |
| --- | --- |
| Context | Why this unit exists and which task/taskset/project it serves |
| Inputs | Source docs, code paths, fixtures, prior decisions |
| Target files | Exact likely files or explicit discovery command |
| Scope | In-scope changes and explicit out-of-scope boundaries |
| Steps | Ordered implementation notes when the task is not trivial |
| Acceptance | Observable behavior or document state required |
| Verification | Commands or inspection checks to run |
| Handoff | What to report, what evidence to link, what remains blocked |

If any required field is missing, the unit is `planner_refine_required`, not
worker-ready.

## Operating Rules

1. A planning agent decomposes vague or strategic requests before a worker
   starts implementation.
2. A worker claims one unit, completes it, verifies it, and stops at the unit
   boundary.
3. A worker may ask for clarification only after checking the linked specs and
   local evidence.
4. A completed taskset must stop and report; adjacent tasksets require a new
   claim or Owner/planner-approved continuation.
5. Scope growth creates a new unit or task; it does not silently expand the
   current worker assignment.
6. Backlog entries without linked detail specs are not enough for low-tier
   worker dispatch.

## Enforcement Targets

The PM operating-system taskset must implement executable enforcement for:

| Gate | Rule |
| --- | --- |
| Detail readiness | Every active worker task links a ready unit or equivalent task detail section |
| Model routing | Task/unit metadata declares `planner_model_tier`, `worker_model_tier`, and escalation triggers |
| Scope boundary | Dispatcher claim records project/taskset/task/unit and blocks out-of-scope continuation |
| WIP | Active unit count per taskset/team stays under configured limits |
| Verification | Completion claims include acceptance evidence and runnable checks |

