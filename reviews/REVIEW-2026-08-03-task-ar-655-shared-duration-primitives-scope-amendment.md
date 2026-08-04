---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-shared-duration-primitives-scope-amendment
title: TASK-AR-655 shared duration primitives scope amendment
date: 2026-08-03
created_at: 2026-08-03T00:43:11+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ADD_EXISTING_PORTABLE_CLAIM_STORE_PRIMITIVES
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: fea7453ae83bd569b4d72f7d1349c5b13bc37a54
candidate_tree: 41d6e2a080500f5167378fa372137a73dccfaa78
release_authorized: false
tags: [task-ar-655, t3-replan, scope-amendment, claim-store, duration, portability]
---

# TASK-AR-655 shared duration primitives scope amendment

## Decision

Add stdlib-only duration validation and comparison primitives to the existing
portable claim-authority module rather than duplicating subtly different
validators across dispatcher, low-level lease, reaper, and watchdog entry
points.

The canonical source and its two portable mirrors are already governed by the
three-way package-source parity contract:

- `src/agent_runtime/claim_store.py`
- `scripts/agent_runtime/claim_store.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/claim_store.py`

This amendment adds those paths and `tests/test_claim_store.py` to the active
unit and claim. It does not add a new runtime asset, package, dependency, or
network service.

## Primitive contract

The shared functions must:

- require `type(value) is int`, so booleans, floats, and strings cannot cross
  an API boundary as durations;
- enforce a caller-provided minimum (`1` for lease/TTL, `0` for grace);
- compute lease expiry and convert timedelta/datetime overflow into a bounded
  `ValueError` before any lock, directory, marker, artifact, or claim mutation;
- decide `now <= deadline + grace` without constructing that potentially
  overflowing datetime; and
- accept arbitrary nonnegative Python integers for grace, using exact integer
  day/second/microsecond comparison and conservatively retaining authority.

CLI parsers may wrap the same value-domain rule in
`argparse.ArgumentTypeError`, but every programmatic mutation entry point must
call the shared API validator before acquiring authority.

## Audit durability

Overflow-safe comparison removes the known mixed-sweep failure. The reaper
must additionally flush any already-queued post-commit audit records from a
`finally` path after lock release, so an unexpected later classification error
cannot leave an earlier durable reap without pane/stop evidence.

## Verification and boundary

Add direct primitive tests to `tests/test_claim_store.py`, then exercise the
behavioral RED/GREEN matrix in dispatcher, claim-lease, reaper, and watchdog
tests. Keep all three claim-store files byte-identical and run their existing
identity matrix plus template/host-lock gates.

No claim release, consumer mutation, CI dispatch, versioning, tag, push,
publish, deployment, or external release action is authorized.
