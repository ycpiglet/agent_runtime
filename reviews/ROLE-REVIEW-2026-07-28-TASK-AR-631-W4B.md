---
title: TASK-AR-631 Independent W4b and Lifecycle Recovery Review
date: 2026-07-28
signal: watch
score: 96
verdict: APPROVE_CODE_REPAIR_LIFECYCLE
verified_by: codex-root-v080-recovery-20260728
verifier_role: independent-auditor
reviewed_commit: 8be1fe2442b62405e807a350c6378b5a77c501e9
base_commit: 8ff4bd059cdfbaa99450ec2b0cbcd42bd82b6bf4
tags: [task-ar-631, w4b, lifecycle-recovery, ui-console]
---

# TASK-AR-631 Independent W4b and Lifecycle Recovery Review

## Bottom Line

The product implementation at exact commit
`8be1fe2442b62405e807a350c6378b5a77c501e9` is approved. Focused and full
regression suites pass, the decision-screenfit acceptance behavior is present,
and no code-level blocker was found.

The work record was not merge-ready when reviewed: the task remained `planned`,
the unit remained `worker_ready`, no active or released claim existed, the unit
creation timestamp was later than its verification timestamp, and the task
declared an unsupported `nav_budget_gate.py --check` command. This review does
not fabricate a retroactive claim. It records the gap and permits a
lifecycle-only recovery before integration.

## Signal

signal: watch

| Check | Result | Evidence |
| --- | --- | --- |
| Diff review | pass | `main...8be1fe24`, 11 files, no unrelated product scope |
| Focused UI suite | pass | 385 passed |
| Full package suite | pass | 2237 passed, 3 skipped |
| i18n literal gate | pass | 2 files scanned, 0 findings |
| Navigation budget | pass | 7 top-level views, budget 7 |
| Taskset work gate | pass | 0 findings |
| Owner governance | pass | 0 blocking findings |
| Lifecycle trace | watch | implementation exists without a claim/release record |

## Findings

### F1 — lifecycle records disagree with implemented reality

- `TASK-AR-631` says `planned`.
- `UNIT-TASK-AR-631-001` says `worker_ready` with passed W4a evidence.
- The checkout contains the implementation commit.
- `work.py status` reports zero active claims.
- There is no durable TASK-AR-631 claim or W4b release record.

The repair must close the existing unit/task from real evidence and record the
claim absence as a process defect. A retroactive claim would imply W2 happened
before implementation and is prohibited.

### F2 — the task verification command was not executable as written

`scripts/nav_budget_gate.py` supports no `--check` option. The exact recorded
command exited with argument error. Running the supported command without the
flag passed. The task record is corrected as lifecycle metadata; product code
is unchanged.

### F3 — the unit timestamp was contradictory

The unit said it was created at 11:30 while its W4a evidence and `updated_at`
were stamped 11:12. The recovery uses the earliest durable evidence timestamp
and marks the timestamp quality `backfilled`; it does not present an invented
high-confidence start time.

## Independent Verification

Verifier `codex-root-v080-recovery-20260728` did not implement TASK-AR-631 and
did not share the worker conversation. The implementation commit attributes the
work to Claude Fable 5, satisfying the independent-instance boundary.

Commands executed:

```text
python -m pytest tests/test_ui_state.py tests/test_ui_console.py \
  tests/test_ui_console_e2e.py tests/test_ui_console_microinteractions.py -q
# 385 passed

python -m pytest tests -q
# 2237 passed, 3 skipped, 4 warnings

python scripts/i18n_literal_gate.py --check
# pass

python scripts/nav_budget_gate.py
# pass: top_level=7 budget=7

python scripts/taskset_work_gate.py --check
# pass

python scripts/owner_governance_gate.py
# pass, no blocking findings
```

## Decision

- Approve the TASK-AR-631 product diff.
- Repair and close the unit/task from durable W4a/W4b evidence.
- Do not create a fake historical claim.
- Register the missing claim-to-diff and projection-reconciliation enforcement
  as P0 work in the v0.8 Adoption and Enforcement taskset.
- Do not start TASK-AR-632 or other console expansion before that P0 taskset is
  registered and claimed.
