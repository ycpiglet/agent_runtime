---
type: verification
id: W4B-2026-07-28-unit-task-ar-639-002-recheck-2
title: UNIT-TASK-AR-639-002 Independent W4b Approval Recheck
date: 2026-07-28
status: passed
signal: pass
verdict: APPROVE
verified_by: qa-20260728-task-ar-639-002-w4b-terra
verifier_role: qa-reviewer
reviewed_commit: a977c5a6
base_commit: 25123303
worker_identity: le-20260728-task-ar-639-002-terra
tags: [task-ar-639, unit-002, w4b, recheck, approved, state-sync]
---

# UNIT-TASK-AR-639-002 Independent W4b Approval Recheck

## Bottom Line

**APPROVE** at `a977c5a6`. The repair at `4f0e99cc` closes the three remaining
projection gaps reported by the prior recheck, while retaining all original
state-sync, lifecycle-recovery, worktree-integrity, schema, and template
guarantees. No blocker was reproduced.

This report preserves, rather than overwrites, the two earlier failed W4b
records:

- `reviews/W4B-2026-07-28-unit-task-ar-639-002.md`
- `reviews/W4B-2026-07-28-unit-task-ar-639-002-recheck.md`

## Independence and Scope

- Worker: `le-20260728-task-ar-639-002-terra`
- Independent verifier: `qa-20260728-task-ar-639-002-w4b-terra`
- Verifier role: `qa-reviewer`
- Reviewed range: `251233033d70c0f251216e183f8ff3764e805858..a977c5a6`
- Repair implementation commit: `4f0e99cc`
- W4a reviewed:
  `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625.json`

## Contradiction Matrix

| Scenario | Expected | Independent result | Verdict |
| --- | --- | --- | --- |
| Active worker targets completed task with an open sibling | block | `claim:task-invalid-lifecycle` regression passes | PASS |
| Active worker targets completed unit | block | `claim:unit-invalid-lifecycle` regression passes | PASS |
| Active worker targets planned/worker_ready/unknown task or unit | block | regression passes | PASS |
| Relative `.worktrees/TASK-*` path from a linked checkout | validate actual worker worktree | regression passes | PASS |
| Worker claim targets primary checkout | block | `claim:main-worktree` regression passes | PASS |
| Literal `overlay: true` matches verified task/unit | must not satisfy worker W2 | `verified-work:missing-lifecycle` | PASS |
| `overlay: false` or string `"true"` | remains worker claim | regression requires worker fields | PASS |
| Unit/task/claim taskset identifiers differ | block | `claim:unit-taskset-mismatch` | PASS |
| Pointer active task is done with an open sibling | block | `active-task:done` | PASS |
| Partial task/unit recovery marker | block | `verified-work:missing-lifecycle` | PASS |
| Two active workers with one primary pointer | additive projection allowed | regression passes | PASS |
| Valid TASK-AR-631 recovered history | one explicit watch only | live state-sync `block=0`, `watch=1` | PASS |

## Independent Adversarial Results

The following temporary fixtures were constructed independently from the test
suite and each produced the required block finding:

```text
overlay-verified= ['verified-work:missing-lifecycle:TASK-AR-720']
unit-taskset= ['claim:unit-taskset-mismatch:CLAIM-TEST-001']
pointer-done-sibling= ['active-task:done:TASK-AR-722']
partial-recovery= ['verified-work:missing-lifecycle:TASK-AR-724']
```

The focused state-sync suite also covers the original lifecycle, linked-path,
primary-checkout, literal-overlay, branch mismatch, recovery evidence, and
parallel-primary-pointer boundaries.

## Commands and Results

```text
python -m pytest tests/test_state_sync_gate.py tests/test_task_claim_dispatcher.py tests/test_work_schema_gate.py -q
# 80 passed in 4.46s

python scripts/state_sync_gate.py --check
# pass; findings=1, block=0, watch=1
# sole watch: recovery:without-claim:TASK-AR-631

python scripts/work_schema_gate.py --items --check
# pass; findings=0, warnings=0

python scripts/parallel_worktree_gate.py --check
# pass; claims=203, findings=0, watch=0

cmp -s scripts/state_sync_gate.py src/agent_runtime/templates/project/scripts/state_sync_gate.py
# exit 0 (root/template shared-gate parity)

python scripts/regen_host_lock_if_needed.py --check
# host lock up to date

python scripts/owner_governance_gate.py
# pass; only non-blocking advisory watches

python -m pytest tests/test_regen_host_lock_if_needed.py tests/test_lock_merge_driver.py tests/test_automation_rules_gate.py -q
# 29 passed in 0.84s

python -m pytest tests -q
# 2266 passed, 3 skipped, 4 warnings in 112.62s
```

## Approval Decision

- **Verdict: APPROVE.**
- The W4b identity is distinct from the worker identity.
- The implementation is eligible for the separate lifecycle owner to release
  `CLAIM-20260728-175515-task-ar-639-639002` using this evidence.
- This verifier did **not** execute `task_claim_dispatcher.py release`, push,
  merge, or alter implementation/lifecycle records.
