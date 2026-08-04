---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: replan
status: accepted
created_at: 2026-07-30T16:31:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-652-001-final-approval.md
tags: [task-ar-652, w4b, replan, route-assertion, receipt-integrity]
---

# TASK-AR-652 final-approval W4b repair replan

## Bottom Line

The independent final-approval review closed the previous governance finding
and found two remaining P1 integrity defects inside the already registered
routing and receipt footprint. This replan keeps the task, unit, acceptance
criteria, consumer boundary, and release boundary unchanged. It narrows the
next candidate to the two reproduced defects and their failure-first tests.

## Reproduced Findings

1. Partial `tier_route` and `provider_route` dictionaries could choose the
   authority against which they were checked. A partial requested tier or the
   registered `codex-agent` provider therefore reached the executable prompt
   or call-message boundary without a separate authority input.
2. A native receipt could claim
   `resolved_reasoning_source=unsupported`, omit observed reasoning, and become
   eligible for token and billed-cost savings. Both the finalizer and the
   report-level gate trusted the receipt string.

## Decision

- Resolve requested tier only from the separate request input or the role
  default, and provider only from the separate provider input or the documented
  native default. Treat both supplied route dictionaries as assertions only.
- Add partial-tier, partial-provider, and mixed negatives at both executable
  dispatch boundaries.
- Expose provider reasoning capability from the canonical routing map with
  fail-closed `required`, `unsupported`, and `unknown` states.
- Require an observed reasoning effort whenever a resolved effort exists or
  either configured/observed provider is canonically reasoning-capable.
- Permit missing observed reasoning only for a canonically registered
  unsupported provider whose receipt also records `unsupported`.
- Cover forged native baseline and actual rows for token and monetary
  eligibility, while preserving a positive `codex-agent` provider-worker path.
- Regenerate the managed fixture host lock because packaged template hashes
  changed.

## Failure-First Evidence

- Partial assertion selection: `4 failed, 2 passed`; the two pre-existing
  passing cases already failed closed through the message boundary's explicit
  `auto` request.
- Native unsupported-source and canonical provider capability selection:
  `3 failed` plus one missing-API failure in each root/template routing suite.
- After repair, the same focused selections pass `6`, `3`, `1`, and `1`
  respectively.

## Invariants

- No live provider, credential, provider account, dependency, consumer
  primary, database, broker, notification, deploy, push, tag, version,
  publication, or release is authorized.
- No token or monetary savings claim is made; the tests prove only
  evidence-eligibility behavior.
- The claim remains `claimed` until a fresh independent W4b approves an exact
  clean candidate.
- The accepted target-file footprint from the prior scope amendment remains
  sufficient; no new production subsystem is added.

## Verification Plan

1. Run the focused failure-first selections after repair.
2. Run the required root, six-module template, SDK, and taskset suites.
3. Run the full Runtime suite with credential variables removed.
4. Regenerate and check the managed fixture host lock.
5. Check runtime assets, template mirrors, evidence index, taskset state,
   taskset T3 assumptions, and integrated Owner governance.
6. Record W4a against the implementation commit, then request a fresh
   independent W4b against the exact final candidate.
