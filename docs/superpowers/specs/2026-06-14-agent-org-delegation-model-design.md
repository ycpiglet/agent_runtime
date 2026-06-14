# Agent Org & Delegation Model — Design

- **Date:** 2026-06-14
- **Status:** approved (Owner, 2026-06-14)
- **Owner:** managing_partner (Director)
- **Topic:** Real lead→worker delegation: operationalize the org model the work-schema already implies.

## Bottom Line

The runtime already has the *mechanism* for a multi-role agent org (roles, instances,
`team_id`, `parent_instance_id`, claims, leases, worktrees, dispatchers) and the
work-schema already defines the *hierarchy* (`initiative → taskset → task → unit`) and
the *tiers* (`planner / worker / reviewer`). It is simply not operationalized: ~90% of
tasks are owned by `lead_engineer` (free-text, inconsistently spelled), and **a claim
existing does not cause a worker to run** — today a human opens a pane and runs the agent
manually. This design closes that gap with a 4-role org, risk-based hybrid dispatch, and a
**swappable worker-execution backend** (Agent-tool sub-agents now; headless daemon later)
behind a stable claim/instance/lease contract. Token/cost discipline is a first-class
constraint, not an afterthought.

## Problem / Context

- **Centralization:** 189/~210 work items owned by `lead_engineer` / `lead-engineer`.
  `owner` is free-text, not bound to a role registry. Only `agents/lead_engineer/` is a
  real doer dir. The Lead effectively acts as planner + worker + reviewer simultaneously.
- **Latent model:** `WORK-SCHEMA.yml` already defines `work_kinds: initiative, taskset,
  task, unit, …`, `parent_id` lineage, `planner/worker/reviewer` `*_model_tier` fields,
  `team`, `assigner`/`dispatcher` consumers, and unit fields built for autonomous
  execution (`unit_spec`, `context`, `inputs`, `scope`, `acceptance`, `handoff`,
  `stop_condition`, `escalation_triggers`).
- **Execution gap:** `wave_dispatcher` / `taskset_dispatcher` create a worktree
  (`git worktree add`) and call `task_claim_dispatcher create`, which writes a
  `CLAIM-*.json` + an `instances/<id>.json` record. **Nothing then runs the worker.** No
  loop/daemon auto-claims; dispatch is role-agnostic. `claim_reaper` only recovers expired
  leases.
- **Cost memory:** recent autonomous runs "continuously wasted tokens." Parallel
  delegation multiplies this risk, so cost controls are a hard requirement.

## Goals

1. A concrete 4-role org (Director → Lead → Worker + Reviewer) bound to a role/team
   registry, replacing free-text `owner`.
2. A real delegation flow: Lead decomposes a Taskset into worker-ready Units, dispatches
   Workers that execute in isolated worktrees, Reviewers independently verify, Lead
   integrates.
3. **Risk-based hybrid dispatch:** low-risk/low-cost units auto-dispatch within
   concurrency + budget caps; high-risk/security/expensive/`approval_required` units are
   Owner-gated.
4. A **swappable execution backend** behind the claim/instance/lease contract: Phase 1 =
   Agent-tool sub-agents; Phase 2 = headless daemon — no model/UI change between phases.
5. First-class **token/cost discipline**.
6. A minimal org/state read-API so a later UI sub-project can render the org chart and
   waiting/active/done state from real data.

## Non-Goals (deferred to other sub-projects)

