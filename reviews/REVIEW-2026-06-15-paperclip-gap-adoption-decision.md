# REVIEW — Paperclip Gap Analysis & Adoption Decision (TASK-AR-367)

- **Date:** 2026-06-15
- **Task:** TASK-AR-367 (TASKSET-AR-DOC-TO-PLAN)
- **Scope note:** Decision over the 4 characterized Paperclip axes (github.com/paperclipai/paperclip, MIT), grounded in agent_runtime's current capabilities. Deep MIT source review is recorded as an optional follow-up; the decisions below stand on the axis descriptions + repo state and do not assert unverified Paperclip internals.

## Bottom Line

Of the 4 axes, **2 are adopted** (budget hard-stop; heartbeat lifecycle — as the org-delegation Phase-2 daemon shape), **1 is modified-adopt** (declarative widgets over out-of-process plugins), and **1 is deferred to Idea Vault** (full multi-tenancy). agent_runtime already covers most of these in nascent form; the work is to formalize, not import wholesale.

## Per-axis decision

### 1. Per-agent budget hard-stop — **ADOPT** (follow-up task)
- **Current state:** `dispatch_gate.py` (risk + budget_cap, TASK-AR-559) and `org_orchestrator.py` (per-taskset token budget, **stop-the-line**, TASK-AR-560) already cap and halt dispatch; `WORK-SCHEMA` has `budget_cap`/`est_*`; TASK-AR-368 adds `actual_*` capture.
- **Gap:** no *aggregate* month/agent-level hard ceiling across tasksets.
- **Decision:** Adopt a thin **budget ledger + hard-stop gate** layered on AR-368 actuals: sum actual cost per agent-role/month/taskset; a gate refuses new dispatch past an Owner-set cap. Reuse the existing risk-based hybrid (Owner-gate on breach), not a parallel system.
- **Follow-up:** register a task "Aggregate budget ledger + hard-stop gate" under the org-delegation or a cost-control taskset.

### 2. Heartbeat execution lifecycle — **ADOPT as the Phase-2 daemon shape** (defer impl)
- **Axis:** scheduled wakeup → budget check → workspace resolve → skill loading → structured log.
- **Current state:** claim **lease heartbeat** + `claim_reaper` (liveness), `scheduled_dispatch_gate.py` (AR-335 scheduled wakeups, emits events but never auto-runs), and the swappable **`WorkerBackend`** (TASK-AR-560) whose **Phase-2 `DaemonBackend`** is exactly "spawn per worktree, heartbeat, reap."
- **Decision:** Adopt this lifecycle as the **specification for the headless `DaemonBackend`** (org-delegation Phase 2): wakeup (scheduled_dispatch) → budget check (axis 1 ledger) → workspace (worktree) resolve → skill/context load (`unit_spec`) → structured pane/census log. Do not build a parallel runtime; it IS the daemon backend behind the existing contract.
- **Follow-up:** fold into the existing org-delegation Phase-2 daemon work item (spec already names the seam).

### 3. Multi-company / full tenancy — **DEFER → Idea Vault**
- **Axis:** full data-isolation tenancy vs current multi-host (AR-341).
- **Decision:** Defer. Current multi-host claim safety (AR-341) is adequate for the dogfooding + small-team horizon. Full tenant data isolation is a large, separable initiative with its own security model; adopting it now is premature (YAGNI). **Record in Idea Vault** with the isolation-level question for revival when a real multi-tenant requirement appears.

### 4. Plugin (out-of-process worker) vs declarative widgets — **MODIFY-ADOPT (declarative)**
- **Axis:** plugin security boundary vs declarative widgets (AR-341).
- **Decision:** Prefer **declarative widgets / extension points (AR-341)** as the extension model; **reject out-of-process plugin workers** for now on security grounds (an out-of-process worker is a new untrusted-code execution boundary requiring sandboxing, capability scoping, and supply-chain review). The agent org's Worker sub-agents already provide scoped execution behind the WorkerBackend; a plugin system would duplicate that with weaker isolation. **Record the plugin option in Idea Vault** (revisit if a marketplace need emerges with a sandbox design).

## Follow-up registration
- Adopt → tasks: (1) aggregate budget ledger + hard-stop gate; (2) Phase-2 `DaemonBackend` heartbeat lifecycle (already implied by the org-delegation spec).
- Defer → Idea Vault: full multi-tenancy isolation; out-of-process plugin workers.

## Done
4 axes each have a 채택/보류/수정 verdict + rationale + follow-up. Deferred items routed to Idea Vault. Decision is grounded in current repo capabilities; deep Paperclip MIT source review remains an optional follow-up that would not change these directions.
