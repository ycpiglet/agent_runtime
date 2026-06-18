---
title: Monitored Role Artifact Evidence
date: 2026-06-18
signal: pass
score: 83
tags: [self-improvement, collaboration-governance, role-monitor, task-ar-574]
---

# Monitored Role Artifact Evidence

## Bottom Line

The monitored-role gate now matches the TASK-AR-574 acceptance contract:
monitored roles can be proven by configured claim, review, council, or policy
records. Required roles in `minimum_claim_roles` remain claim-only.

## Signal

| Metric | Before | After |
| --- | ---: | ---: |
| monitored role gaps | 3 | 1 |
| self-improvement score | 73 | 83 |
| unwaived blocks | 0 | 0 |
| waiver debt | 0 | 0 |

## Action Board

| Role | State | Evidence |
| --- | --- | --- |
| council | accepted | `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md` with `type: council` |
| skeptic | accepted | same council record includes the `skeptic` viewpoint |
| progress-scout | still watch | no current claim/log or configured artifact evidence |

## Risk

This does not treat prose mentions as role execution. A monitored role only
counts when `agents/project/COLLABORATION-GOVERNANCE.json` explicitly maps the
role to a path glob and required content tokens, and a matching artifact exists.

## Decision

Keep `minimum_claim_roles` strict, and add `monitored_role_evidence` only for
roles whose existing artifacts are semantically the role surface. Do not add
`progress-scout` until a current progress-scout claim/log or stronger progress
record exists.

## Next

- Route `progress-scout` through real status/progress work before counting it.
- Burn down lifecycle watch debt separately instead of weakening role evidence.
- Continue wiki/graph work from the now cleaner role baseline.

