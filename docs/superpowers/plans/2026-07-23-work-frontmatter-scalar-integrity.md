---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
work_uid: be07c34b-ea41-496d-9ca6-2af5931485de
kind: taskset
id: TASKSET-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
parent_id: INIT-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
initiative_id: INIT-AR-WORK-FRONTMATTER-SCALAR-INTEGRITY
status: active
owner: lead-engineer
created_at: 2026-07-23T15:01:03+09:00
updated_at: 2026-07-23T15:01:03+09:00
origin_type: verification_audit_finding
origin_ref: reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md
created_by: codex-root-planner
summary: Define and enforce lossless work-item frontmatter scalar serialization.
---

# Work Frontmatter Scalar Integrity

## Goal

- Define and enforce lossless work-item frontmatter scalar serialization.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-622` | Preserve literal work frontmatter scalars across rewrites |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-622-001` | `TASK-AR-622` | Define and test lossless work scalar serialization |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
