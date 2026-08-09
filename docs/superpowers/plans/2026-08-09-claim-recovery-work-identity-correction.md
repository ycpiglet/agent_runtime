---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
work_uid: d3e628c1-648f-4b65-8e88-4cdda4c1289b
kind: taskset
id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
parent_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
initiative_id: INIT-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
status: active
owner: lead-engineer
created_at: 2026-08-09T12:00:00+09:00
updated_at: 2026-08-09T12:00:00+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-08-09-claim-recovery-work-identity-correction-plan.md
created_by: codex-root-owner-approved-correction
summary: Make recovery durable and collision-safe, restore exact ledger and taskset authority, and re-key the lost V080 Scribe and Compound work without rewriting history.
---

# Claim Recovery and Work Identity Correction

## Goal

- Make recovery durable and collision-safe, restore exact ledger and taskset authority, and re-key the lost V080 Scribe and Compound work without rewriting history.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-660` | Complete durable owner-bound claim recovery transactions |
| `TASK-AR-661` | Restore collision-safe work ledger and taskset authority |
| `TASK-AR-662` | Re-key and re-attest the lost V080 Scribe work |
| `TASK-AR-663` | Re-key and finish the lost V080 Compound work |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-660-001` | `TASK-AR-660` | Bind claim work identity and add receipt-first recovery WAL |
| `UNIT-TASK-AR-660-002` | `TASK-AR-660` | Implement owner-attributed in-place expired-claim rotation |
| `UNIT-TASK-AR-661-001` | `TASK-AR-661` | Repair work identity authority and prevent first-parent ledger loss |
| `UNIT-TASK-AR-662-001` | `TASK-AR-662` | Re-attest integrated Scribe behavior under collision-free authority |
| `UNIT-TASK-AR-663-001` | `TASK-AR-663` | Re-attest and finish repeated-failure Compound enforcement |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
