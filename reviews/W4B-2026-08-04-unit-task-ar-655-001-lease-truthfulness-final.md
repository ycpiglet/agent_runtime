---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-04-unit-task-ar-655-001-lease-truthfulness-final
title: TASK-AR-655 Lease Truthfulness Final Independent W4b
date: 2026-08-04
created_at: 2026-08-04T14:10:00+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260804-121045-task-ar-655-0427
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: independent-context-isolated-auditor-task-ar-655
reviewer_role: independent-auditor
status: accepted
signal: pass
verdict: ACCEPT
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
rounds: 11
audited_commit: a50392bc6f7054aa7204fce2d74b72a2139cc56c
audited_tree: cdcdda9d6f2bf1b770aa16a7ed55a98c5052cac7
independence_status: independent_context_isolated
claim_lease_status_at_authorship: live
implementation_reviewed: true
w4b_acceptance: true
release_authorized: false
supersedes: reviews/W4B-2026-08-03-unit-task-ar-655-001-type-strict-pointer-final.md
blocker_closed_by: reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md
tags: [w4b, task-ar-655, lease-truthfulness, claim-authority, accept]
---

# TASK-AR-655 lease truthfulness final independent W4b

## Bottom Line

`ACCEPT — P0: 0, P1: 0, P2: 0`, after eleven adversarial rounds against a
context-isolated reviewer.

The prior W4b (`REVISE — P1 1`) is superseded. Its blocking finding —
pre-mutation-field claims could neither heartbeat nor renew — was closed by
TASK-AR-659, and this reviewer verified that independently by rebuilding the
legacy claim shape and driving heartbeat → adopt → renew end to end rather
than taking AR-659's acceptance on faith.

The lease is live: this record was authored at 14:10 against a claim expiring
15:36. The predecessor review was invalidated by materialising 23 seconds
after its lease expired; that failure is not repeated.

## Round history

| Round | Verdict | Substance |
|---|---|---|
| 1 | `REVISE P1 2, P2 3` | `heartbeat` never validated `scope_binding`; `_mutation_now` was an unclamped authority seam |
| 2 | `REVISE P1 1, P2 1` | the overlay exemption keyed on a self-asserted flag |
| 3 | `REVISE P1 1, P2 1` | the replan gate compared the claim to itself and could never fire |
| 4 | `REVISE P1 2, P2 2` | `--now` clamp confirmed; deadline-less and torn-lease classes still exit-less |
| 5 | `REVISE P1 0, P2 2` | the whole false-positive class traced to one degenerate fixture |
| 6 | `REVISE P1 0, P2 2` | create and the mutation path disagreed about validity |
| 7 | `REVISE P1 1, P2 1` | a guard was weakened to keep an invalid fixture green |
| 8 | `REVISE P1 0, P2 2` | fifth create/mutate field: frontmatter ids |
| 9 | `REVISE P1 0, P2 1` | sixth field: the resolver was shared, the comparison was not |
| 10 | `REVISE P1 0, P2 1` | the canonical pin ran on two of three paths |
| 11 | **`ACCEPT`** | — |

Every P1 from round 2 onward was a defect in a previous *repair*, not in the
original implementation. The worker's own W4a caught one real P1 and missed
the round-1 P0-class clock defect entirely.

## What convergence actually required

The reviewer's measured record, and the most transferable result here:

- **Subtractive changes — removing a divergence or an exemption — went 6 for 6.**
- **Additive compensating checks went 0 for 4.**

Two changes closed whole families rather than single defects, and both moved
an invariant from "a test we remembered to write" into "code both paths must
call":

1. **De-degenerating `_write_routing_work`** (round 6). The fixture behind
   nearly every claim test declared one target file and no `stop_condition`,
   so every claim-to-spec comparison was evaluated where both sides were
   trivially equal. Making it realistic turned heartbeat, renew, and adopt red
   simultaneously in the existing suite with no new tests written.
2. **Extracting `_scope_contract_error`** (round 10). Canonical spec location,
   spec resolution, and `target_files` component equality in one predicate
   called from both `_claim_creation_errors` and `_validate_mutation_authority`,
   so "whatever heartbeat refuses, create refuses" holds by construction.

## The final finding and why the obvious fix was wrong

Round 10 left the canonical pin on heartbeat only, so a claim anchored to an
unregistered spec could not beat but could be renewed indefinitely. The
tempting fix — share the whole contract with renew — would have broken renew,
which exists to reconcile drift against an accepted replan.

`check_footprint=False` on the renew path was adjudicated against the criterion
that made the overlay flag illegitimate, and passes all three tests:

- **Provenance**: a call-site literal, one occurrence, unreachable from any
  claim edit. The overlay flag was read out of the artifact under validation.
- **No weaker path**: renew refuses a widened footprint on *stricter* grounds
  via `_accepted_replan_ref`, verified empirically — heartbeat and renew both
  refuse, file byte-unchanged, and still un-beatable afterwards.
- **It prevents a contradiction** rather than creating an exemption.

Recorded residual, not a defect: that "no weaker path" property rests on
`_accepted_replan_ref`, a different mechanism. If the replan gate is ever
weakened, renew silently becomes the lenient path and nothing in
`_scope_contract_error` would notice. The coupling and its three guarding
tests are named in the `check_footprint` docstring.

## Operational evidence

Worth more than any test result here. During this review the claim's lease
expired overnight, ~16 hours past deadline, still `status: claimed` — the
exact shape that opened this unit. Because it was `mode: worker`,
`claim_reaper --apply` recovered it in one command with no owner action and no
hand-edited JSON. The `mode: orchestrator` claim that started the unit sat
expired and invisible for 5.4 hours, deadlocked its own task set, and needed a
hand-written terminalize under Owner authority plus a whole recovery task.

Same failure, twelve hours apart, with and without the fix.

## Gate and suite state

```
20-file set, umask 0077     1104 passed, 2 skipped
20-file set, umask 0002     1 failed  (P2-3, owned by TASK-AR-648)
template_mirror_gate        findings=0
state_sync_gate             pass, findings=0
plan_assumption_gate        pass, findings=0, anchors 64
tests/test_claim_guard.py   21 failed / 15 passed - the AR-648 umask defect
```

## Open, and not this unit's to close

- **The umask-dependent private-index defect** in `claim_guard.py`: `chmod 0600`
  precedes a `git add` that rewrites the index as `0666 & ~umask`, so
  `parallel_worktree_gate` never recognises the claim-commit transaction on a
  default-umask machine. Routed to TASK-AR-648. The 21-red claim-guard baseline
  is that defect, not this unit's.
- **The `stop_condition` migration tolerance**, closed by agreement in round 7;
  heartbeat-side healing withdrawn in round 8 by the reviewer.

## Not granted

Unit acceptance is recommended. This record grants no release, tag, push,
publish, or deploy authorization. No consumer project was touched.