- The headless daemon itself (Phase 2 — only the seam is built now).
- Rich org-chart visualization + 2.5D agent characters (UI sub-project #3).
- Decision-first console IA redesign (UI sub-project #1).
- i18n / Korean UI localization (cross-cutting decision, separate).
- Insight graph redesign (UI sub-project #3).

## Design

### A. Role & Team model

Four roles mapped to schema tiers and the work hierarchy:

| Role | Schema tier | Owns / acts on | Responsibility |
| --- | --- | --- | --- |
| Director / MP (`managing_partner`) | `planner_high` | Initiative | Direction, prioritization, approval of Owner-gated dispatch |
| Lead (team lead) | `planner_high` | Taskset | Decompose Taskset→Units, dispatch, integrate, accept |
| Worker | `worker_low` / `worker_standard` | Unit | Execute one Unit in an isolated worktree |
| Reviewer (≠ Worker) | `reviewer_standard` / `reviewer_high` | Unit verification | Independent W4b verification |

- **New SSOT:** `agents/project/ORG-MODEL.yml` — teams, roles, default model tiers, and the
  canonical role IDs. A gate (`org_model_gate.py`) validates that every work item's
  `owner`/`team` resolves to a registered role/team, ending the `lead_engineer` vs
  `lead-engineer` drift.
- **Teams (initial; refinable):** Engineering, Research, Quality & Eval, Risk & Safety,
  Release & Integrity. Planning is the Lead decomposition function, not a separate team.
- **Hierarchy mapping:** Initiative→Director, Taskset→Lead, Task→(Lead's grouping of
  units), Unit→Worker, verification→Reviewer.

### B. Delegation flow + state machine

1. Director owns/approves an Initiative and delegates a Taskset to a Lead.
2. Lead decomposes the Taskset's Tasks into **worker-ready Units** (`unit_spec`,
   `context`, `inputs`, `scope`, `acceptance`, `handoff`, `stop_condition`,
   `escalation_triggers`), so each Unit is executable without chat history. (Hierarchy:
   Taskset → Task → Unit; a Worker executes one Unit. Small Tasks may hold a single Unit.)
3. **Risk-based dispatch decision** per Unit (see D).
4. Worker executes the Unit in its worktree, heartbeating its lease; on completion it
   releases the claim with verification evidence.
5. Reviewer (a different instance) verifies independently → pass / fail (W4b).
6. Lead integrates passing Units and updates the Taskset rollup.

State (drives the "waiting N / active N / done" visibility the Owner asked for):

- **Unit.status:** `worker_ready → active → in_progress → review → completed → closed`
  (`blocked` as needed).
- **Claim.status:** `claimed → in_progress → review → released` (or `expired` → reaped).

### C. Execution mechanism — swappable `WorkerBackend`

**Principle: the claim + instance + lease records are the contract between "decide" and
"execute." The spawn backend is replaceable behind an interface.**

```
WorkerBackend (interface)
  spawn(claim) -> instance_id        # start a worker on this claim's worktree+unit_spec
  await(claim) -> result             # block/poll until release or failure
  terminate(instance_id)             # cancel/cleanup
  health(instance_id) -> heartbeat   # liveness for lease refresh
```

- **Phase 1 (now) — `SubagentBackend`:** the Lead orchestrator (a script/skill) (1) calls
  the existing dispatcher to create the claim + worktree + instance, (2) `spawn`s a Worker
  **sub-agent via the Agent tool** with the `unit_spec` as its prompt and the unit's
  worktree as isolation, (3) on completion `spawn`s a Reviewer sub-agent for independent
  verification, (4) maps the sub-agent lifecycle onto the claim lease/heartbeat/release so
  the org-chart data stays truthful. Concurrency-capped parallel fan-out (optionally via
  the Workflow tool when the Owner opts in).
- **Phase 2 (later) — `DaemonBackend`:** a long-running daemon watches for worker-ready
  unclaimed Units and spawns headless `claude` processes per worktree, heartbeating and
  reaping. Implements the same `WorkerBackend` interface → **the orchestrator, dispatch
  gating, records, and UI are unchanged.** Only the backend is swapped.

This seam is the hard requirement: nothing above `WorkerBackend` may assume sub-agents.

### D. Risk-based hybrid dispatch gating

Per Unit, evaluate `risk_tier`, `security_sensitive`, `approval_required`, `budget_cap`,
`escalation_triggers`:

- **Auto-dispatch** (Lead, no Owner prompt) when: `risk_tier` ∈ {low, medium},
  not `security_sensitive`, not `approval_required`, est cost ≤ unit budget, and global
  concurrency + taskset budget caps not exceeded.
- **Owner-gated** otherwise. Reuse the existing auto-mode classifier / `approval_gate`
  rather than inventing a parallel approval path.
- A `dispatch_gate.py` makes the auto-vs-gate decision auditable (one record per Unit).

### E. Cost & token discipline (first-class)

Directly addresses "recent versions wasted tokens." Controls:

1. **Per-Unit budget cap** (`budget_cap` / `est_tokens`): the worker backend enforces a
   hard ceiling; on breach it stops and escalates rather than looping.
2. **Per-Taskset aggregate budget:** the Lead stops dispatching new Units once the
   taskset's budget is consumed; remaining Units wait.
3. **Concurrency cap:** bounded parallel workers (config, e.g., min(N, cores−2)) so a
   fan-out cannot explode.
4. **Model-tier routing:** route routine/low-risk Units to `worker_low`; reserve
   `planner_high` / `reviewer_high` for genuinely hard or high-risk Units. Cheap by
   default.
5. **Idempotent claims:** never spawn a Worker for a Unit already `in_progress`/
   `completed` (claim-status check) — prevents re-doing finished work, a known waste mode.
6. **`stop_condition` + `escalation_triggers`:** Units cannot expand into adjacent scope
   or loop; ambiguous/failing Units escalate to the Lead/Owner instead of burning tokens.
7. **Observability:** record `est_tokens` vs `actual_tokens` per Unit; surface overruns in
   the state read-API so waste is visible, not silent.

### F. Observability / org-chart data contract

The read-API exposes, from real records only (no fabricated data):

- Org tree: teams → roles → live instances (`instances/*.json`: who, role, team, parent,
  on-behalf-of, model tier).
- Work state: per Initiative/Taskset/Unit status counts (waiting/active/in_progress/
  review/done) + drill-down to a selected item's Units and their claim status.
- Liveness/audit: lease heartbeats + pane/census events; token est-vs-actual.

This sub-project delivers the **data contract + a minimal text read-API** only. The visual
org chart and characters are UI sub-project #3.

## Build sequence (maps to Taskset Units for "Stage B" registration)

1. **`ORG-MODEL.yml` + role/team registry + `org_model_gate.py`** — define teams/roles/
   tiers; normalize `owner`/`team`; gate drift.
2. **Lead decomposition tool** (`work_split`/`unit` generation: Taskset→worker-ready
   Units) + extend the existing `task_unit_readiness_gate`.
3. **`dispatch_gate.py`** — risk-based auto-vs-Owner-gate decision, auditable.
4. **Orchestrator + `WorkerBackend` interface + `SubagentBackend`** — spawn Worker/
   Reviewer sub-agents, sync claim lease/release lifecycle, enforce concurrency + budget
   caps + idempotency.
5. **Minimal org/state read-API** — org tree + work-state counts + drill-down + token
   est-vs-actual, for later UI consumption.

## Risks / open questions

- **Token blow-up** if caps are mis-set → start conservative (low concurrency, tight
  budgets), make caps Owner-visible, fail safe (stop > loop).
- **Sub-agent ↔ claim lifecycle drift** → the orchestrator owns both; reconcile on
  spawn/await/terminate; reaper remains the backstop.
- **Reviewer independence** must be enforced (Reviewer instance ≠ Worker instance) by the
  orchestrator + identity gate.
- **Team taxonomy** (Section A) is the initial proposal; adjust during plan if disciplines
  differ.
- Interaction with the live harness's own concurrent worktrees must avoid the
  claim-first / `parallel_worktree_gate` contention seen during integration.
