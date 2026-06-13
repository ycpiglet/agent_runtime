# Deadlock Guardrails — keeping a goal moving without weakening safety

Autonomous goals (waves, tasksets, `agent_loop --goal`) sometimes stop mid-run.
The stops fall into two kinds, and this subsystem treats them differently:

- **Accidental stalls** (recoverable) — a dead worker's stale claim, a dirty
  worktree on a feature branch, an expired lease, a transient error. These are
  auto-recovered / auto-resumed within strict guardrails.
- **Intentional safety guards** (preserved, never overridden) — the hard
  iteration cap, the `max_failures` halt, emergency stop files, the owner
  governance Stop hook, plan-assumption drift, footprint conflicts, taskset
  boundary completion, and a dirty worktree on `main`/`master`.

Every stop is classified and recorded so the *appropriate* auto-resume cap can be
judged later from real data instead of guessed up front.

## Components

| Module | Role |
| --- | --- |
| `scripts/stop_events.py` | Classify (`recoverable` vs `intentional`), record stop events to `agents/runtime/events/stop_events-<date>.jsonl`, and aggregate `agents/runtime/stop_counters.json`. Foundation for everything below. |
| `scripts/claim_reaper.py` | Recover **provably-dead** claims (lease expired beyond grace, non-orchestrator) → status `expired` → unit becomes re-dispatchable. Breaks the wave/goal deadlock. Dry-run by default. |
| `scripts/claim_reaper_hook.py` | SessionStart hook wrapper: auto-recover provably-dead claims at session start (best-effort, non-blocking). |
| `scripts/agent_loop.py` (`--checkpoint-dirty`) | Opt-in: commit a WIP checkpoint instead of stopping when the worktree is dirty on a feature branch (never on `main`/`master`). |
| `scripts/goal_supervisor.py` | Detect a stopped-but-incomplete goal loop, classify the stop, and re-arm it for *resumable* reasons under a restart cap. |
| `scripts/deadlock_watchdog.py` | One-shot cycle (reaper + supervisor) for periodic scheduling. |

## The deadlock, precisely

When a worker dies mid-task its claim JSON stays in an active status. The wave
dispatcher then skips that task forever ("task already has an active claim"), so
the wave never completes. `task_claim_dispatcher release` can't help — it requires
independent cross-verification (it is for *completed* work, not *abandoned* work).

The reaper transitions a provably-dead claim to `expired`, which is in **none** of
the dispatcher/footprint active sets nor the done set, so the unit re-classifies as
`pending` and is dispatched again. The worktree/branch are left in place so the new
worker resumes from where the dead one left off. The original status is kept in
`recovered_from_status` and every reap is audited (pane event + stop event).

### Why a long-running live worker is never falsely reaped

A live worker keeps refreshing its lease (`expires_at` / `lease.expires_at`) via
heartbeat, so its deadline stays in the future. The reaper only acts when
`now > deadline + grace`. A dead worker stops refreshing; a live one — however slow
— keeps its deadline ahead of now.

## Configuration (environment variables)

| Variable | Default | Effect |
| --- | --- | --- |
| `AGENT_RUNTIME_REAPER_GRACE_SECONDS` | `600` | Seconds past lease expiry before a claim is provably dead. |
| `AGENT_RUNTIME_REAPER_AUTO_APPLY` | on | SessionStart hook recovers provably-dead claims. Set `0` for report-only. |
| `AGENT_RUNTIME_REAPER_DISABLE` | off | Set `1` to skip the SessionStart reaper entirely. |
| `AGENT_RUNTIME_GOAL_MAX_RESTARTS` | `3` | Resume cap per goal. **A starting guess** — tune it from `stop_counters.json`. |

## Wiring

- **Hook** — `claim_reaper_hook.py` is registered in `.codex/hooks.json` `SessionStart`.
  It recovers dead claims before new work begins, best-effort and non-blocking.
- **Trigger (periodic)** — schedule `deadlock_watchdog.py --apply` on an interval
  (Windows Task Scheduler, cron, or the harness `/loop` / `schedule`) for long goal
  runs. One cycle reaps dead claims and re-arms a stopped goal.
- **API** — every module has a dry-run-by-default CLI (`--apply` to act, `--json`
  for machine output).

## Safety invariants

1. A claim whose lease is still valid (heartbeating, or within grace) is never touched.
2. Orchestrator claims are never reaped.
3. Claims with no lease info are skipped (death cannot be proven), not reaped.
4. The reaper processes **all** claims, skipping the un-actionable and recovering the rest.
5. Reaping is idempotent; the terminal `expired` status leaves the unit re-dispatchable.
6. `--checkpoint-dirty` never auto-commits on `main`/`master`, and does not bypass
   commit hooks — a checkpoint that can't pass them lets the loop stop honestly.
7. The supervisor never resumes an intentional, non-resumable stop
   (`max_failures`, emergency/orchestrator stop). `max_iterations` is resumable but
   bounded by the restart cap.
8. Everything is dry-run by default; only `--apply` (or the hook/trigger) mutates state.

## Tuning the restart cap from data

`AGENT_RUNTIME_GOAL_MAX_RESTARTS` defaults to a conservative `3`. Don't guess the
"right" number — read it off the recorded data once enough goals have run:

```
python scripts/stop_events.py --root . summary --json
```

`goal_restarts` shows resumes per goal; `by_reason` / `by_action` show how often
each stop reason fires and what was done. Raise or lower the cap to match how many
restarts goals actually need before completing vs. spinning.
