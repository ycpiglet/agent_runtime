---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-WORK-CLI-INTEGRITY
work_uid: 778399c0-2cbf-4237-8e09-b48c87ecf59a
kind: taskset
id: TASKSET-AR-WORK-CLI-INTEGRITY
parent_id: INIT-AR-WORK-CLI-INTEGRITY
initiative_id: INIT-AR-WORK-CLI-INTEGRITY
status: active
owner: lead-engineer
created_at: 2026-07-23T08:40:51+09:00
updated_at: 2026-07-23T08:40:51+09:00
origin_type: review_finding
origin_ref: reviews/REVIEW-2026-07-23-work-cli-integrity-design.md
created_by: codex-root-planner
summary: Make work-item serialization round-trip safe and exact task or unit selectors deterministic before release preflight.
---

# Work CLI Integrity

## Goal

- Make work-item serialization round-trip safe and exact task or unit selectors deterministic before release preflight.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-617` | Preserve work frontmatter values across lifecycle rewrites |
| `TASK-AR-618` | Resolve exact task and unit selectors deterministically |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-617-001` | `TASK-AR-617` | Implement round-trip-safe work frontmatter emission |
| `UNIT-TASK-AR-618-001` | `TASK-AR-618` | Implement exact work-item selector precedence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
