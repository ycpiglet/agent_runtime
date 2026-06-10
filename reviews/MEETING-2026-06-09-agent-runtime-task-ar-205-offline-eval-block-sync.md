# MEETING: TASK-AR-205 Offline Eval Block Sync

## 참석 역할

- Lead Engineer
- QA Reviewer
- Data Steward
- Release Manager

## Agenda

- Offline eval gate execution result review.
- Decide whether current goldsets can support `v0.1.8` release readiness.
- Route blocker into closeout state.

## Decision

- Current goldsets cannot support release readiness.
- The lane is not blocked by tooling anymore; it is blocked by data completeness.
- Release state route: `hold_for_data`.

## Required Data Additions

- Add `case_type` to every row.
- Add `source_refs` to every row.
- Add `query_contract` with scope, time window, tolerance, ambiguity, access level, and source tier.
- Cover policy-required case types: typical, edge, adversarial, ambiguous, access-controlled.
- Re-run `scripts/offline_eval_gate.py` after data expansion.
