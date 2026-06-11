---
type: review
id: REVIEW-2026-06-11-agent-runtime-task-ar-298-eval-verification-registry
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [rsi, evaluation, verification, metrics, task-ar-298, verification]
---

# TASK-AR-298 Evaluation Verification Registry Closeout

## Bottom Line

- Summary: `TASK-AR-298` is complete for evaluation and verification registry contracts.
- Output: evaluation and verification registry docs now define how to add normalized records with `record_id`, `source_command`, `source_path`, `scope_boundary`, metric fields, and local-vs-provider-live boundaries.
- Boundary: this closes registry shape and documentation only; automated proposal scoring is still tracked by later RSI operating-system tasks.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| TDD red | pass | `test_task_ar_298_eval_and_verification_registry_contracts_are_declared` failed before registry docs declared `How To Add` and normalized source fields |
| TDD green | pass | `python -m pytest tests/test_rsi_operating_system_docs.py::test_task_ar_298_eval_and_verification_registry_contracts_are_declared -q`: `1 passed` |
| Evaluation registry | pass | `agents/project/evidence/evaluations/README.md` defines record shape, proposal metrics, seed evidence, and add procedure |
| Verification registry | pass | `agents/project/evidence/verification/README.md` defines command evidence shape, required closeout commands, and add procedure |
| Boundary | pass | Both docs distinguish `local_deterministic` from `provider_live`, remote, release, or external evidence |

## Insight

- The registry must be queryable by fields, not scraped from review prose after the fact.
- Proposal quality metrics require consistent source-command and scope metadata before any scoring can be trusted.
- Local deterministic proof and provider-live proof remain separate evidence classes.

## Decision

- Mark `TASK-AR-298` completed.
- Continue with `TASK-AR-299` to make failure and compound casebooks searchable.
- Keep normalized record consumption proposal-only until later engine and gate tasks are complete.

## Action Board

| Item | State | Next |
| --- | --- | --- |
| `TASK-AR-298` | completed | Archive from live board after board regeneration |
| `TASK-AR-299` | planned | Build failure and compound casebook registry |
| Eval/verification registries | ready | Consume through proposal scoring only after dedupe and quality checks |

## Risks / Blockers

- Risk: registry docs need later enforcement or script support to prevent drift.
- Risk: provider-live evidence may be confused with local deterministic evidence if producers do not set `scope_boundary`.
- Blocker: none for `TASK-AR-298` local scope.

## Next Steps

- Start `TASK-AR-299` before claiming failure or compound casebook completion.
- Reuse the registry field names in later proposal scoring and verification wrapper tasks.
