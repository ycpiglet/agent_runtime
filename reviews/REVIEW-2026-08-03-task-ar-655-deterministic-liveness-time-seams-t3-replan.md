---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-deterministic-liveness-time-seams-t3-replan
title: TASK-AR-655 deterministic liveness CLI time-seam T3 amendment
date: 2026-08-03
created_at: 2026-08-03T02:44:59+09:00
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
verdict: ADD_ONLY_DETERMINISTIC_CLI_TIME_INJECTION
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
candidate_commit: 95d3f987e2ac039d9a3a6883e1faaa61b5b90361
candidate_tree: 878c22675ddf34c3ded64652c8cc4daf3a751803
release_authorized: false
tags: [task-ar-655, t3-replan, liveness, deterministic-time, cli]
---

# TASK-AR-655 deterministic liveness CLI time-seam T3 amendment

## Decision

Accept the cross-slice audit. Extend the registered footprint only with
`tests/test_template_smoke.py` and the two audit records. The four gate source
pairs and `tests/test_task_claim_dispatcher.py` are already registered.

The implementation may expose an optional aware `--now` that delegates to the
existing injected-time Python APIs. It must not add a phase exception, enlarge
grace, revive expired authority, alter the default wall clock, or write claim,
pointer, Git, or external state.

## Failure-first order

1. Commit the root CLI supplemental RED already reproduced as argparse refusal.
2. Add installed-template RED coverage using the same explicit fixture clock
   for parallel and state sync.
3. Implement root/template CLI parsing with bounded malformed/naive refusal.
4. Re-run the dispatcher journey, installed portable journey, root/template
   parity, and the complete registered matrix.

The active claim remains claimed and the unit remains verification-failed.
No release or external action is authorized.
