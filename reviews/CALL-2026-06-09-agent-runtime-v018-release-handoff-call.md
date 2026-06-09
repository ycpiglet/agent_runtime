---
type: call
id: CALL-2026-06-09-v018-release-handoff
audience: agent-team
status: G
priority: Medium
tags: [handoff, release, v0.1.8]
actions: [external-publish-optional]
owner: doc-steward
evidence:
  - reviews/REVIEW-2026-06-09-agent-runtime-v018-automation-policy-release.md
---

Bottom Line: v0.1.8 is locally released and ready for optional external GitHub publish.

## Handoff

| Item | State | Next |
|------|-------|------|
| Version | G | `0.1.8` |
| Local smoke | G | complete |
| External publish | Y | run `publish-github-execute` with remote if needed |
| Reports | G | Executive BRIEF v2 used |
