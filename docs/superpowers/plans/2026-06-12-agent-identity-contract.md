---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-AGENT-IDENTITY-CONTRACT
work_uid: db1ca2b6-8778-4f4d-b23b-73a08d9c559a
kind: taskset
id: TASKSET-AR-AGENT-IDENTITY-CONTRACT
parent_id: INIT-AR-AGENT-IDENTITY-OBSERVABILITY
initiative_id: INIT-AR-AGENT-IDENTITY-OBSERVABILITY
status: completed
owner: lead_engineer
created_at: 2026-06-12T14:50:00+09:00
updated_at: 2026-06-12T15:34:30+09:00
verification:
  - python scripts/task_identity.py check --check
  - python scripts/work_item_classifier.py --check
  - python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-AGENT-IDENTITY-CONTRACT --check
  - python scripts/owner_governance_gate.py
origin_type: owner_request
origin_ref: reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
created_by: codex
summary: Add role/instance/display identity records, spawn provenance, and attribution gates for multi-agent work.
verification_status: passed
verified_at: 2026-06-12T15:30:00+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151220.json
  - reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612153000.json
resolution: done
completed_at: 2026-06-12T15:34:30+09:00
closed_by: codex
actual_hours: 1.3
actual_tokens: 0
---

# Agent Identity Contract

## Goal

- Add role/instance/display identity records, spawn provenance, and attribution gates for multi-agent work.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-375` | Agent instance spawn records and attribution gate |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-375-001` | `TASK-AR-375` | Agent Instance Registry And Gate Foundation |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-AGENT-IDENTITY-CONTRACT --check`
- `python scripts/owner_governance_gate.py`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T15:34:30+09:00`
- Resolution: `done`
- Actual hours: `1.3`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151220.json`
  - `reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612153000.json`
<!-- work-close:end -->