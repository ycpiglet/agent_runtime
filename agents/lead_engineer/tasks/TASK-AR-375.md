---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-375
display_id: TASK-AR-375
task_uid: fe4cf218-9eb5-4597-b8a9-1df6826e3e04
work_id: TASK-AR-375
work_uid: fe4cf218-9eb5-4597-b8a9-1df6826e3e04
kind: task
parent_id: TASKSET-AR-AGENT-IDENTITY-CONTRACT
registered_at: 2026-06-12T14:50:00+09:00
created_at: 2026-06-12T14:50:00+09:00
started_at: 2026-06-12T15:05:12+09:00
updated_at: 2026-06-12T15:25:40+09:00
title: Agent instance spawn records and attribution gate
status: completed
priority: P1
difficulty: M
est_hours: 1
est_tokens: 1000
owner: lead_engineer
initiative_id: INIT-AR-AGENT-IDENTITY-OBSERVABILITY
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-AGENT-IDENTITY-CONTRACT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-375/UNIT-TASK-AR-375-001.md
verification:
  - python -m py_compile scripts/agent_instance_registry.py scripts/agent_identity_gate.py scripts/task_claim_dispatcher.py scripts/pane_event_log.py
  - python -m py_compile src/agent_runtime/templates/project/scripts/agent_instance_registry.py src/agent_runtime/templates/project/scripts/agent_identity_gate.py src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py src/agent_runtime/templates/project/scripts/pane_event_log.py src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - pytest tests/test_agent_identity_gate.py tests/test_task_claim_dispatcher.py tests/test_rbac_write_gate.py tests/test_backlog_board_tasksets.py -q
  - python scripts/agent_identity_gate.py --check
  - python scripts/owner_governance_gate.py
reservation_id: RES-20260612-145000-73c415fc-01
origin_type: owner_request
origin_ref: reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md
created_by: codex
summary: Create durable instance-level identity records and a deterministic gate that rejects claim attribution without matching instance evidence.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification_status: passed
verified_at: 2026-06-12T15:18:30+09:00
verified_by: codex
evidence_refs:
  - reviews/VERIFY-2026-06-12-task-ar-375-20260612150820.json
  - reviews/VERIFY-2026-06-12-task-ar-375-20260612151830.json
resolution: done
completed_at: 2026-06-12T15:25:40+09:00
closed_by: codex
actual_hours: 1.1
actual_tokens: 0
---

# TASK-AR-375 - Agent instance spawn records and attribution gate

## Goal

- Create durable instance-level identity records and a deterministic gate that rejects claim attribution without matching instance evidence.

## Scope

- Create durable instance-level identity records and a deterministic gate that rejects claim attribution without matching instance evidence.

## Acceptance Criteria

- Task claim creation writes a runtime instance record keyed by agent_instance_id.
- Claim-created pane events preserve instance-level actor attribution with role/callsign context.
- The instance record separates role, team, instance id, callsign/display name, callsite, pane, worktree, model tier, and spawn provenance.
- An agent identity gate verifies every active claim has a matching instance record and reports role-only or missing instance attribution.
- The owner governance gate and reusable project template include the same identity gate and claim-created attribution behavior.
- Tests cover instance record creation, idempotent repeat handling, and gate failure for missing/mismatched records.

## Verification

- `python -m py_compile scripts/agent_instance_registry.py scripts/agent_identity_gate.py scripts/task_claim_dispatcher.py scripts/pane_event_log.py`
- `python -m py_compile src/agent_runtime/templates/project/scripts/agent_instance_registry.py src/agent_runtime/templates/project/scripts/agent_identity_gate.py src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py src/agent_runtime/templates/project/scripts/pane_event_log.py src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- `pytest tests/test_agent_identity_gate.py tests/test_task_claim_dispatcher.py tests/test_rbac_write_gate.py tests/test_backlog_board_tasksets.py -q`
- `python scripts/agent_identity_gate.py --check`
- `python scripts/owner_governance_gate.py`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-12T15:25:40+09:00`
- Resolution: `done`
- Actual hours: `1.1`
- Actual tokens: `0`
- Closed by: `codex`
- Evidence:
  - `reviews/VERIFY-2026-06-12-task-ar-375-20260612150820.json`
  - `reviews/VERIFY-2026-06-12-task-ar-375-20260612151830.json`
<!-- work-close:end -->