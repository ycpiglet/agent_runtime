---
type: host_feedback_queue
id: HOST-FEEDBACK-QUEUE-agent-runtime
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [host-feedback, intake, triage, dogfooding, generated-index]
generated_at: 2026-06-14
entry_count: 7
---

# Host Feedback Intake Queue

## Bottom Line
- Summary: `7` host (autofolio) feedback items in the intake queue (triage `7`).
- Rule: host feedback is first-class input. Items sit in `triage` until the TASK-AR-527 deliberation accepts/defers/rejects them and TASK-AR-528 replies back to the issue.

## Signal
| Item | Category | Status | Source | Tasks | Title |
|---|---|---|---|---|---|
| `HFQ-131` | process | triage | ycpiglet/agent_runtime#131 | TASK-AR-526, TASK-AR-527, TASK-AR-528 | host feedback intake -> council/seminar deliberation -> reply-back pipeline |
| `HFQ-121` | relationship | triage | ycpiglet/agent_runtime#121 | TASK-AR-531 | autofolio<->agent_runtime relationship + host-fit gaps (wheel dotfiles, read-location, work_cli, status i18n) |
| `HFQ-125` | defect | triage | ycpiglet/agent_runtime#125 | TASK-AR-529 | parallel wave: declared vs actual footprint post-verify gate missing |
| `HFQ-128` | design | triage | ycpiglet/agent_runtime#128 | TASK-AR-530 | cross-version self-eval harness + fixed/variable metrics + RSI fitness gate |
| `HFQ-021` | defect | triage | ycpiglet/agent_runtime#21 | TASK-AR-532 | BUG-002: sync --diff fails on Windows cp949 console (UnicodeEncodeError) |
| `HFQ-020` | defect | triage | ycpiglet/agent_runtime#20 | TASK-AR-532 | BUG-001: build_sync_plan accepts stale config (AttributeError) |
| `HFQ-019` | defect | triage | ycpiglet/agent_runtime#19 | TASK-AR-532 | BUG-004: project template role docs link to unshipped files |

## Decision
- Decision: route every host feedback item through this queue; never let it rot as an unconsumed issue.
- Guardrails: deliberation informs but does not override the Owner on product direction; safety/order boundary is always a human (R3); votes are a priority signal, not a direction decider.

## Next
- Run the TASK-AR-527 council/seminar deliberation on `triage` items; record verdicts and reply back (TASK-AR-528).
- Re-run `python scripts/host_feedback_intake.py --write` after queue changes.
