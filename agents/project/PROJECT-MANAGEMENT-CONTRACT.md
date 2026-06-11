# Project Management Contract

## Purpose

This contract makes work executable by weaker or cheaper implementation models
without losing the intent created by stronger planning models.

## Hierarchy

Owner-facing work uses this hierarchy:

```text
initiative -> taskset -> task -> unit
```

| Level | Purpose | Canonical record | Typical owner |
| --- | --- | --- | --- |
| Workspace / Host Project | Repository, product, customer host, or durable operating lane | `agents/project/PROJECT-CONTEXT.yml` and `agents/project/*.md` | lead-engineer / planning-office |
| Initiative | Outcome-level parent for one or more tasksets | `agents/project/initiatives/<initiative_id>.md` | lead-engineer / planning-office |
| Taskset | Coherent workflow bundle with one completion boundary | `docs/superpowers/plans/<date>-<taskset>.md` plus board metadata | lead-engineer |
| Task | Deliverable with one accountable owner and evidence target | `agents/lead_engineer/tasks/TASK-*.md` | assigned role/team |
| Unit | Smallest executable worker assignment | `agents/lead_engineer/tasks/units/<task_id>/UNIT-*.md` | worker agent |

Backlog and board files are routing surfaces. They should expose metadata,
progress, and links, but they should not carry the full execution context.

`project_id` remains supported for legacy routing and host/project identity.
New Owner-facing planning should use `initiative_id` for the taskset parent so
`project` does not ambiguously mean both the whole repository and a work bundle.

## Owner Request Vocabulary

| Owner phrase | Agent action |
| --- | --- |
| `initiative 작성/등록해줘` | Create or update the parent outcome record and propose tasksets under it |
| `taskset 작성/등록해줘` | Create an executable batch plan and task files under an initiative |
| `task 작성/등록해줘` | Add one canonical task to an existing taskset |
| `unit 작성해줘` | Split one task into worker-ready unit specs with exact scope and verification |

## Metadata Conventions

Use stable IDs in frontmatter so worker models can route without chat history:

| Field | Level | Required when | Example |
| --- | --- | --- | --- |
| `project_id` | project/task/task unit | A task belongs to a durable project or operating-system lane | `PROJECT-AGENT-RUNTIME-PM-OS` |
| `initiative_id` | initiative/taskset/task/task unit | A taskset belongs to an outcome parent above taskset | `INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` |
| `task_set_id` | task/task unit | Any registered taskset work | `TASKSET-AR-PM-OPERATING-SYSTEM` |
| `task_id` | task unit | Any unit spec | `TASK-AR-344` |
| `unit_id` | task unit | Any unit spec | `UNIT-TASK-AR-344-001` |
| `horizon` | project/task | Planning horizon is known | `short`, `medium`, `long`, `unit` |
| `unit_spec` | task/claim | A worker should follow a linked unit spec | `agents/lead_engineer/tasks/units/TASK-AR-344/UNIT-TASK-AR-344-001.md` |
| `planner_model_tier` | task/unit | Planner decomposition is needed or already done | `planner_high` |
| `worker_model_tier` | task/unit | Implementation can be routed to a worker | `worker_low`, `worker_standard` |
| `reviewer_model_tier` | task/unit | Independent verification is required | `reviewer_standard`, `reviewer_high` |
| `escalation_triggers` | task/unit | Low-tier execution must stop or route upward under named conditions | `ambiguity`, `security`, `cross_cutting`, `external_effect`, `repeated_failure` |

Task files may omit some fields during migration. New worker-dispatched units
must not: dispatchers and readiness gates treat missing unit detail as
`planner_refine_required`.

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

