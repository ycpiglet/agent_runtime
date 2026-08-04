---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-V080-OPERABILITY-HARDENING
work_uid: f1f246ac-d5c1-4ade-b15c-67d7bd3b9419
kind: taskset
id: TASKSET-AR-V080-OPERABILITY-HARDENING
parent_id: INIT-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
status: active
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Turn the pilot findings into enforced, observable, reusable Runtime behavior and keep the RC blocked until the release-critical tasks pass.
---

# v0.8 Operability Hardening

## Goal

- Turn the pilot findings into enforced, observable, reusable Runtime behavior and keep the RC blocked until the release-critical tasks pass.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-652` | Bind model tiers to actual execution and economic receipts |
| `TASK-AR-653` | Close the Scribe source-debt and active-work loop |
| `TASK-AR-654` | Require Compound for declared repeated failures |
| `TASK-AR-655` | Add atomic heartbeat and renewal to task claims |
| `TASK-AR-656` | Make lifecycle hooks composable and deduplicated |
| `TASK-AR-657` | Ship consumer adoption and failure operating skills |
| `TASK-AR-658` | Expose Runtime operability health in the read-only UI |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-652-001` | `TASK-AR-652` | Implement role-aware economic routing receipts and budget enforcement |
| `UNIT-TASK-AR-653-001` | `TASK-AR-653` | Implement active-aware Scribe planning, receipt, and closure semantics |
| `UNIT-TASK-AR-654-001` | `TASK-AR-654` | Enforce repeated-failure Compound closure and ship its skill |
| `UNIT-TASK-AR-655-001` | `TASK-AR-655` | Unify task-claim renewal and expiry consumers |
| `UNIT-TASK-AR-656-001` | `TASK-AR-656` | Implement a managed Runtime hook core with host extension registry |
| `UNIT-TASK-AR-657-001` | `TASK-AR-657` | Package the reusable consumer-adoption operating procedure |
| `UNIT-TASK-AR-658-001` | `TASK-AR-658` | Build the secret-free Runtime health resource and console surface |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
