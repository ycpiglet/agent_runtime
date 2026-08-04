---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-01T00:00:05+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
tags: [task-ar-654, t3, compound, accepted-watch, line-boundary, repair]
---

# TASK-AR-654 splitlines boundary T3 replan

## Why replan

The exact implementation candidate
`debe338007d417c8b6d0448a0cbec37f3ae0240a` (tree
`08ce4e4acd14b4256a7b35ed3b5a291cfa589e2d`) passed its registered W4a and
received an independent W4b approval, but the mandatory additive skeptic
closeout subsequently found a new P1 authority bypass. Python
`str.splitlines()` removes VT, FF, FS, GS, RS, NEL, U+2028, and U+2029 before
the parser compares frontmatter delimiters. Serialized markers such as
`---<FS>` can therefore become exact `---` logical lines and grant accepted
watch authority.

The skeptic reproduced `32/32` unsafe helper approvals across the source and
packaged copies and `4/4` unsafe approvals across the actual `work close` and
work-linked Stop consumers. Its `REVISE` report supersedes the earlier
implementation approval for closeout purposes.

The previous primary claim was already recorded as released before this later
finding, but no merge or consumer write occurred. That lifecycle record remains
append-only history; it is not evidence that the now-rejected candidate is
acceptable. A distinct repair claim is required before any implementation
write.

## Drift classification

The T2 plan-assumption gate reports 18 changed or newly present anchors. They
are the expected TASK-AR-654 candidate, test, template, registry, host-lock,
and unit-state changes already reviewed in this branch. No unrelated product
scope is added. The new information is the lower-level physical-line parsing
assumption exposed by the skeptic report.

## Repair decision

1. Accept only LF and CRLF as physical line endings for authority-bearing
   Markdown. Normalize CRLF to LF only after validating the raw text. Reject a
   lone CR explicitly.
2. Reject VT, FF, FS, GS, RS, NEL, U+2028, and U+2029 before structural line
   splitting; do not allow Python's Unicode-wide `splitlines()` semantics at
   this trust boundary.
3. Add failure-first regressions for all eight separators at both opening and
   closing delimiter positions through:
   - the source and packaged accepted-watch helpers;
   - `scripts/work.py close`; and
   - the work-linked Stop closure gate.
4. Add positive LF and CRLF controls and explicit lone-CR rejection. Preserve
   valid JSON behavior and every prior duplicate, semantic-key, scalar,
   indentation, NBSP, exact-marker, and non-lossy-authority regression.
5. Keep `src/agent_runtime/knowledge_records.py` and
   `src/agent_runtime/templates/project/scripts/compound_record.py`
   byte-identical, then refresh the mirror contract and derived host lock.
6. Run the registered focus suite and full suite, produce fresh machine
   evidence and W4a, and require a new independent W4b plus skeptic closeout on
   the exact repaired candidate before claim release or local integration.

## Lifecycle and scope boundaries

- Preserve the released primary and review-overlay artifacts, the earlier
  approvals, and this later REVISE report as an auditable sequence.
- Release the review overlays after their reports exist, repair the stale
  active-work projection, and open a new claim without `--skip-plan-check`.
- The synthetic review overlay's inability to start a real process is a
  separate Runtime lifecycle-harness gap. Record it for the lifecycle/routing
  backlog; do not expand this parser repair into that cross-cutting change.
- Runtime repository only. Bean Wiki, Allimbot, Autofolio, and all consumer
  primaries remain read-only until their designated pilot phases.
- No credential access, live provider call, package installation, database,
  broker, order, notification, deploy, push, PR, tag, version bump,
  publication, or release.
