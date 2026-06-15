---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-371
work_uid: b1f3ba90-9bea-4fab-b72c-a7c3388c8dd3
kind: task
parent_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
origin_type: planning_proposal
origin_ref: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
created_by: planner
id: TASK-AR-371
display_id: TASK-AR-371
task_uid: b1f3ba90-9bea-4fab-b72c-a7c3388c8dd3
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
updated_at: 2026-06-15T12:01:39+09:00
title: BACKLOG.md shared-write deconfliction
status: completed
resolution: done
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: doc_steward
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers:
  - cross_cutting
  - documentation
tags:
  - backlog
  - conflict
  - docs
started_at: 2026-06-15T12:01:39+09:00
completed_at: 2026-06-15T12:01:39+09:00
verification_status: passed
review_refs:
  - reviews/W4B-2026-06-15-TASK-AR-371-374.md
  - reviews/REVIEW-2026-06-15-work-hierarchy-conflict-closure-closeout.md
---

# TASK-AR-371 - BACKLOG.md shared-write deconfliction

## Goal

- Remove `BACKLOG.md` as a top-of-file shared manual registration hotspot while preserving historical narrative context.

## Scope

- Decide the replacement shape: generated registration changelog, append-only per-taskset registration record, or compact index sourced from task/taskset metadata.
- Keep `BACKLOG-BOARD.md` generated from task frontmatter.
- Preserve old `BACKLOG.md` entries as history or generated archive sections.
- Update docs so planners do not manually prepend registration sections to `BACKLOG.md`.
- Add a stale/manual-edit gate if needed.

## Out Of Scope

- Deleting historical backlog entries without an archive.
- Changing task status semantics.
- Moving detailed task instructions into the backlog.

## Acceptance Criteria

- Normal taskset registration no longer requires all planners to edit the same top section of `BACKLOG.md`.
- Historical backlog context remains discoverable.
- Regenerating the board does not require conflict-prone manual merge work.

## Verification

- `python scripts/backlog_board.py --write`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`
- Focused tests or gate checks for the new registration index/changelog path.

## Handoff

- Report which file is now generated, which file is append-only, and which file future planners should edit.

