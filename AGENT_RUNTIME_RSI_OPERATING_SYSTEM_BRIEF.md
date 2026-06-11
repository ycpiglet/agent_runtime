---
type: brief
id: AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF
audience: owner
status: watch
signal: watch
score: 86
priority: High
tags: [rsi, evidence-to-proposal, failure-registry, evals, owner-brief]
---

# Agent Runtime RSI Operating System Brief

## Bottom Line

- Summary: registered `TASKSET-AR-RSI-OPERATING-SYSTEM` as the A안 follow-up to the completed RSI planning loop.
- Result: the next work is no longer just a planner; it is an Evidence-to-Proposal OS with evidence inboxes, evaluation/verification registries, failure and compound casebooks, proposal metrics, council review, A2A lifecycle verification, skill packaging, and bounded apply gates.
- Boundary: this is registration and scaffold documentation only. It does not claim A2A end-to-end execution, quantified proposal quality, or C-mode auto-apply is complete.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Taskset registered | pass | `TASK-AR-297` through `TASK-AR-305` |
| Conversation recorded | pass | `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md` |
| Evidence directories created | pass | `agents/project/evidence/` |
| Failure casebook created | pass | `agents/project/casebooks/failure-and-compound-casebook.md` |
| C-mode status | watch | latent option only; not active |
| Implementation state | watch | planned taskset, no completion claim |

## Insight

- The existing `TASKSET-AR-RSI-PLANNING` proved B-mode structure, proposal-first behavior, state-machine grounding, and verification gates.
- The missing layer is operating discipline: evidence must be collected in one shape, failures must be casebooked, eval and verification outputs must be queryable, and proposal quality must be measured.
- C-mode can remain valuable long-term, but only after repeated B-mode evidence shows proposal quality, regression closure, and low-risk apply safety.

## Decision

- Decision: adopt A안 as `TASKSET-AR-RSI-OPERATING-SYSTEM`.
- Decision: do not reopen `TASKSET-AR-RSI-PLANNING`; this is a follow-up taskset.
- Decision: preserve C안 as latent future architecture, not active implementation.
- Decision: treat failure and compound records as inputs to regression fixtures, gates, or explicit accepted watch states.

## Action Board

| Task | Action | Owner | Evidence |
| --- | --- | --- | --- |
| `TASK-AR-297` | Evidence inbox and conversation capture | lead_engineer | `agents/project/evidence/inbox/README.md` |
| `TASK-AR-298` | Eval and verification registry | evaluation-office | `agents/project/evidence/evaluations/README.md` |
| `TASK-AR-299` | Failure and compound casebook | rsi-lab | `agents/project/casebooks/failure-and-compound-casebook.md` |
| `TASK-AR-300` | Evidence-to-proposal engine contract | planning-coordinator | `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md` |
| `TASK-AR-301` | Council review and metrics | diversity-council | `DIVERSITY-COUNCIL-PROTOCOL.md` |
| `TASK-AR-302` | A2A lifecycle verification | evaluation-office | `scripts/a2a_lifecycle_gate.py` |
| `TASK-AR-303` | Latent C-mode and apply gate roadmap | risk-and-safety | `C-MODE-LATENT-ROADMAP.md` |
| `TASK-AR-304` | RSI OS skill layer | lead_engineer | `skills/rsi-planning-loop/SKILL.md` |
| `TASK-AR-305` | Taskset verification and handoff | lead_engineer | `scripts/verify_rsi_operating_system_taskset.py` |

## Risks / Blockers

- Risk: registries can become another archive unless proposal metrics and closeout gates consume them.
- Risk: C-mode language can be misread as approval for auto-apply; current state is latent watch only.
- Risk: A2A remains a documented evidence shape until `TASK-AR-302` verifies lifecycle execution.
- Blocker: none for registration; implementation must start at `TASK-AR-297`.

## Next Steps

- Start `TASK-AR-297` to harden evidence inbox schema and conversation capture.
- Then implement `TASK-AR-298` and `TASK-AR-299` so eval/verification and failure/compound evidence are queryable before proposal automation expands.
- Keep `TASKSET-AR-RSI-OPERATING-SYSTEM` planned until a claim starts it; current active UI taskset remains separate.

