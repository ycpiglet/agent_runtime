---
type: release
id: RELEASE-2026-06-09-v0.1.8
audience: owner
status: G
priority: High
tags: [release, automation, autonomy-policy, executive-brief]
actions: [released-local, external-publish-pending]
owner: lead-engineer
evidence:
  - reviews/AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8.json
  - reviews/RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8.json
  - reviews/RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8.json
---

Bottom Line: v0.1.8 local release evidence is complete; external GitHub publish remains a separate remote execution step.

## Signal

| Item | State | Evidence |
|------|-------|----------|
| Automation policy | G | `AUTONOMY-POLICY-GATE`, findings 0 |
| Release council | G | `RELEASE-COUNCIL-GATE`, findings 0 |
| Local tag smoke | G | `publish-tag-smoke --apply`, smoke passed |
| Package version | G | `agent_runtime-0.1.8` installed |
| External publish | Y | not executed in this cycle |

## Action

| # | Action | Owner | Trigger |
|---|--------|-------|---------|
| 1 | Use v0.1.8 local release evidence | lead-engineer | immediate |
| 2 | Run external GitHub publish | ci-cd | remote execution decision |

## Insight

1. Routine branch/commit/PR/merge and noncritical releases no longer need repeated Owner approval when gates pass.
2. Critical boundaries remain explicit: secrets, production data, destructive operations, legal/billing, failed gates, major/breaking releases.
3. Executive BRIEF v2 makes reports shorter for humans and easier for agents to filter by metadata.

## Decision

1. Local v0.1.8 release: complete.
2. External publish: not executed; run only when remote push is intended.

## Footer

- Tags: release, automation, autonomy-policy, executive-brief
- Evidence: local tag smoke, release council gate, autonomy policy gate
- Open risk: external GitHub tag is not pushed in this cycle.
