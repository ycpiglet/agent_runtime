---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-659-w4b-consumer-wiring-scope-amendment
title: TASK-AR-659 W4b Consumer Wiring Scope Amendment
date: 2026-08-03
created_at: 2026-08-03T15:29:00+09:00
amended_at: 2026-08-03T15:30:10+09:00
task_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
claim_id: CLAIM-20260803-143123-task-ar-659-cfc8
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
tier: T3
reviewer: le-20260803-143123-kst-cfc8
reviewer_role: worker
status: accepted
signal: pass
verdict: AMEND_SCOPE_FOR_W4B_CONSUMER_WIRING
priority: P2
w4b_ref: independent context-isolated W4b, 2026-08-03
release_authorized: false
tags: [task-ar-659, scope-amendment, w4b, deadlock-watchdog, reaper-hook]
---

# TASK-AR-659 W4b consumer wiring scope amendment

## Bottom Line

The independent W4b's P2 finding cannot be repaired inside the unit's declared
footprint. Two files must be added: `scripts/deadlock_watchdog.py` and
`scripts/claim_reaper_hook.py`, plus their template mirrors.

## Why the original footprint was wrong

The unit declared the files that *produce* the recovery signal
(`claim_reaper.py`, `task_claim_dispatcher.py`) but not the files that
*consume* it. W4b showed the consequence: `_summary_line`
(`deadlock_watchdog.py:64-74`) emits only `reaped / live / skipped`, and the
session-start hook (`claim_reaper_hook.py:39`) reads only
`reaped` / `would_reap`. So the new `needs_owner_recovery` bucket reached
nobody except a human running `claim_reaper.py` directly and reading
`_render_human`.

That is the exact failure the unit exists to prevent. `deadlock_watchdog` is
the component documented as breaking wave deadlocks, and the hook is what an
owner actually sees at session start — the two places the AR-655 signal most
needed to surface. Producing a signal no consumer reads is not a fix.

## Amendment

Added to `target_files`:

- `scripts/deadlock_watchdog.py`
- `src/agent_runtime/templates/project/scripts/deadlock_watchdog.py`
- `scripts/claim_reaper_hook.py`
- `src/agent_runtime/templates/project/scripts/claim_reaper_hook.py`

Both changes are additive and read-only with respect to claim authority: the
watchdog gains one counter in its summary line, and the hook gains one
conditional message naming the `terminalize` command. Neither mutates a claim,
neither changes reaping behaviour, and both degrade silently via
`report.get("needs_owner_recovery") or []` against an older report shape.

## Assumptions unchanged

Every plan assumption recorded in
`REVIEW-2026-08-03-task-ar-659-legacy-claim-bootstrap-t3-replan.md` still
holds. No network or distributed lease dependency, recovery stays owner-bound,
no release or acceptance authority is added, and the reaper still never
auto-reaps an orchestrator claim.

## Record sequence

This record was authored, then `renew` refused it for a missing `tier` field,
then `tier: T3` was added, then `renew` succeeded at `15:30:27` and the anchors
were re-recorded at the same second. An earlier revision of this file carried a
hand-written `created_at` of `15:35:00`, which post-dated the very `renew` it
authorized. `_accepted_replan_ref` validates status, signal, tier, task, and
unit but not ordering, so nothing caught it. Corrected here rather than left as
a self-consistent-looking but false timestamp.

## Tier

`T3`. Per `AGENTS.md:123-126`, T3 is the replan review that re-runs `record`
to re-anchor the plan. The implementation drifted taskset anchors
(`task_claim_dispatcher.py`, `claim_reaper.py`, `deadlock_watchdog.py`, their
mirrors, the touched test files, and the regenerated host lock fixture), so
this record re-anchors all of them rather than only amending the footprint.

## Decision

`AMEND` the unit footprint, re-record the taskset anchors against this record,
and rebind the claim scope by `renew`. No release authorization.
