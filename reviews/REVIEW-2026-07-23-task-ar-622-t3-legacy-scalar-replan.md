---
id: REVIEW-2026-07-23-task-ar-622-t3-legacy-scalar-replan
title: TASK-AR-622 T3 legacy scalar replan and re-anchor
kind: planning
status: approved
date: 2026-07-23
task_id: TASK-AR-622
task_set_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
decision: replan
---

# TASK-AR-622 T3 legacy scalar replan and re-anchor

## Current objective

Make TASK-AR-622 dispatch-ready without implementing its general parser and
serializer fix inside the TASK-AR-602 release closeout.

## Drift and acceptance findings

The skeptical recheck found two planning defects:

1. The automatic T0 design digest was recorded against the registration
   review's CRLF working-tree bytes, while the committed checkout normalizes
   the same file to LF. The design anchor therefore drifted immediately even
   though the file had no semantic post-registration edit.
2. Parser-visible round-trip acceptance is insufficient for a legacy raw line
   such as `origin_ref: ... #274`: the raw parser can discard the suffix before
   the serializer sees it, and a round trip of the already truncated value can
   still pass.

## T3 decision

- Re-anchor the taskset from this T3 record and current committed script bytes.
- Add `scripts/backlog_board.py` to the implementation footprint because raw
  comment detection is a parser boundary, not solely a work lifecycle writer
  boundary.
- Require verify/close to fail before rewrite on an unsafe legacy unquoted
  hash-bearing scalar unless an explicitly reviewed migration supplies the
  intended value. The worker must not infer discarded provenance.
- Preserve historical records and evidence; no bulk migration is authorized.

## Re-anchor set

- `reviews/REVIEW-2026-07-23-task-ar-622-t3-legacy-scalar-replan.md`
- `scripts/task_claim_dispatcher.py`
- `scripts/work.py`
- `scripts/backlog_board.py`

## Verification

- `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY`
- `python scripts/work_schema_gate.py --items --check`
- `python scripts/taskset_work_gate.py --check`

