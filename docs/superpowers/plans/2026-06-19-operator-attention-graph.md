---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
work_uid: f9fa9a02-3dd5-48cb-b779-a6fc6746c3e2
kind: taskset
id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
parent_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
initiative_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
status: active
owner: lead_engineer
created_at: 2026-06-19T09:08:00+09:00
updated_at: 2026-06-19T09:08:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: First source-mutating implementation of the accepted operator_attention_graph direction: relation tokens/components/patterns, one taskset-to-evidence workflow wiring, and beta/UX evaluation evidence.
---

# Operator Attention Graph

## Goal

- First source-mutating implementation of the accepted operator_attention_graph direction: relation tokens/components/patterns, one taskset-to-evidence workflow wiring, and beta/UX evaluation evidence.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-603` | Implement operator attention graph relation assets |
| `TASK-AR-604` | Run operator attention graph beta and UX evaluation |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-603-001` | `TASK-AR-603` | Add relation-aware UI assets and first workflow wiring |
| `UNIT-TASK-AR-604-001` | `TASK-AR-604` | Record beta-tester and UX-evaluator evidence |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
