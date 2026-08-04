---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-03-task-ar-655-lease-grace-boundaries
title: TASK-AR-655 lease and reaper grace boundary audit
date: 2026-08-03
created_at: 2026-08-03T00:30:23+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: audit
reviewer: codex-ar655-lease-scope-auditor-20260803
reviewer_role: independent-auditor
status: completed
signal: fail
verdict: REVISE_SCOPE_BEFORE_RED
priority: P1
finding_counts: {P0: 0, P1: 3, P2: 2}
candidate_commit: 905480cefa4775141e304eda4ca8c20b6b8ff60c
candidate_tree: 58aa45a32d3033e54542111ecd0664b36a75c175
release_authorized: false
tags: [task-ar-655, lease, grace, claim-reaper, deadlock-watchdog, failure-to-regression]
---

# TASK-AR-655 lease and reaper grace boundary audit

## Outcome

The existing AR-655 task owns the defect, but its registered unit footprint and
verification command omit the authoritative reaper/watchdog surfaces. A
bounded T3 scope amendment is required before adding RED tests or changing
implementation.

Exact canonical lookup for
`defect:negative-lease-or-grace-kills-live-claim:315a2daf2bae5424`
and for
`defect:claim-reaper-deadline-overflow-partially-mutates:5d3658dc71ab217a`
returned `[]` with legacy lookup disabled. The active claim performed the first
lookup before persistence; the second was performed before its scope amendment.

## P1 findings

### Negative create lease persists already-expired authority

`scripts/task_claim_dispatcher.py` calculates
`now + timedelta(minutes=args.lease_minutes)` without validating the duration.
In an isolated temporary Git worktree, `create --lease-minutes -1` returned
zero and persisted a claim whose `claimed_at` was `08:00` while both top-level
and nested `expires_at` were `07:59`.

The lower-level `scripts/claim_lease.py` has the same input-domain defect in
both acquire and heartbeat. It accepts zero, negative, and boolean TTL seconds;
negative or zero values persist expiry no later than the heartbeat, and a huge
integer raises an uncaught datetime overflow. AR-655 already names this module
as an input for the planned heartbeat integration, so leaving it out would
reintroduce the same defect through the low-level path.

### Negative explicit grace can kill future-live authority

`scripts/claim_reaper.py` coerces an explicit grace with `int()` and then uses
`deadline + timedelta(seconds=grace_seconds)`. At `now=12:00`, a claim expiring
at `12:05` was transitioned to `expired` with explicit grace `-600` through all
four entry paths:

- reaper API;
- reaper CLI, return code zero;
- watchdog API; and
- watchdog CLI, return code zero.

`scripts/deadlock_watchdog.py` forwards the negative value. It also isolates a
reaper exception as report data and normally returns zero, so only validating
inside the reaper would leave a misleading watchdog CLI contract.

### Deadline addition overflow can partially commit a sweep without audit

With ordinary grace `600`, a sorted dead claim followed by an active claim at
datetime maximum reproduces a transactional split: the first claim is
atomically changed to `expired`, adding grace to the second deadline raises
`OverflowError`, and the queued pane/stop audits are never emitted. This is a
separate registered defect because it leaves durable authority inconsistent
with its audit trail even without negative input.

## P2 findings

- Task, unit, and claim did not begin with a common defect signature and the
  unit omitted root runtime mirrors, reaper/watchdog sources, and their tests.
- The explicit API accepts implicit conversions while the environment default
  already has a distinct legacy rule: unset and malformed values use `600`,
  while a negative environment value is clamped to `0`.

The pre-amendment dispatcher, reaper, and watchdog test files passed `136`
tests despite the reproduced defects, demonstrating missing regression
coverage rather than an incidental failing baseline.

## Required value domains

- A create lease is a plain integer number of minutes, excluding `bool`, and
  must be at least `1`. Zero and negative values fail before persistence.
- A low-level lease TTL is a plain integer number of seconds, excluding
  `bool`, and must be at least `1` for both acquire and heartbeat.
- Explicit reaper/watchdog grace is a plain integer number of seconds,
  excluding `bool`, and must be at least `0`.
- Zero grace remains valid. Equality with the raw deadline remains live; the
  claim becomes dead only after that instant.
- Positive grace equality remains inclusive-live.
- The legacy environment normalization remains unchanged: unset/malformed is
  `600`; negative is clamped to `0`.
- Huge nonnegative grace must be overflow-safe and conservative. Integer
  comparison should classify it as live rather than imposing an arbitrary cap.
- Near-maximum deadlines must use the same overflow-safe comparison so a sweep
  cannot commit an earlier claim and then lose its audit queue.
- A create duration whose datetime addition overflows must return nonzero,
  without traceback and without any claim, handoff, log, pane event, instance,
  or store-marker mutation.

## Scope consequence

The root/template pairs for dispatcher, low-level lease, reaper, and watchdog, the direct tests,
the existing reaper boundary/concurrency checks, and the generated host lock
must be registered together. The original AR-655 heartbeat/renewal acceptance
remains in force; this audit only adds the fail-closed value boundary that must
precede that broader implementation.

No consumer mutation, CI dispatch, versioning, tag, push, publish, deployment,
claim release, or external release action is authorized.
