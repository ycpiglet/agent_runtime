---
type: review
id: REVIEW-2026-06-11-agent-runtime-task-ar-297-evidence-inbox-contract
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [rsi, evidence, inbox, conversation-record, task-ar-297, verification]
---

# TASK-AR-297 Evidence Inbox Contract Closeout

## Bottom Line

- Summary: `TASK-AR-297` is complete for evidence inbox and conversation capture contract hardening.
- Output: `agents/project/evidence/README.md` and `agents/project/evidence/inbox/README.md` now declare task/taskset links, observed failure or signal, proposed routing, dedupe, owner boundary, and quality-check fields before proposal generation.
- Boundary: this closes the registry contract only; evaluation/verification registry work remains `TASK-AR-298`, and proposal automation remains later tasks in `TASKSET-AR-RSI-OPERATING-SYSTEM`.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| TDD red | pass | `tests/test_rsi_operating_system_docs.py` first failed because `task_set_id` and related contract fields were missing |
| TDD green | pass | `python -m pytest tests/test_rsi_operating_system_docs.py -q`: `1 passed` |
| Evidence registry | pass | `agents/project/evidence/README.md` defines required record fields and proposal quality-check boundary |
| Inbox contract | pass | `agents/project/evidence/inbox/README.md` defines intake fields, dedupe, routing, and quality-check rules |
| Conversation record | pass | `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md` records A option registration, eval/verification records, failure/compound casebooks, and latent C option |

## Insight

- The registration scaffold was close, but it did not explicitly require `task_set_id`, `observed_failure`, `observed_signal`, `proposed_routing`, or `quality_check`.
- Those fields are the minimum shape needed to keep raw evidence from becoming unreviewed task churn.
- Conversation evidence remains an input to proposal review, not direct authority to mutate backlog, release, or skill state.

## Decision

- Mark `TASK-AR-297` completed.
- Continue `TASKSET-AR-RSI-OPERATING-SYSTEM` with `TASK-AR-298` for evaluation and verification record registries.
- Keep C-mode latent and proposal-only until later bounded gate work proves safety.

## Action Board

| Item | State | Next |
| --- | --- | --- |
| `TASK-AR-297` | completed | Archive from live board after board regeneration |
| `TASK-AR-298` | planned | Create evaluation and verification record registry |
| Evidence inbox | ready | Use only after dedupe and quality checks |

## Risks / Blockers

- Risk: documents alone do not enforce proposal quality; enforcement belongs in later RSI OS tasks.
- Risk: owner conversation records must stay source evidence, not bypass review.
- Blocker: none for `TASK-AR-297` local scope.

## Next Steps

- Start `TASK-AR-298` before claiming evaluation or verification registry completion.
- Keep `tests/test_rsi_operating_system_docs.py` as the contract guard for evidence inbox fields.
