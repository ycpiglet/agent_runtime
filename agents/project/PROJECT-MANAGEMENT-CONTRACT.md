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
| `milestone` | initiative/taskset/task | Work maps to a release, demo, or date-bound goal | `v0.1.9`, `demo-day` |
| `team` | task/unit | Ownership, workload, or reporting axis is needed | `agent-runtime-core` |
| `unit_spec` | task/claim | A worker should follow a linked unit spec | `agents/lead_engineer/tasks/units/TASK-AR-344/UNIT-TASK-AR-344-001.md` |
| `planner_model_tier` | task/unit | Planner decomposition is needed or already done | `planner_high` |
| `worker_model_tier` | task/unit | Implementation can be routed to a worker | `worker_low`, `worker_standard` |
| `reviewer_model_tier` | task/unit | Independent verification is required | `reviewer_standard`, `reviewer_high` |
| `escalation_triggers` | task/unit | Low-tier execution must stop or route upward under named conditions | `ambiguity`, `security`, `cross_cutting`, `external_effect`, `repeated_failure` |

Task files may omit some fields during migration. New worker-dispatched units
must not: dispatchers and readiness gates treat missing unit detail as
`planner_refine_required`.

## Numbering And Classification

There are three distinct identifiers; do not conflate them (TASK-AR-535):

1. **Stable key (canonical identity)** — `task_uid`, a UUID (UUIDv7/ULID for new
   records; UUIDv4 legacy keys remain valid). This is the only canonical identity;
   it never changes and is what attribution, claims, and evidence bind to.
2. **Human-facing number** — the generated hierarchy ordinal
   `Initiative 1 -> Taskset 1.1 -> Task 1.1.1 -> Unit 1.1.1.1`, rendered by
   `scripts/work_item_classifier.py`. This is the official number to cite in
   Owner-facing discussion. It is contiguous and recomputed, so it has no gaps.
3. **Display key** — `display_id` / `TASK-AR-NNN`, a convenience label.

**`TASK-AR-NNN` gaps are cosmetic and expected.** Gaps (e.g. no 100s/400s, the
200/300/500 blocks) are an inherent property of any central sequence — Postgres
and MySQL document that sequences cannot be gapless; Jira keys and Stripe invoice
numbers separate an opaque stable key from a derived display number for exactly
this reason. **Gaps are never backfilled and carry no meaning.** New
`TASK-AR-NNN` are allocated **contiguously from `max+1`** (no reserved blocks,
no "quantum jumps"); reservation of a vanity `TASK-AR-NNN` is optional, not on
the hot path (see TASK-AR-536). When a contiguous label is unavailable under
concurrency, the `TASK-AR-<timestamp>-<hex8>` form is a first-class equivalent.

Use `scripts/work_item_classifier.py --write` after hierarchy metadata changes
and `--check` in governance and before handoff. `0.*` ordinals are legacy or
unassigned work that predates `initiative_id`; add `initiative_id` when that
work is next touched.

## Triage Intake State (TASK-AR-538)

`status: triage` (alias `intake`) is an intake state, NOT active work. Triage
items are held OUT of the Active board, surfaced in a dedicated `## Triage`
inbox on `BACKLOG-BOARD.md`, and counted in the board's `Needs attention`
rollup. Transitions: **accept** -> `planned`/`backlog` (enters active work) or
**defer** -> a someday parking lot. Host feedback enters via this state
(`HOST-FEEDBACK-QUEUE.json` uses the same `triage -> accepted/deferred/rejected`
vocabulary, TASK-AR-526). This is a status FIELD + view, not a directory move
(single store + status + views; see the work-store restructure initiative).

## Orthogonal Axes And Non-Tree Work

Milestone, horizon, team, owner, role, priority, and phase are orthogonal axes,
not hierarchy levels. Keep them as metadata so one taskset can report to a
release, a team, and a horizon without breaking the tree.

Two work types may live outside the goal-oriented tree:

| Type | Use | Record shape |
| --- | --- | --- |
| Routine | Recurring operational work such as log rotation, daily briefs, board regeneration, or idea-vault scans | `agents/lead_engineer/routines/ROUTINE-*.md` plus schedule/trigger metadata |
| Spike | Time-boxed research or experiment whose output is a decision, not necessarily implementation | Task or unit with `type: spike`, timebox, decision output, and stop boundary |

Display skins may rename the same data model without changing canonical fields:
`Initiative=Saga`, `Taskset=Quest`, `Task=Mission`, `Unit=Step`.

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
7. Planning discussions and hierarchy/numbering decisions must be recorded in
   `reviews/` before closeout; chat-only planning is not durable state.

## Enforcement Targets

The PM operating-system taskset must implement executable enforcement for:

| Gate | Rule |
| --- | --- |
| Detail readiness | Every active worker task links a ready unit or equivalent task detail section |
| Model routing | Task/unit metadata declares `planner_model_tier`, `worker_model_tier`, and escalation triggers |
| Scope boundary | Dispatcher claim records project/taskset/task/unit and blocks out-of-scope continuation |
| WIP | Active unit count per taskset/team stays under configured limits |
| Verification | Completion claims include acceptance evidence and runnable checks |
| Classification | Work-item classifier output is current and no orphan unit points to a missing task |

