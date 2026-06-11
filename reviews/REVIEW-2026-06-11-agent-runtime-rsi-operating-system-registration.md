---
type: review
id: REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration
audience: owner
status: pass
signal: pass
score: 92
priority: High
tags: [rsi, evidence-to-proposal, taskset, registration]
---

# RSI Operating System Registration Review

## Bottom Line

- Summary: registered `TASKSET-AR-RSI-OPERATING-SYSTEM` as the A안 implementation path.
- Task range: `TASK-AR-297` through `TASK-AR-305`.
- Boundary: this is a planned taskset registration. It does not claim the Evidence-to-Proposal OS is implemented.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Owner request captured | pass | `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md` |
| Task files created | pass | `agents/lead_engineer/tasks/TASK-AR-297.md` through `TASK-AR-305.md` |
| Plan created | pass | `docs/superpowers/plans/2026-06-11-rsi-operating-system-taskset.md` |
| Evidence registry scaffolded | pass | `agents/project/evidence/README.md` |
| Casebook scaffolded | pass | `agents/project/casebooks/failure-and-compound-casebook.md` |
| C-mode boundary | watch | latent option only |

## Insight

- The review gap was not that RSI planning lacked concepts; it lacked operating record discipline and measurable quality loops.
- A안 fits the current repo better than a full agent-department runtime because it strengthens the existing B-mode evidence path first.
- The C option should remain visible but blocked until proposal metrics, A2A lifecycle proof, and low-risk apply evidence are repeated.

## Decision

- Decision: register A안 as `TASKSET-AR-RSI-OPERATING-SYSTEM`.
- Decision: use `agents/project/evidence/` and `agents/project/casebooks/` as durable query surfaces.
- Decision: implementation starts at `TASK-AR-297`; no C-mode auto-apply is approved.

## Action Board

| Task | Action | Owner | Evidence |
| --- | --- | --- | --- |
| `TASK-AR-297` | Evidence inbox and conversation capture | lead_engineer | evidence inbox docs |
| `TASK-AR-298` | Eval and verification registry | evaluation-office | eval/verification docs |
| `TASK-AR-299` | Failure and compound casebook | rsi-lab | casebook docs |
| `TASK-AR-300` | Proposal engine contract | planning-coordinator | contract/schema updates |
| `TASK-AR-301` | Council metrics | diversity-council | structured verdict metrics |
| `TASK-AR-302` | A2A lifecycle proof | evaluation-office | deterministic lifecycle gate |
| `TASK-AR-303` | Latent C-mode apply gate | risk-and-safety | roadmap/checklist |
| `TASK-AR-304` | Skill layer | lead_engineer | RSI/failure skills |
| `TASK-AR-305` | Verification closeout | lead_engineer | taskset verification wrapper |

## Risks / Blockers

- Risk: evidence registries can drift unless future gates read them.
- Risk: proposal precision and recall need accepted/rejected proposal history before they become meaningful.
- Risk: A2A lifecycle remains watch until a deterministic fixture and gate exist.
- Blocker: none for registration.

## Next Steps

- Run board generation and focused gates for registration integrity.
- Keep the taskset planned until a future claim starts `TASK-AR-297`.
- Do not mark this taskset complete until `TASK-AR-305` verification passes.

