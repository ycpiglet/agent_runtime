---
type: initiative
id: INIT-AR-PARALLEL-WAVE-EXECUTION
status: planned
owner: lead_engineer
created_at: 2026-06-12T18:35:45+09:00
updated_at: 2026-06-12T18:35:45+09:00
priority: High
task_sets:
  - TASKSET-AR-PARALLEL-WAVE-EXECUTION
---

# Parallel Wave Execution Initiative

## Purpose

Turn the current sequential cascade loop into opt-in parallel execution:
multiple codex/claude panes working simultaneously without conflicts, with
the full governance cycle running at wave boundaries instead of per task.

## Decision

- A `wave` is an execution-time bundle of units with no dependency edges and
  pairwise-disjoint `target_files` footprints. It is dispatch metadata, not a
  record hierarchy level, and is orthogonal to `taskset` (goal grouping).
- Parallelism is opt-in: dispatcher default stays cascade; `parallel` mode
  with depth/max-panes options pays the token cost only when wall-clock
  speedup is worth it.
- Conflict prevention moves from merge-time discovery to claim-time blocking
  via footprint intersection checks.
- Shared SSoT files remain orchestrator-owned; workers go through a serial
  merge queue.

## Scope

- Claim-time footprint conflict gate (TASK-AR-500).
- Wave dispatcher with cascade/parallel execution modes (TASK-AR-501).
- Integrator merge queue serialization (TASK-AR-502).
- Claim-first enforcement for worktree work (TASK-AR-503).

## Out Of Scope

- Reopening completed collaboration/concurrency tasksets.
- Central always-on orchestrator daemon (observation stays ui-console based).
- Renumbering or restructuring existing task records.
- Implementation before codex AR-372 / agent-identity branches merge
  (dispatcher and work-items file overlap).
