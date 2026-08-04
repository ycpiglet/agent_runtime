---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-03-task-ar-655-deterministic-liveness-time-seams
title: TASK-AR-655 deterministic liveness CLI time-seam audit
date: 2026-08-03
created_at: 2026-08-03T02:44:59+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: audit
reviewer: codex-ar655-heartbeat-cross-slice-reviewer-20260803
reviewer_role: peer-reviewer
status: completed
signal: fail
verdict: ADD_DETERMINISTIC_AWARE_NOW_TO_LIVENESS_CLIS
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 1}
candidate_commit: 95d3f987e2ac039d9a3a6883e1faaa61b5b90361
candidate_tree: 878c22675ddf34c3ded64652c8cc4daf3a751803
release_authorized: false
tags: [task-ar-655, liveness, deterministic-time, cli, template-smoke]
---

# TASK-AR-655 deterministic liveness CLI time-seam audit

## Outcome

The shared expiry classifier correctly makes fixed 2026-06 and 2026-07 claims
expired at the current wall clock. Two older integration journeys, however,
create claims with an explicit historical `--now` and then invoke the
parallel/state-sync CLIs without any way to reuse that fixture clock. Their
Python entry points already accept an injected aware `now`; only the CLI seam
is missing.

The root dispatcher journey now fails cleanly because its supplemental test
passes `--now` to `parallel_worktree_gate.py` and argparse refuses the unknown
option. The installed core journey exposes the same wall-clock dependency in
the template parallel gate and will expose it in state sync once the first
failure is removed.

This is a boundary of the already registered
`defect:expired-task-claim-appears-live-across-runtime-c:39f0d2087c60993c`
signature, not a new defect family. No new signature or Compound lookup is
introduced.

## Required scope

- Add an optional timezone-aware `--now` to root/template
  `parallel_worktree_gate.py` and pass it to both normal and continuity-only
  evaluation.
- Add the same optional aware `--now` to root/template `state_sync_gate.py`
  and pass it to `analyze()`.
- Add `tests/test_template_smoke.py` to the unit footprint and use one fixed
  fixture clock for both installed liveness CLIs.
- Preserve the default wall clock, shared grace resolution, and fail-closed
  expiry semantics when `--now` is omitted.

## P2 condition

Malformed or naive `--now` input must return a bounded non-zero result without
a traceback. Root/template parity and the installed portable journey must be
verified after the change.

No claim release, CI dispatch, version, tag, push, publish, deploy, or external
release action is authorized.
