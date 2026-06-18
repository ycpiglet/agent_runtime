---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
work_uid: 516503da-06ae-454d-9c2d-29f5682323bc
kind: taskset
id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
parent_id: INIT-AR-RELEASE-AUTOMATION
initiative_id: INIT-AR-RELEASE-AUTOMATION
status: active
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Fix the stale release execution gate (parameterize the hardcoded v0.1.8) and wire a cadence-bound auto-release path that runs the agent-council vote, gates, tag, and push for noncritical releases on green main CI, while keeping major/breaking/critical releases Owner-gated. Correct the release-conductor skill doc to match the implemented tier rule.
---

# Noncritical Release Auto-Execution

## Goal

- Fix the stale release execution gate (parameterize the hardcoded v0.1.8) and wire a cadence-bound auto-release path that runs the agent-council vote, gates, tag, and push for noncritical releases on green main CI, while keeping major/breaking/critical releases Owner-gated. Correct the release-conductor skill doc to match the implemented tier rule.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-585` | Parameterize the release execution gate (remove hardcoded v0.1.8) |
| `TASK-AR-586` | Wire cadence-bound noncritical auto-release and correct the release-conductor doc |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-585-001` | `TASK-AR-585` | Make execution gate target version parametric |
| `UNIT-TASK-AR-586-001` | `TASK-AR-586` | Noncritical auto-release orchestrator |
| `UNIT-TASK-AR-586-002` | `TASK-AR-586` | Schedule + Owner notification wiring |
| `UNIT-TASK-AR-586-003` | `TASK-AR-586` | Correct the release-conductor skill doc |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
