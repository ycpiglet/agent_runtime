---
id: RETRO-2026-07-29-task-ar-646-model-routing
title: TASK-AR-646 model-routing retrospective
kind: retrospective
status: completed
signal: pass-with-followup
date: 2026-07-29
task_id: TASK-AR-646
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
---

# TASK-AR-646 Model-Routing Retrospective

## Outcome

TASK-AR-646 made routine model routing lower-cost by default and made its
application auditable without claiming unobserved savings. Root and shipped
template routing assets are exact mirrors; generic, provider-worker,
auto-dispatch, and native Codex paths now carry correlated requested,
resolved, observed, usage, and cost-availability state. Deterministic lookup
can finish without a model call, while explicit ambiguity, data-integrity,
security, cross-cutting, external-effect, high-risk, and repeated-failure
signals escalate visibly.

The exact implementation head `7d61659ae690c85225d8010dc1e2861f90654f5a`
passed W4a and an independent W4b at 98/100. PR
[#377](https://github.com/ycpiglet/agent_runtime/pull/377) merged as
`50cd566305687a58246bfccdaa9af82d9d2cae2a`. No live billable provider call,
credential write, consumer-repository mutation, global Codex configuration,
version change, tag, publication, release, or deployment occurred.

## What Worked

- Failure-first verification preserved the initial timeout/invalid-command
  evidence and produced a separate passing task record instead of rewriting
  history.
- Independent W4b retested the exact implementation head across root,
  shipped template, clean-host Doctor, native bridge, provider worker,
  deterministic-first, and economic-evidence boundaries.
- Requested and configured model state never became observed state by
  inference. The independent verifier's exact model identifier was likewise
  recorded as unavailable because the runtime did not expose it.
- Provider equivalence matrices made same-model routes visibly ineffective;
  token deltas remain non-monetary, and monetary deltas require comparable
  same-currency billed-cost evidence.
- The implementation reused the native collaboration execution surface and
  only added an auditable bridge rather than creating another executor.

## Friction and Corrections

- The first task verification used a one-second diagnostic timeout and still
  contained a prose bullet parsed as a shell command. The registered
  verification list was corrected to executable commands, and both the failed
  and passing records were retained.
- Claim release updated the canonical claim but initially left
  `BACKLOG-BOARD.md` and `agents/project/NEXT-SESSION-POINTER.yml` stale.
  Pre-commit gates caught the disagreement; the canonical board generator and
  an explicit pointer update restored the projection before integration.
- Main workflow
  [30406516812](https://github.com/ycpiglet/agent_runtime/actions/runs/30406516812)
  attempt 1 failed on Python 3.11 in
  `test_decision_record_is_agent_council_noncritical`. Its temporary
  repository reached `chore: tick 22`, exhausted six retryable fixture
  commits, and reported `fatal: could not parse HEAD`. The PR had not changed
  that test. An unchanged workflow rerun passed Python 3.10, 3.11, and 3.12,
  confirming another recurrence of the known `ci-flaky-temp-git` signature,
  not evidence that may be discarded as a bare rerun.
- As in TASK-AR-645, `work verify` retained both failed and passing attempts in
  active `evidence_refs`, while `work close` requires only current passing
  evidence there. W6 preserved the failed artifact and index entry, moved its
  link to the superseded-attempt section, and kept the passing record active.

## Durable Rules

1. Every registered verification bullet must be executable; explanatory prose
   belongs outside the command list.
2. Requested, selected, resolved, and observed models are different facts.
   Missing observations remain unavailable and cannot support application or
   savings claims.
3. Same-model tier mappings are not economic savings. Token evidence and
   billed monetary evidence must remain separately named and gated.
4. Claim, board, archive, pointer, and closeout projections must be checked as
   one lifecycle transaction before integration.
5. TASK-AR-651 must harden or remove the release-critical temp-git boundary
   with observable recovery and a deterministic regression fixture. It must
   also prove fail-then-pass-then-close without manual evidence metadata
   edits.
6. Bean Wiki and Allimbot pilots must measure actual routing/application
   evidence and deterministic no-call outcomes; configured model differences
   alone are not savings evidence.

## Evidence

- W4a: `reviews/W4A-2026-07-29-unit-task-ar-646-001.md`
- Independent W4b:
  `reviews/W4B-2026-07-29-unit-task-ar-646-001.md`
- Superseded failed task verification:
  `reviews/VERIFY-2026-07-29-task-ar-646-20260729073326.json`
- Passing task verification:
  `reviews/VERIFY-2026-07-29-task-ar-646-20260729073520.json`
- Passing unit verification:
  `reviews/VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848.json`
- Canonical compound record:
  `agents/project/knowledge/compounds/records/COMPOUND-20260729-081348-temp-git-fixture-head-corruption-survives-bounde-2514bdcf5f65.json`
- PR CI workflow: `30406275099`
- Main workflow: `30406516812`, attempt 1 failed with the known signature;
  unchanged attempt 2 passed the supported Python matrix.
