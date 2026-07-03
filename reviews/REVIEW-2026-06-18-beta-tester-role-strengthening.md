---
type: review
id: REVIEW-2026-06-18-beta-tester-role-strengthening
audience: owner
status: pass
signal: pass
score: 94
priority: High
tags: [beta-tester, ui, exploratory-testing, verification, role-contract]
---

# Beta Tester Role Strengthening

## Bottom Line

- Summary: Beta Tester is now defined as an exploratory UI gate, not a smoke-test role.
- Result: user-facing UI changes require a clean/fail `ROUNDS.md` entry, and failures become `BTC-NNN` evidence for QA conversion.

## Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Role contract | pass | `src/agent_runtime/templates/project/agents/beta_tester/SKILL.md` |
| Exploration protocol | pass | `src/agent_runtime/templates/project/agents/beta_tester/references/exploration.md` |
| False-positive guard | pass | `src/agent_runtime/templates/project/agents/beta_tester/GOTCHAS.md` |
| Routing gate | pass | `src/agent_runtime/templates/project/scripts/cycle_gate.py` |

## Decision

- Decision: a Beta round is valid only when it records user-like actions, edge/recovery attempts, environment, and evidence.
- Decision: smoke checks, DOM existence checks, and single screenshots do not satisfy Beta Tester evidence for UI work.
- Decision: QA automation and Beta exploration are separate responsibilities; one does not replace the other.

## Action Board

| Action | Owner | Status | Evidence |
| --- | --- | --- | --- |
| Add explicit UI Beta gate language | lead-engineer | done | `SKILL.md` |
| Ship detailed exploration matrix | lead-engineer | done | `references/exploration.md` |
| Ship Beta gotchas | lead-engineer | done | `GOTCHAS.md` |
| Require stronger cycle-gate artifact text | lead-engineer | done | `test_cycle_gate.py` |

## Risks / Blockers

- Risk: this strengthens host-project templates and routing signals, but it does not retroactively create Beta rounds for completed UI work.
- Risk: full mechanical closeout blocking still depends on each host project's W4b/release gates consuming the Beta evidence ref.

## Next Steps

- Add host-project release/W4b enforcement that refuses UI closeout without a `ROUNDS.md` evidence ref.
- Convert repeated BTC findings into QA-owned automated regressions.
