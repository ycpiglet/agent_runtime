---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-654
display_id: TASK-AR-654
task_uid: ef3cb8e5-d5b9-443e-ad93-5948ade62659
work_id: TASK-AR-654
work_uid: ef3cb8e5-d5b9-443e-ad93-5948ade62659
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-01T00:45:10+09:00
started_at: 2026-07-31T04:07:35+09:00
title: Require Compound for declared repeated failures
status: in_progress
priority: P1
difficulty: M
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: quality
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-654/UNIT-TASK-AR-654-001.md
reservation_id: RES-20260730-112500-842c7890-03
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
escalation_triggers:
  - repeated_failure
defect_signatures:
  - defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694
  - defect:accepted-watch-malformed-utf8-fail-open:eac1aefa14add5d1
  - defect:claim-repeated-failure-signals-lost-at-closure:1da2d2d41b194afb
  - defect:accepted-watch-unbounded-raw-file-read:ceb1edfdb452964a
review_refs:
  - reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
  - reviews/REVIEW-2026-07-31-task-ar-654-rsi-skill-contract-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
summary: Prevent a repeated defect from closing with only a generic review or retro and no reusable prevention record.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260731-040735-task-ar-654-ar654001.json
  - agents/runtime/task_claims/CLAIM-20260801-000156-task-ar-654-ar654repair001.json
acceptance:
  - Claim-time knowledge lookup remains before persistence.
  - A task with repeated_failure or defect signatures cannot close without a linked canonical Compound record.
  - The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
  - Generic substantial work may still close with an appropriate linked review or retro.
  - failure-to-regression is included in the consumer core profile and asset registry.
verification:
  - python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
---

# TASK-AR-654 - Require Compound for declared repeated failures

## Goal

- Prevent a repeated defect from closing with only a generic review or retro and no reusable prevention record.

## Scope

- Make defect signatures and repeated_failure triggers require a linked canonical Compound record and ship the failure-to-regression operating skill to consumers.

## Acceptance Criteria

- Claim-time knowledge lookup remains before persistence.
- A task with repeated_failure or defect signatures cannot close without a linked canonical Compound record.
- The Compound prevention record links to a regression, gate, task proposal, or accepted watch state.
- Generic substantial work may still close with an appropriate linked review or retro.
- failure-to-regression is included in the consumer core profile and asset registry.

## Verification

- `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Reopened fail-closed authority repair

Fresh independent review superseded the physical-line W4a for release
purposes. TASK-AR-654 remains in progress under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md` until
malformed input, claim-signal propagation, bounded reads, and both task/unit
closeout authorities pass a new W4 sequence.
