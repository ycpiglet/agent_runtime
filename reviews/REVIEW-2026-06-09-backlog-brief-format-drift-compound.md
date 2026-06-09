---
type: review
id: REVIEW-2026-06-09-backlog-brief-format-drift-compound
audience: owner
status: Y
priority: High
tags: [reporting, backlog, brief-format, recurrence, compound]
actions: [enforce-format, add-gate, update-backlog]
owner: lead_engineer
due: 2026-06-10
evidence:
  - agents/lead_engineer/compound_log.md
  - src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md
  - IMPLEMENTATION_PLAN.md
---

# REVIEW: Backlog BRIEF Format Drift Recurrence

## Bottom Line
- The backlog output format drifted again despite prior enforcement decisions.
- The issue was not missing documentation; it was missing execution-time enforcement for chat/backlog rendering.
- Treat this as a recurring process defect and add an executable/reporting gate, not another prose-only reminder.

## Signal
| Item | State | Evidence |
|---|---|---|
| Canonical format exists | G | `REPORTING-FORMAT.md` defines Executive BRIEF v2 and fixed section order. |
| Review artifact rule exists | G | `IMPLEMENTATION_PLAN.md` requires `Bottom Line`, `Signal`, `Insight`, `Decision`. |
| Chat output drifted | R | Backlog response omitted the decision-board structure and used plain P0/P1 grouping. |
| Recurrence acknowledged | R | User explicitly noted this is not the first occurrence. |

## Insight
- The failure happened because "rules in docs" were treated as sufficient, while the actual response path had no pre-answer format assertion.
- The assistant optimized for shortness and lost decision usefulness.
- The user's intent is stable: backlog/report output must help choose what to do next, not merely list tasks.
- The correct fix is to bind `백로그`/report/status/plan responses to a canonical response contract.

## Decision
1. Keep the existing format; do not replace it with a new style.
2. Add concise bullets, metadata, tags, and action tables only as enhancements on top of the existing BRIEF structure.
3. Make backlog output default to `Bottom Line -> Signal -> Insight -> Decision -> Priority/Action Board -> Next`.
4. Track a follow-up gate that rejects plan/report/backlog artifacts missing required decision sections.

## 5W1H
| Field | Record |
|---|---|
| Who | Assistant/Codex response path; user/Owner affected. |
| What | Backlog was output in a simplified list instead of the required decision-oriented BRIEF. |
| When | 2026-06-09 after v0.1.8 and README/reporting work. |
| Where | Chat response in `agent_runtime`; relevant records in `STATUS.md`, `BACKLOG.md`, `REPORTING-FORMAT.md`. |
| Why | Conversational response path lacked an enforcement gate; "concise" overrode "decision-oriented". |
| How | The assistant answered directly from a summarized mental model instead of applying the canonical backlog/report template. |

## Action
| # | Action | Owner | Trigger |
|---|---|---|---|
| 1 | Add backlog rendering contract to follow-up backlog. | lead_engineer | Immediate. |
| 2 | Implement report/backlog format gate. | lead_engineer | Next reporting-format task. |
| 3 | For future `백로그` requests, render decision board by default. | assistant | Every backlog/status/report output. |

## Footer
- Tags: reporting, backlog, recurrence, format-drift, executive-brief
- Evidence: `agents/lead_engineer/compound_log.md`
- Open risk: Until a gate exists, this remains a behavioral rule rather than a hard check.
