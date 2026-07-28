---
type: compound
title: v0.8 lifecycle, closeout, and CI friction
date: 2026-07-28
status: recorded
signal: watch
casebook: agents/project/casebooks/failure-and-compound-casebook.md
related: [TASK-AR-639, TASK-AR-640, TASK-AR-645, TASK-AR-646, TASK-AR-651, PR #353, PR #354, PR #355, PR #356, PR #357, PR #377, main run 30406516812]
---

# v0.8 lifecycle, closeout, and CI friction

TASK-AR-639 repaired the lifecycle control plane, but its own live execution
exposed recurring producer/consumer and phase-boundary defects. Recording them
before TASK-AR-640 prevents the next v0.8 units from normalizing manual
workarounds into operating practice.

## Repeated failure signatures

### 1. A W4a-green change can still be acceptance-incomplete

Independent W4b twice found cross-surface gaps after focused implementation
tests were green: lifecycle overlay exemptions were too broad, taskset and
pointer projections disagreed, and consumer-template schema parity was
incomplete. The implementation was locally correct at one surface but not
closed across every producer and consumer of the same tuple.

General lesson: any task that changes a durable lifecycle/configuration tuple
needs an adversarial matrix covering root, shipped template, active worker,
explicit overlay, taskset, pointer, and UI/read-model consumers. W4a evidence
is necessary but cannot substitute for that matrix.

Route: keep independent W4b mandatory for TASK-AR-640 through TASK-AR-647 and
add the reusable cross-surface fixture under TASK-AR-643 or TASK-AR-651.

### 2. Closeout evidence is produced in a form `work close` cannot consume

The W4b artifacts are Markdown review records, while `work close` accepts a
narrower evidence-reference shape. UNIT-001 and UNIT-002 both required
temporarily excluding the valid W4b reference, running close, then restoring
the evidence manually. That is a producer/consumer contract defect, not an
operator typo.

General lesson: every mandatory artifact emitted by one lifecycle phase must
have an end-to-end fixture proving the next phase consumes it without manual
projection edits.

Route: TASK-AR-645 must make task-linked compound/review evidence first-class
closeout input. TASK-AR-651 must include a no-manual-edit lifecycle smoke.

### 3. Released unit and active taskset phases are conflated

Collaboration governance expects released claims to be
`phase: taskset-completed`, even when a unit is honestly complete and its
parent taskset remains active. Operators must choose between a false taskset
completion claim and a persistent warning.

General lesson: unit completion, task completion, claim release, and taskset
completion are distinct facts. A phase vocabulary must not force one to imply
another.

Route: TASK-AR-645 should define the phase/evidence contract; TASK-AR-651
should block an RC if honest intermediate unit closure still requires a
warning waiver.

### 4. Claim bootstrap order previously created split-brain state

TASK-AR-639 encountered primary-checkout, relative-worktree, and claim-before-
worktree inconsistencies. The dispatcher is now stricter, but the corrected
sequence is not yet proven as a clean-host end-to-end fixture.

General lesson: claim persistence is the transaction boundary. A worker
worktree must be derived from a committed claim projection, never used to
retroactively justify one.

Route: TASK-AR-643 clean-host dependency/lifecycle smoke and the Bean Wiki
pilot must exercise the exact W2 order.

### 5. Temp-git cadence failure recurred after the original hardening

Main CI run `30350865552` failed once on Python 3.12 in
`test_each_critical_flag_halts_for_owner[failed_or_missing_critical_gate]`:
the result was `trigger-error` instead of the expected owner-required
decision. Exact PR CI had passed; the exact local test passed ten consecutive
runs; an unchanged failed-job rerun passed on Python 3.10/3.11/3.12.

The earlier fix correctly converted query failure into a loud error, but it
did not remove the temp-git flake. This is recurrence 3+ of
`ci-flaky-temp-git`, so a bare rerun policy is no longer sufficient.

Route: TASK-AR-651 must either add a bounded, observable retry at the remaining
git-query boundary with a deterministic regression fixture or explicitly
exclude the unstable mechanism from release-critical decisions.

TASK-AR-646 confirmed that the boundary remains release-critical. Its exact PR
CI passed, but main run `30406516812` attempt 1 failed on Python 3.11 in
`test_decision_record_is_agent_council_noncritical`: a temp-repo commit at
`chore: tick 22` exhausted six retryable attempts and ended with
`fatal: could not parse HEAD`. The PR did not modify that test, and an
unchanged workflow rerun passed Python 3.10/3.11/3.12. This raises the known
signature to recurrence 4+ and requires a canonical task-linked compound
record at
`agents/project/knowledge/compounds/records/COMPOUND-20260729-081348-temp-git-fixture-head-corruption-survives-bounde-2514bdcf5f65.json`;
preserving both workflow attempts is part of the evidence contract.

## Additional release watches

- `.githooks/post-merge` is shipped without its executable bit. TASK-AR-644
  owns cross-platform hook installation and doctor checks.
- Main CI reported Node 20 action deprecation annotations and
  `PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE`. TASK-AR-651 owns
  release workflow modernization and warning-summary readback.
- `recovered_without_claim` is a boolean concept stored through the current
  encoded-scalar compatibility path. Preserve current round-trip behavior, but
  audit semantic typing before claiming schema-v2 cleanliness.
- The July review-to-compound ratio exceeded the configured cadence. This
  record satisfies the immediate learning obligation; TASK-AR-645 must make
  the obligation task-linked rather than dependent on an operator noticing
  the aggregate warning.

## Feed-forward

- Casebook recurrence updated for `ci-flaky-temp-git`.
- TASK-AR-646 adds a canonical task/unit-linked `ci-flaky-temp-git` record and
  keeps TASK-AR-651 as its prevention owner.
- New casebook entries:
  `w4-green-cross-surface-gap`,
  `closeout-evidence-producer-consumer-gap`, and
  `released-unit-taskset-phase-conflation`.
- TASK-AR-640 starts only after its assumption record points at this compound
  and its bounded configuration design review.
