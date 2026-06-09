---
type: meeting
id: MEETING-2026-06-09-v018-release-council
audience: agent-team
status: G
priority: High
tags: [release-council, automation, v0.1.8]
actions: [approve-release, record-evidence]
owner: lead-engineer
evidence:
  - agents/project/release/RELEASE-DECISION-v0.1.8.yml
---

Bottom Line: Agent release council approved v0.1.8 as noncritical and eligible for automated release execution.

## Signal

| Role | Vote | Reason |
|------|------|--------|
| Lead Engineer | approve | scope is minor automation/governance policy |
| QA | approve | gates and smoke evidence are required |
| Independent Auditor | approve | critical flags are empty |
| Doc Steward | approve | report and handoff format improved |

## Decision

1. Proceed with v0.1.8 local release evidence.
2. Keep external GitHub publish as a separate remote execution step.
