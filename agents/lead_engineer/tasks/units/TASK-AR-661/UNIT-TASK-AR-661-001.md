---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-661-001
work_uid: b9644221-7353-4ad6-bfd3-47cf18d2cc3b
kind: unit
parent_id: TASK-AR-661
unit_id: UNIT-TASK-AR-661-001
task_id: TASK-AR-661
task_set_id: TASKSET-OWNER-REPORT-CLARITY-20261102
initiative_id: INIT-OWNER-REPORT-CLARITY-20261102
project_id: agent_runtime
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-11-02T10:29:43+09:00
updated_at: 2026-11-02T11:32:11+09:00
origin_type: owner_request
origin_ref: owner-request:2026-11-02:compact-report-readability
created_by: codex-owner-report-planner
summary: Compact owner report generation and validation
horizon: unit
model_tier: worker_low
escalation_triggers:
context: Owners need concise reports with a one-line outcome, at most three state highlights, explicit visible limitations/approval boundaries and next actions. Keep audit evidence in a secondary section; do not delete it or manufacture certainty. Add a deterministic compact Markdown generator and format validation; keep legacy reports valid. No network/delivery/hooks activation. Public generic examples only.
inputs:
  - AGENTS.md
  - scripts/owner_doc_format_gate.py
target_files:
  - scripts/owner_doc_format_gate.py
  - src/agent_runtime/templates/project/scripts/owner_doc_format_gate.py
  - src/agent_runtime
  - tests/test_owner_doc_format_gate.py
  - tests
  - AGENTS.md
  - src/agent_runtime/templates/project/AGENTS.md
  - src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md
  - src/agent_runtime/templates/project/agents/lead_engineer/reports/README.md
scope: Implement compact-v1 owner reporting in the existing format gate and package; update reusable host guidance; focused regressions.
acceptance:
  - Legacy format tests still pass.
  - Dense first-layer content, missing limitations or unknown report profile fails.
  - Compact Markdown preserves unknown/not-run and concrete limits in the visible first layer.
  - Renderer escapes untrusted Markdown controls/links and does not fetch or send data.
verification:
  - PYTHONPATH=src python3 -m pytest tests/test_owner_doc_format_gate.py tests/test_owner_brief.py -q
  - PYTHONPATH=src python3 scripts/owner_doc_format_gate.py --manifest owner-docs.yml
handoff: Give exact head, changed files, test exit/status and known limits; do not claim consumer rollout.
stop_condition: Stop after scoped code/tests/docs and self-verification; independent reviewer must approve.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20261102-103438-task-ar-661-f587.json
verified_at: 2026-11-02T11:31:12+09:00
verified_by: codex-owner-report-planner
evidence_refs:
  - reviews/VERIFY-2026-11-02-unit-task-ar-661-001-20261102113112.json
defect_signatures:
compound_refs:
review_refs:
  - reviews/REVIEW-2026-11-02-owner-report-clarity.json
resolution: done
completed_at: 2026-11-02T11:32:11+09:00
closed_by: codex-owner-report-planner
measurement_unavailable_reason: Host per-task hours and token usage unavailable; preserve unknown rather than zero. No new model/provider call activated.
---

# UNIT-TASK-AR-661-001 - Compact owner report generation and validation

## Context

Owners need concise reports with a one-line outcome, at most three state highlights, explicit visible limitations/approval boundaries and next actions. Keep audit evidence in a secondary section; do not delete it or manufacture certainty. Add a deterministic compact Markdown generator and format validation; keep legacy reports valid. No network/delivery/hooks activation. Public generic examples only.

## Inputs

- AGENTS.md
- scripts/owner_doc_format_gate.py

## Target Files

- scripts/owner_doc_format_gate.py
- src/agent_runtime/templates/project/scripts/owner_doc_format_gate.py
- src/agent_runtime
- tests/test_owner_doc_format_gate.py
- tests
- AGENTS.md
- src/agent_runtime/templates/project/AGENTS.md
- src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md
- src/agent_runtime/templates/project/agents/lead_engineer/reports/README.md

## Scope

Implement compact-v1 owner reporting in the existing format gate and package; update reusable host guidance; focused regressions.

## Steps

1. Add bounded structured input to compact Markdown conversion.
2. Teach root/template format gates compact profile while preserving legacy checks.
3. Make new owner reports default to the compact layout with visible critical limits and secondary evidence.
4. Run focused tests and independent review.

## Acceptance Criteria

- Legacy format tests still pass.
- Dense first-layer content, missing limitations or unknown report profile fails.
- Compact Markdown preserves unknown/not-run and concrete limits in the visible first layer.
- Renderer escapes untrusted Markdown controls/links and does not fetch or send data.

## Verification

- `PYTHONPATH=src python3 -m pytest tests/test_owner_doc_format_gate.py tests/test_owner_brief.py -q`
- `PYTHONPATH=src python3 scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

## Handoff

Give exact head, changed files, test exit/status and known limits; do not claim consumer rollout.

## Stop Boundary

Stop after scoped code/tests/docs and self-verification; independent reviewer must approve.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-11-02T11:32:11+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Host per-task hours and token usage unavailable; preserve unknown rather than zero. No new model/provider call activated.
- Closed by: `codex-owner-report-planner`
- Verification evidence:
  - `reviews/VERIFY-2026-11-02-unit-task-ar-661-001-20261102113112.json`
- Reviews:
  - `reviews/REVIEW-2026-11-02-owner-report-clarity.json`
<!-- work-close:end -->
