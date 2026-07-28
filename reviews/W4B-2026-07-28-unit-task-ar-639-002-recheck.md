---
type: verification
id: W4B-2026-07-28-unit-task-ar-639-002-recheck
title: UNIT-TASK-AR-639-002 Independent W4b Recheck
date: 2026-07-28
status: blocked
signal: fail
verdict: CHANGES_REQUIRED
verified_by: qa-20260728-task-ar-639-002-w4b-terra
verifier_role: qa-reviewer
reviewed_commit: 6fa6bd4f
base_commit: 25123303
worker_identity: le-20260728-task-ar-639-002-terra
tags: [task-ar-639, unit-002, w4b, recheck, state-sync, lifecycle-projection]
---

# UNIT-TASK-AR-639-002 Independent W4b Recheck

## Bottom Line

The repair at `6fa6bd4f` resolves all five blockers in the first W4b report:
completed and pre-dispatch canonical lifecycle states now block worker claims,
relative worker paths resolve from a linked checkout, and primary-checkout
claims are rejected. It is still **not approved**. Three required adjacent
projection seams silently pass, so the active claim must not be released.

The original blocking evidence remains intact at
`reviews/W4B-2026-07-28-unit-task-ar-639-002.md`.

## Independence and Scope

- Worker: `le-20260728-task-ar-639-002-terra`
- Independent verifier: `qa-20260728-task-ar-639-002-w4b-terra`
- Verifier role: `qa-reviewer`
- Reviewed range: `251233033d70c0f251216e183f8ff3764e805858..6fa6bd4f`
- Latest W4a reviewed:
  `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401.json`

## Recheck Matrix

| Scenario | Expected | Observed | Result |
| --- | --- | --- | --- |
| Active claim targets completed task while sibling remains open | block | regression test passes with `claim:task-invalid-lifecycle` | PASS |
| Active claim targets completed unit | block | regression test passes with `claim:unit-invalid-lifecycle` | PASS |
| Active claim targets planned/worker_ready/unknown canonical task or unit | block | regression test passes | PASS |
| Linked checkout validates primary-root-relative `.worktrees/TASK-*` claim path | pass | regression test passes | PASS |
| Active claim targets primary checkout | block | regression test passes with `claim:main-worktree` | PASS |
| Explicit overlay matching verified task/unit counts as a historical worker W2 claim | block: missing worker claim must require recovery | no block finding | FAIL |
| Active worker claim's unit taskset disagrees with task/claim taskset | block | no block finding | FAIL |
| Pointer `active_task` is completed while sibling task remains open | block | no block finding | FAIL |
| Recovery marker exists on task but not unit | block | `verified-work:missing-lifecycle` | PASS |

## Blocking Findings

### F1 — overlay claims bypass the worker-claim/recovery requirement

`_claim_for_item` currently returns true for every claim record with matching
`task_id` and `unit_id`. It does not exclude explicit overlays. Therefore a
synthetic `overlay: true` claim matching a verified task and unit suppresses
`verified-work:missing-lifecycle`, despite no worker W2 claim and no recovery
record.

Isolated fixture result:

```text
overlay-counts-as-W2: []
```

The empty list is the complete block finding list. This violates the explicit
overlay boundary: overlays are not worker execution and cannot establish a
historical worker lifecycle trace.

### F2 — unit taskset correlation is not checked

`_validate_active_claim` checks `claim.task_set_id` against the task, but it
does not compare `unit.task_set_id` with the task or claim. A claim can thus
name a canonical task and unit from different tasksets while satisfying every
other active-worker projection check.

Isolated fixture result:

```text
unit-taskset-disagrees: []
```

### F3 — completed primary pointer task is accepted while its taskset is open

The pointer branch only rejects `taskset:active-but-complete`. If the pointer
selects a completed task and another task in that taskset remains open, the
gate has no finding. This permits the UI/pointer projection to identify a
completed task as the active task.

Isolated fixture result:

```text
pointer-completed-with-open-sibling: []
```

## Commands and Results

```text
python -m pytest tests/test_state_sync_gate.py -q
# 23 passed in 0.57s

python -m pytest tests/test_task_claim_dispatcher.py tests/test_work_schema_gate.py -q
# 54 passed in 3.96s

# Independent temporary-fixture adversarial check
# overlay-counts-as-W2: []
# unit-taskset-disagrees: []
# pointer-completed-with-open-sibling: []
# task-recovery-unit-missing: [('block', 'verified-work:missing-lifecycle:TASK-AR-714')]

python scripts/state_sync_gate.py --check
# pass; block=0, watch=1
# only live watch: recovery:without-claim:TASK-AR-631

python scripts/work_schema_gate.py --items --check
# pass; findings=0, warnings=0

python scripts/parallel_worktree_gate.py --check
# pass; claims=203, findings=0, watch=0

python scripts/regen_host_lock_if_needed.py --check
# host lock up to date

python scripts/owner_governance_gate.py
# pass; only advisory non-blocking watches

python -m pytest tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_automation_rules_gate.py -q
# 29 passed in 0.87s

python -m pytest tests -q
# 2263 passed, 3 skipped, 4 warnings in 106.61s
```

Root/template `state_sync_gate.py` parity is exact (`cmp` exit 0), and the
regenerated host lock is current. The live recovery shape for TASK-AR-631
remains the sole intended state-sync watch.

## Required Narrow Repair

1. Make `_claim_for_item` exclude explicit overlay claims; only a worker claim
   may satisfy the verified historical lifecycle requirement. Add a regression
   test where an overlay matches a verified task/unit without recovery.
2. For every active non-overlay worker claim, require the unit's
   `task_set_id` to equal both the canonical task's `task_set_id` and the
   claim's `task_set_id`. Add a mismatch regression test.
3. Reject a pointer `active_task` whose canonical task is done, even when its
   taskset has another open task. Add the open-sibling regression test.
4. Mirror root/template changes, refresh the host lock, retain the existing
   completed/pre-dispatch, linked-path, primary-checkout, strict-overlay,
   recovery, and parallel-primary-pointer behavior.

## Decision

- **Verdict: CHANGES_REQUIRED.**
- Do not release `CLAIM-20260728-175515-task-ar-639-639002`.
- Do not overwrite or supersede the first failure evidence; this is a separate
  recheck record.
- Require a fresh independent W4b after the three listed projection checks and
  their root/template regression coverage are repaired.
