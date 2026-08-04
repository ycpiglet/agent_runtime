---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final
title: TASK-AR-659 Owner-Bound Recovery Commands Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T16:25:00+09:00
task_id: TASK-AR-659
unit_id: UNIT-TASK-AR-659-001
claim_id: CLAIM-20260803-143123-task-ar-659-cfc8
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: independent-context-isolated-auditor-task-ar-659
reviewer_role: independent-auditor
status: accepted
signal: pass
verdict: ACCEPT
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
rounds: 4
audited_commit: 6ef3d03e
head_commit: 14844d43a6cf997bdd5a9869229f5d59ef325f25
head_tree: ac28ffe821f9061fb496b715b3b9ba95dd3f2bdb
independence_status: independent_context_isolated
claim_lease_status_at_authorship: live
implementation_reviewed: true
w4b_acceptance: true
release_authorized: false
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-659-001-recovery-commands.md
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-659-001-20260803160906.json
compound_ref: agents/project/knowledge/compounds/records/COMPOUND-20260803-150241-give-every-claim-state-a-registered-exit-before-c0729965fea7.json
tags: [w4b, task-ar-659, claim-authority, recovery, accept]
---

# TASK-AR-659 owner-bound recovery commands final independent W4b

## Bottom Line

`ACCEPT — P0: 0, P1: 0, P2: 0`, after four adversarial rounds that produced
1 P0, 5 P1, and 8 P2 findings, all closed.

The reviewer was context-isolated, did not share the worker conversation, and
was explicitly instructed not to manufacture nits to justify another REVISE.
Its closing statement: *"I found nothing else worth reporting and am not going
to invent anything."*

## Round history

| Round | Verdict | What it caught |
|---|---|---|
| 1 | `REVISE — P0 1, P1 2, P2 3` | `--now` defeated the live-claim refusal; deadline-less claims still exit-less; adopt minted scope; activate-store unattributed; signal reached no consumer; owner id unbounded |
| 2 | `REVISE — P1 3, P2 5` | The worker's own P1 repair introduced a regression making adopted claims permanently un-renewable; only the rarest lease shape was fixed; spec-less scope hole still open |
| 3 | `REVISE — P1 2, P2 2` | The worker's spec-less replan gate compared the claim to itself and could never fire; the new flag ended claims with readable future deadlines |
| 4 | **`ACCEPT`** | — |

Every P1 in rounds 2 and 3 was a defect in a previous *repair*, not in the
original implementation. That is the substantive finding of this review: the
worker's self-review (W4a) caught one real P1 but missed the P0 entirely, and
each subsequent fix needed independent challenge.

## Verified in round 4

**The `git checkout --` incident lost nothing.** During round-3 repair the
worker ran `git checkout -- scripts/task_claim_dispatcher.py` and discarded
three uncommitted fixes, then re-applied them. Four independent lines of
evidence confirm the re-apply was complete:

1. `git diff c2e7f239 6ef3d03e` on the dispatcher contains exactly three
   hunks, all additive; no deletions of prior work anywhere in the file.
2. `claim_reaper.py`, `claim_reaper_hook.py`, `deadlock_watchdog.py` are
   byte-identical between the two commits.
3. A 19-marker inventory of every invariant established in rounds 1-3 is
   present in the audited file.
4. The classic partial-re-apply symptom is absent: `_stamp_recovery` has
   exactly two call sites and both pass the new parameter.

**The liveness-evidence boundary is correct in both directions.** Eight shapes
probed; every shape carrying future or in-grace evidence is refused with or
without the flag, and every provably dead shape remains endable. The
`== grace` case being terminalizable matches the reaper's own
`deadline <= now - grace` rule, so it is consistent rather than off-by-one.
The flag did not become useless.

**The spec-less gate closes the bypass without creating a dead end.** A
spec-less claim can no longer self-bless arbitrary scope, and is still
adoptable with a properly registered replan.

**The renewability fixture is honest.** It invokes the real
`plan_assumption_gate.py record` with a live anchor rather than hand-writing
the registry or monkeypatching `_accepted_replan_ref`, and was confirmed red
by reintroducing the regression on a throwaway copy.

**`recovery_evaluated_at`** absent in 8 of 8 runs without `--now`; present and
correct with it.

**`_legacy_claim` switched to spec-backed** weakened nothing; each dependent
test still refuses for its own stated reason.

## Head advance during review

The audited candidate is `6ef3d03e`. HEAD advanced to `14844d43` mid-review:
test-only, +62 lines, a parametrized boundary test whose matrix the reviewer
had independently derived. All four production scripts are byte-identical
between the audited candidate and HEAD, verified per-file. The audit stands.

## Gate and suite state

```
six-suite pytest (PYTHONPATH=src)   429 passed, 2 skipped  (433 at HEAD)
template_mirror_gate --check        findings=0
plan_assumption_gate --check        pass, findings=0
plan anchors                        64, 0 dropped, 0 added, 0 stale
tests/test_claim_guard.py           21 failed / 15 passed  (pre-existing baseline, unchanged)
```

## Observation carried forward, not a finding

The two cap tests (`owner id`, `reason`) assert only on returncode and
file-unchanged, so they would tolerate a future shift in refusal reason. The
anon-owner test pins its message; those two do not.

## Not granted

Unit acceptance is recommended, but this record grants no release, tag, push,
publish, or deploy authorization, and no consumer project was touched. The
pre-existing `tests/test_claim_guard.py` baseline is unchanged and remains
unowned by this unit.
