---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-03-task-ar-655-owner-governance-clock-propagation
title: TASK-AR-655 owner-governance liveness clock propagation audit
date: 2026-08-03
created_at: 2026-08-03T02:56:50+09:00
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
verdict: PROPAGATE_AWARE_NOW_THROUGH_OWNER_GOVERNANCE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 1bebb9947a9eb58736646ca6688b9d3db9ab55d7
candidate_tree: d56667c3dfd3412b5bcf68fa23ca90b3b3f7982a
release_authorized: false
tags: [task-ar-655, liveness, deterministic-time, owner-governance, template-smoke]
---

# TASK-AR-655 owner-governance liveness clock propagation audit

## Outcome

The root/template parallel and state-sync CLIs now accept the same explicit
aware clock as the historical claim fixture. Their exact supplemental selector
passes 8 cases, and the complete two-gate regression passes 123 cases. The
installed portable journey still fails after those direct checks because the
template `owner_governance_gate.py` invokes both liveness gates again without
propagating the fixture clock.

The nested calls therefore evaluate the July claim against the August wall
clock and report the same claim expired twice. This is a P1 orchestration seam:
the individual consumers are truthful, but their aggregate harness cannot
reproduce the same evaluation instant.

This remains a boundary of the registered
`defect:expired-task-claim-appears-live-across-runtime-c:39f0d2087c60993c`
signature. It does not introduce a new defect family or require a new Compound
lookup.

## Reproduced evidence

- Direct deterministic selector: `8 passed`.
- Complete parallel/state-sync suites: `123 passed`.
- Installed portable journey: one failure after direct gates pass.
- Nested root cause: owner-governance starts parallel and state-sync with only
  `--check`; both emit the same fixed claim's liveness-expired blocker.

## Required scope

- Add an optional timezone-aware `--now` to root and template
  `owner_governance_gate.py`.
- Propagate it only to `parallel_worktree_gate.py` and `state_sync_gate.py`;
  preserve every other child argv and the literal chain order.
- Add root/template propagation and malformed/naive refusal regressions to
  `tests/test_owner_governance_chain_parity.py`.
- Pass the existing fixed clock to the installed owner-governance invocation
  in `tests/test_template_smoke.py`.
- Refresh the intentional owner-governance divergence hashes in
  `agents/project/TEMPLATE-MIRROR-CONTRACT.json` and the installed host lock.

## Safety condition

Malformed or naive owner-governance `--now` must be rejected before any child
gate starts, with a bounded non-zero result and no traceback. Omitting `--now`
must retain the wall clock. No grace enlargement, expiry exception, claim or
pointer mutation, Git mutation, external action, or release action is allowed.
