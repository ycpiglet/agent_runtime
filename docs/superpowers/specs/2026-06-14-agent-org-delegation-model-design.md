# Agent Org & Delegation Model — Design (research-refined)

- **Date:** 2026-06-14
- **Status:** approved direction (Owner, 2026-06-14); refined by research 2026-06-14
- **Owner:** managing_partner (Director)
- **Research basis:** `reviews/RESEARCH-2026-06-14-agent-org-design-references.md`
- **Topic:** Operationalize a Director→Lead→Worker+Reviewer org with **seam-aware**
  parallel delegation, reconciling machinery the project already ships.

## Bottom Line

The project already has the *mechanism* (roles, instances, `team_id`,
`parent_instance_id`, claims, leases, worktrees, dispatchers), the *hierarchy*
(`initiative → taskset → task → unit`), the *tiers* (`planner / worker / reviewer`), and —
in the **template** — a full org suite (`roles.yml` with ~17 roles, `agent_orchestrator`,
`subagent_dispatch` perspectives, `subagent_council`, `agent_seminar` blind-Delphi). It is
simply **not operationalized in the repo**: ~90% of work is owned by free-text
`lead_engineer`, and **a claim existing does not run a worker** (today a human opens a pane
manually). This design closes that gap by **reconciling the two systems** (template
org-suite ↔ repo claim/wave execution) behind a swappable execution backend, with
**seam-aware parallelism + phased autonomy** (software work is on Cognition's
"don't naively parallelize" side), a separate **deliberation/persona-diversity layer**, and
**token cost as a binding constraint** (multi-agent ≈ 15× tokens).

## Problem / Context

- **Centralization:** 189/~210 items owned by `lead_engineer` / `lead-engineer` (free-text,
  inconsistent). Only `agents/lead_engineer/` is a real doer dir. The Lead acts as
  planner + worker + reviewer at once.
- **Two un-reconciled systems:** the **template** ships `agents/roles.yml` (ceo,
  managing-partner, lead-engineer, backend, uiux, ci-cd, qa, independent-auditor, research,
  doc-steward, scribe, timeline, beta-tester, secretary, requirements-interviewer, owner) +
  `agent_orchestrator.py` + `subagent_dispatch.py` (perspectives: implementer / strategist
  / skeptic / reviewer / auditor) + `subagent_council.py` + `agent_seminar.py`. The **repo**
  does **not** use these (only `release_council_gate.py`); it runs the newer 500-series
  claim/wave dispatch. The repo does not dogfood its own org.
- **Execution gap:** dispatchers write `CLAIM-*.json` + `instances/<id>.json` + a worktree;
  **nothing auto-runs the worker**; dispatch is role-agnostic; `claim_reaper` only recovers
  expired leases.
- **Research caveats (see research note):** software eng is write-heavy + interdependent →
  naive parallelism causes context fragmentation + conflicting assumptions; multi-agent ≈
  15× tokens; persona diversity helps only in deliberation and only if independent.

## Goals

1. A concrete 4-role org (Director → Lead → Worker + Reviewer) bound to a role/team
   registry, **reusing the template `roles.yml`** rather than inventing one.
2. Real but **seam-aware** delegation: Lead decomposes a Taskset into worker-ready Units,
   dispatches Workers **only on genuinely independent seams** (separate files/services/
   read-only research), **serializes interdependent edits** (single-thread), and is the
   single integrating owner.
3. **Risk-based hybrid dispatch as an autonomy slider, default-low**, sliding right per
   task class as reliability is earned.
4. A **swappable `WorkerBackend`** behind the claim/instance/lease contract: Phase 1 =
   Agent-tool sub-agents; Phase 2 = headless daemon — no model/UI change between phases.
5. A separate **deliberation & persona-diversity layer** (extend council/seminar) used for
   design/decision/review only.
6. First-class **token/cost discipline**.
7. A minimal org/state read-API for a later UI sub-project.

## Non-Goals (deferred)

