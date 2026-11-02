---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-661
display_id: TASK-AR-661
task_uid: a9ead343-b9f5-478a-a8a6-fea6096c346a
work_id: TASK-AR-661
work_uid: a9ead343-b9f5-478a-a8a6-fea6096c346a
kind: task
parent_id: TASKSET-OWNER-REPORT-CLARITY-20261102
registered_at: 2026-11-02T10:29:43+09:00
started_at: 2026-11-02T10:34:38+09:00
created_at: 2026-11-02T10:29:43+09:00
updated_at: 2026-11-02T11:33:12+09:00
title: Compact report contract and generator
status: completed
priority: P1
difficulty: M
est_hours: 1
est_tokens: 1000
owner: lead_engineer
initiative_id: INIT-OWNER-REPORT-CLARITY-20261102
project_id: agent_runtime
task_set_id: TASKSET-OWNER-REPORT-CLARITY-20261102
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-661/UNIT-TASK-AR-661-001.md
reservation_id: RES-20261102-102943-b03919b6-01
origin_type: owner_request
origin_ref: owner-request:2026-11-02:compact-report-readability
created_by: codex-owner-report-planner
summary: Owners need concise reports with a one-line outcome, at most three state highlights, explicit visible limitations/approval boundaries and next actions. Keep audit evidence in a secondary section; do not delete it or manufacture certainty. Add a deterministic compact Markdown generator and format validation; keep legacy reports valid. No network/delivery/hooks activation. Public generic examples only.
planner_model_tier: planner_high
worker_model_tier: worker_low
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - Legacy format tests still pass.
  - Dense first-layer content, missing limitations or unknown report profile fails.
  - Compact Markdown preserves unknown/not-run and concrete limits in the visible first layer.
  - Renderer escapes untrusted Markdown controls/links and does not fetch or send data.
verification:
  - PYTHONPATH=src python3 -m pytest tests/test_owner_doc_format_gate.py tests/test_owner_brief.py -q
  - PYTHONPATH=src python3 scripts/owner_doc_format_gate.py --manifest owner-docs.yml
claim_refs:
  - agents/runtime/task_claims/CLAIM-20261102-103438-task-ar-661-f587.json
verification_status: passed
verified_at: 2026-11-02T11:33:07+09:00
verified_by: codex-owner-report-planner
evidence_refs:
  - reviews/VERIFY-2026-11-02-task-ar-661-20261102113307.json
escalation_triggers:
defect_signatures:
compound_refs:
review_refs:
  - reviews/REVIEW-2026-11-02-owner-report-clarity.json
resolution: done
completed_at: 2026-11-02T11:33:12+09:00
closed_by: codex-owner-report-planner
measurement_unavailable_reason: Host per-task hours and token usage unavailable; preserve unknown rather than zero. No new model/provider call activated.
---

# TASK-AR-661 - Compact report contract and generator

## Goal

- Owners need concise reports with a one-line outcome, at most three state highlights, explicit visible limitations/approval boundaries and next actions. Keep audit evidence in a secondary section; do not delete it or manufacture certainty. Add a deterministic compact Markdown generator and format validation; keep legacy reports valid. No network/delivery/hooks activation. Public generic examples only.

## Scope

- Owners need concise reports with a one-line outcome, at most three state highlights, explicit visible limitations/approval boundaries and next actions. Keep audit evidence in a secondary section; do not delete it or manufacture certainty. Add a deterministic compact Markdown generator and format validation; keep legacy reports valid. No network/delivery/hooks activation. Public generic examples only.

## Acceptance Criteria

- Legacy format tests still pass.
- Dense first-layer content, missing limitations or unknown report profile fails.
- Compact Markdown preserves unknown/not-run and concrete limits in the visible first layer.
- Renderer escapes untrusted Markdown controls/links and does not fetch or send data.

## Verification

- `PYTHONPATH=src python3 -m pytest tests/test_owner_doc_format_gate.py tests/test_owner_brief.py -q`
- `PYTHONPATH=src python3 scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

<!-- work-close:start -->
## Closeout

- Completed at: `2026-11-02T11:33:12+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Host per-task hours and token usage unavailable; preserve unknown rather than zero. No new model/provider call activated.
- Closed by: `codex-owner-report-planner`
- Verification evidence:
  - `reviews/VERIFY-2026-11-02-task-ar-661-20261102113307.json`
- Reviews:
  - `reviews/REVIEW-2026-11-02-owner-report-clarity.json`
<!-- work-close:end -->
