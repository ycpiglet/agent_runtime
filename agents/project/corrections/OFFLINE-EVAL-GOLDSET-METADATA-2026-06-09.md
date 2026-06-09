# Correction Proposal: Offline Eval Goldset Metadata

## Trigger

`scripts/offline_eval_gate.py` returned `status=block` for the current committed goldsets.

## Affected Datasets

- `agents/project/evals/overlay-routing-v1.jsonl`
- `agents/project/evals/gov-metadata-v1.jsonl`

## Required Correction

- Add `case_type` to every row.
- Add `source_refs` to every row.
- Add `query_contract` to every row.
- Add enough rows to cover `typical`, `edge`, `adversarial`, `ambiguous`, and `access-controlled` cases.

## Resolution

- status: resolved_for_goldset_readiness
- resolved_at: 2026-06-09
- evidence: reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json
- remaining_boundary: model-output answer accuracy scoring is still pending.

## Owner Routing

- owner: lead_engineer
- reviewer: independent_auditor
- release_route: hold_for_data
- expiry: 2026-07-02