Headless daemon itself (Phase 2 — only the seam now); rich org-chart viz + 2.5D characters
(UI sub-project #3); decision-first console IA (UI #1); i18n; insight-graph redesign.

## Design

### A. Role & team model (reuse the template registry)

Four roles, mapped to existing `roles.yml` roles + schema tiers + work hierarchy:

| Role | From `roles.yml` | Tier | Owns | Responsibility |
| --- | --- | --- | --- | --- |
| Director / MP | `ceo` / `managing-partner` | planner_high | Initiative | Direction, scope, approval of gated dispatch |
| Lead | `lead-engineer` + per-discipline leads (`backend`,`uiux`,`ci-cd`,`qa`,`research`) | planner_high | Taskset | Decompose→Units, dispatch, **integrate** |
| Worker | discipline role at worker tier | worker_low/standard | Unit | Execute one Unit in an isolated worktree |
| Reviewer | `independent-auditor` / `qa` | reviewer_standard/high | Unit verification | Independent W4b verification (≠ Worker) |

- **SSOT:** port/activate `agents/roles.yml` in the repo (it exists only in the template
  today) and add `agents/project/ORG-MODEL.yml` only for the *team→role→tier* overlay the
  registry lacks. A gate validates every item's `owner`/`team` resolves to a registered
  role, ending the `lead_engineer`/`lead-engineer` drift.
- **Teams = functional disciplines** (Engineering, UI/UX, Research, Quality/Eval, Risk &
  Release). The Owner's "split by UI/UX" maps here: **UI/UX is a team/role inside the org**
  (`uiux` already exists), not a competing decomposition.
- **Hierarchy mapping:** Initiative→Director, Taskset→Lead, Task→Lead's grouping,
  Unit→Worker, verification→Reviewer.
- **LLM-OS framing (Karpathy):** Director ≈ kernel/scheduler; context windows are scarce
  RAM (practice context engineering, not stuffing); the repo + claim/handoff records are
  the **disk memory** that compensates for worker "amnesia."

### B. Delegation flow + state machine

1. Director owns/approves an Initiative; delegates a Taskset to a Lead.
2. Lead decomposes the Taskset's Tasks into **worker-ready Units** with a structured
   contract — objective, output format, tools/inputs, **explicit boundaries** (`scope`,
   `stop_condition`), `acceptance`, `handoff` — so each Unit runs without chat history.
   Units are PR-sized (small, independently verifiable).
3. **Seam analysis + risk-based dispatch decision** per Unit (see C, D).
4. Worker executes the Unit in its worktree, heartbeating its lease; releases with evidence.
5. Reviewer (different instance) verifies independently → pass / fail; bounded retries (≤3).
6. Lead integrates passing Units (the single serialization point) and updates the rollup.

State (drives "waiting N / active N / done" visibility): **Unit** `worker_ready → active →
in_progress → review → completed → closed` (`blocked`); **Claim** `claimed → in_progress →
review → released` (or `expired` → reaped).

### C. Execution mechanism — seam-aware, swappable `WorkerBackend`

**Principle: the claim + instance + lease records are the contract between "decide" and
"execute." The spawn backend is replaceable behind an interface.**

```
WorkerBackend (interface)
  spawn(claim) -> instance_id     # run a worker on this claim's worktree + unit_spec
  await(claim) -> result          # block/poll until release or failure
  terminate(instance_id)
  health(instance_id) -> heartbeat
```

- **Seam-aware parallelism (the key refinement):** the Lead may dispatch Workers in
  parallel **only for Units with disjoint footprints** (`target_files` / services /
  read-only research), verified by the existing `footprint_conflict_gate`. Units that
  touch shared or interdependent code are **serialized** through the Lead. Workers receive
  full upstream traces (not just messages); long context is compressed. This directly
  answers the Cognition failure mode.
- **Phase 1 — `SubagentBackend` (now):** Lead orchestrator (1) creates claim + worktree +
  instance via the existing dispatcher, (2) `spawn`s a Worker **sub-agent via the Agent
  tool** with the unit contract + worktree isolation, (3) on completion `spawn`s a Reviewer
  sub-agent, (4) syncs sub-agent lifecycle ↔ claim lease/release. Concurrency-capped.
- **Phase 2 — `DaemonBackend` (later):** a daemon spawns headless `claude` processes per
  worktree, implementing the same interface — orchestrator, gating, records, UI unchanged.
- **Phased autonomy (autonomy slider):** start conservative (low concurrency, narrow
  auto-dispatch); widen a task class only after it earns a reliability track record.

### D. Risk-based hybrid dispatch gating

Per Unit evaluate `risk_tier`, `security_sensitive`, `approval_required`, `budget_cap`,
`escalation_triggers`:

- **Auto-dispatch** (no Owner prompt) when: `risk_tier` ∈ {low, medium}, not
  `security_sensitive`, not `approval_required`, est cost ≤ unit budget, footprint disjoint,
  and concurrency + taskset-budget caps not exceeded.
- **Owner-gated** otherwise — reuse the existing auto-mode classifier / `approval_gate`.
- `dispatch_gate.py` records the auto-vs-gate decision per Unit (auditable).

### E. Deliberation & persona-diversity layer (separate from execution)

Used for **design debate, decisions, and reviews — never routine execution** (where
diversity is noise + cost).

- Extend the existing blind-Delphi `agent_seminar.py` + DIVERSITY-COUNCIL with **persona
  archetypes** that vary *substance* axes (risk tolerance, time-horizon, values/
  optimization target, domain lens, epistemic style) — not just tone. Starter set: Skeptic,
  Pragmatist, Systems-Thinker, User-Advocate, Empiricist, First-Principles, Steward.
  **No demographic personas** (bias).
- Keep diversity *real*: independent blind first drafts before agents see each other;
  anonymized aggregation; confidence-weighting to resist capture by a confident-wrong
  agent; **measure** semantic spread and re-anchor each round.
- Optional **LLM-Council** (Karpathy): multiple models → anonymized ranking → Chairman
  synthesis for high-stakes reviews.
- Persona ≠ pipeline role: a Worker/Reviewer *role* is a pipeline-stage responsibility; a
  *persona* is a deliberation perspective (orthogonal, like `subagent_dispatch`).

### F. Cost & token discipline (binding — multi-agent ≈ 15×)

1. Per-Unit `budget_cap`/`est_tokens` hard ceiling — on breach, stop + escalate, never loop.
2. Per-Taskset aggregate budget — Lead stops dispatching when consumed.
3. Concurrency cap — bounded parallel workers.
4. Model-tier routing — cheap `worker_low` for routine Units; strong tier only for hard/
   high-risk Units and the Lead (Karpathy: optimize the generation–verification gap).
5. Idempotent claims — never re-spawn a Unit already in_progress/completed.
6. `stop_condition` + `escalation_triggers` — no scope creep, no loops.
7. Observability — `est_tokens` vs `actual_tokens` per Unit surfaced; waste is visible.

### G. Observability / org-chart data contract

Read-API exposes, from real records only: org tree (teams→roles→live instances), work-state
counts per Initiative/Taskset/Unit + drill-down, lease heartbeats/census, token est-vs-
actual. Minimal text read-API only; visual org chart + characters are UI sub-project #3.

## Build sequence (maps to Taskset Units for "Stage B" registration)

1. **Port + activate `agents/roles.yml` in the repo** + `ORG-MODEL.yml` team overlay +
   `owner`/`team` normalization gate.
2. **Lead decomposition tool** (Taskset→worker-ready Units) + extend
   `task_unit_readiness_gate`.
3. **Seam + risk dispatch gate** (`dispatch_gate.py`): footprint-disjoint check +
   auto-vs-Owner-gate decision, auditable.
4. **Orchestrator + `WorkerBackend`/`SubagentBackend`** — spawn Worker/Reviewer sub-agents,
   sync claim lifecycle, enforce seam-serialization + concurrency/budget caps + idempotency
   + full-trace sharing.
5. **Deliberation/persona layer** — extend `agent_seminar`/council with substance-axis
   personas + diversity measurement + capture guards (reuse blind-Delphi).
6. **Minimal org/state read-API** — org tree + work-state counts + drill-down + token
   est-vs-actual.

## Risks / open questions

- **Naive parallelism** (the #1 failure) — mitigated by footprint-gate seams + Lead
  serialization + full-trace sharing; start with low concurrency.
- **Token blow-up** — conservative caps, Owner-visible, fail safe (stop > loop).
- **Fake diversity / persona conformity (85%)** — blind-Delphi, measurement,
  confidence-weighting; personas only in deliberation.
- **Sub-agent ↔ claim lifecycle drift** — orchestrator owns both; reaper backstop.
- **Two-systems reconciliation** — porting template `roles.yml`/orchestrator into the repo
  must not fork from the template; prefer shared code.
- **Live-harness contention** — avoid the claim-first / `parallel_worktree_gate` issues seen
  during integration.
