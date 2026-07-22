---
title: TASK-AR-608 Dispatch T3 Replan
date: 2026-07-23
signal: pass
score: 96
task_id: TASK-AR-608
task_set_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
tags: [replan, plan-assumptions, task-ar-608, github-298, frontmatter]
---

# TASK-AR-608 Dispatch T3 Replan

## Bottom Line

T2 correctly refused TASK-AR-608 dispatch because three release-cadence and
release-auto anchors changed after TASK-AR-607. Those changes are the verified
results of TASK-AR-613 through TASK-AR-616 and do not overlap TASK-AR-608's
frontmatter parser targets. The next registered unit remains worker-ready with
its original scope and stop boundary unchanged.

## Drift Assessment

| Drifted anchor | Cause | TASK-AR-608 impact |
| --- | --- | --- |
| `scripts/release_cadence_trigger.py` | TASK-AR-613 query recovery | none; outside parser scope |
| `tests/test_release_cadence_trigger.py` | TASK-AR-613 regression coverage | none; outside parser scope |
| `tests/test_release_auto_noncritical.py` | TASK-AR-615/616 fixture recovery | none; outside parser scope |

No active claim or divergent worktree exists. GitHub #298 remains open. The
current parser still reproduces the reported defect: parsing
`summary: "PR #167 intact"` yields `"PR"`. The existing nine backlog taskset
tests pass, and the generated host lock is current, so failure-first work can
start from a stable baseline.

## Revalidated Scope

- Change only lexical frontmatter comment scanning in the root/template
  `backlog_board.py` pair.
- Preserve hashes inside single-quoted and double-quoted scalars, including
  escaped double quotes and flow-list items.
- Preserve existing unquoted comment removal.
- Make malformed or unterminated quote handling deterministic and covered.
- Regenerate only the declared generated-host lock after root/template parity.
- Do not add a YAML dependency or expand the supported subset into a general
  YAML parser.

## T3 Decision

Re-record the current design, dispatch-flow, TASK-AR-608 parser/test/lock, and
TASK-AR-609 classifier anchors. Dispatch may proceed only if the refreshed T2
check passes. TASK-AR-609 remains downstream and will receive its own T3
revalidation after TASK-AR-608 integration changes shared taskset anchors.
