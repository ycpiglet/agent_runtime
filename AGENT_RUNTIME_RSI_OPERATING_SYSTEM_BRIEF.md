---
type: brief
id: AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF
audience: owner
status: pass
signal: pass
score: 95
priority: High
tags: [rsi, evidence-to-proposal, failure-registry, evals, owner-brief]
---

# Agent Runtime RSI Operating System Brief

## Bottom Line

- Summary: completed local implementation of `TASKSET-AR-RSI-OPERATING-SYSTEM` as the A안 follow-up to the completed RSI planning loop.
- Result: the OS now has evidence inboxes, evaluation/verification registries, failure and compound casebooks, proposal contract fields, proposal metrics, council review blocking, deterministic A2A lifecycle verification, skill packaging, and a named closeout verifier.
- Boundary: this proves local deterministic Evidence-to-Proposal OS behavior only. C-mode auto-apply and provider-live A2A transport remain latent watch items.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Taskset registered | pass | `TASK-AR-297` through `TASK-AR-305` |
| Conversation recorded | pass | `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md` |
| Evidence directories created | pass | `agents/project/evidence/` |
| Failure casebook created | pass | `agents/project/casebooks/failure-and-compound-casebook.md` |
| Proposal contract | pass | `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`, `schemas/planning-proposal.schema.json` |
| A2A lifecycle gate | pass | `scripts/a2a_lifecycle_gate.py`, `tests/test_a2a_lifecycle_gate.py` |
| Skill layer | pass | `skills/rsi-planning-loop/SKILL.md`, `skills/failure-to-regression/SKILL.md` |
| C-mode status | watch | latent option only; not active |
| Implementation state | pass | `scripts/verify_rsi_operating_system_taskset.py` closeout path |

## Insight

- The existing `TASKSET-AR-RSI-PLANNING` proved B-mode structure, proposal-first behavior, state-machine grounding, and verification gates.
- The missing operating discipline layer is now represented in durable docs, schema fields, scripts, tests, skills, and closeout gates.
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

- Risk: registries can become another archive unless proposal metrics and closeout gates keep consuming them.
- Risk: C-mode language can be misread as approval for auto-apply; current state is latent watch only.
- Risk: A2A provider-live transport remains unproven; current proof is local deterministic lifecycle reconstruction.
- Blocker: none for local implementation closeout.

## Next Steps

- Run the named closeout verifier and attach `reviews/RSI-OPERATING-SYSTEM-TASKSET-VERIFY.json`.
- Open the PR from `codex/taskset-ar-rsi-os` and wait for merge.
- Keep C-mode latent until repeated B-mode pass evidence, rollback evidence, and explicit Owner policy allow a specific low-risk action class.

