---
id: TASK-AR-263
title: Governance operations report and deprecation decision loop
status: completed
priority: P1
importance: High
difficulty: M
est_hours: 5
est_tokens: 1800
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: governance-loop
owner: independent-auditor
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [governance-report, deprecation, lifecycle, owner-brief]
audit_log: [reviews, scripts/runtime_asset_usage.py]
---

## Goal

Publish a recurring governance operations report that turns watch/waived/unused/low-reuse signals into owner-readable decisions.

## Completion Criteria

- `governance_ops_report.py` aggregates collaboration governance, runtime asset usage, taskset work, state sync, and Owner doc gates.
- Report output follows the Owner BRIEF frame.
- Low-use assets include a decision: keep, modify, deprecate, or remove.
- Waiver expiry and burn-down actions are visible in the report.

## Execution Notes

- The report should summarize evidence; gates remain the enforcement mechanism.
- The report must not hide watch findings behind a pass summary.

## Result

- Added `scripts/governance_ops_report.py` and template copy.
- Added `tests/test_governance_ops_report.py`.
- Generated `reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md`.
- Report status is `watch` because scribe role evidence and monitored low-frequency roles remain visible.
