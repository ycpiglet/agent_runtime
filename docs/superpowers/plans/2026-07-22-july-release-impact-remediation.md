---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
work_uid: bfb99bff-41dd-4120-997f-2c36ff8fa814
kind: taskset
id: TASKSET-AR-JULY-RELEASE-IMPACT-REMEDIATION
parent_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
initiative_id: INIT-AR-JULY-RELEASE-IMPACT-REMEDIATION
status: active
owner: lead-engineer
created_at: 2026-07-22T17:45:00+09:00
updated_at: 2026-07-22T17:45:00+09:00
origin_type: downstream_bug
origin_ref: reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md
created_by: codex-root-planner
summary: Repair canonical identity, task start state, host dashboard dependencies, hook activation, CI isolation, frontmatter parsing, and classifier semantics.
---

# Release Impact Remediator

## Goal

- Repair canonical identity, task start state, host dashboard dependencies, hook activation, CI isolation, frontmatter parsing, and classifier semantics.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-603` | Unify canonical task ID producers and consumers |
| `TASK-AR-604` | Persist canonical task start status |
| `TASK-AR-605` | Make the generated session dashboard self-contained |
| `TASK-AR-606` | Activate configured pre-commit hooks on POSIX hosts |
| `TASK-AR-607` | Make transient-spawn recovery testing deterministic |
| `TASK-AR-608` | Preserve quoted hashes in frontmatter scalars |
| `TASK-AR-609` | Classify initiative records by canonical kind |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-603-001` | `TASK-AR-603` | Adopt a shared canonical task-ID contract |
| `UNIT-TASK-AR-604-001` | `TASK-AR-604` | Separate task status normalization from persistence |
| `UNIT-TASK-AR-605-001` | `TASK-AR-605` | Add a clean-template W0 fallback |
| `UNIT-TASK-AR-606-001` | `TASK-AR-606` | Make hook activation executable and idempotent |
| `UNIT-TASK-AR-607-001` | `TASK-AR-607` | Isolate transient-spawn recovery state |
| `UNIT-TASK-AR-608-001` | `TASK-AR-608` | Make frontmatter comment scanning quote-aware |
| `UNIT-TASK-AR-609-001` | `TASK-AR-609` | Filter classifier initiative collection by record kind |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
