---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-602
display_id: TASK-AR-602
task_uid: efd21353-1697-4993-b007-cc3472708332
work_id: TASK-AR-602
work_uid: efd21353-1697-4993-b007-cc3472708332
kind: task
parent_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
registered_at: 2026-07-19T10:28:06+09:00
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-23T14:38:48+09:00
title: Synchronize state and release v0.7.0
status: planned
priority: P0
difficulty: L
est_hours: 5
est_tokens: 12000
owner: lead-engineer
team: release-integrity
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-602/UNIT-TASK-AR-602-001.md
reservation_id: RES-20260719-102806-bbbc9438-07
origin_type: owner_request
origin_ref: "chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277"
created_by: codex-root-planner
summary: Close the taskset through full governance, current-head release preflight, version cascade, tag, GitHub release, issue reconciliation, and W5/W6 cleanup.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
verification:
  - python scripts/release_version_cascade.py --check
  - python scripts/owner_governance_gate.py
  - python -m pytest -q
  - python scripts/work.py status
  - git cat-file -t v0.7.0
  - git rev-parse v0.7.0~0
verification_status: passed
verified_at: 2026-07-23T14:38:48+09:00
verified_by: /root/task-ar-602
evidence_refs:
  - reviews/VERIFY-2026-07-23-task-ar-602-20260723143848.json
---

# TASK-AR-602 - Synchronize state and release v0.7.0

## Goal

- Resolve GitHub #280 after every intake unit is merged by refreshing current-state records, bumping the complete version cascade, and publishing an annotated v0.7.0 release from verified main.

## Scope

- Run only after predecessor units are complete; update generated project state and the declared version cascade, then publish the Owner-approved v0.7.0 release.

## Acceptance Criteria

- Internal backlog/status and GitHub issue/PR state agree on remaining work before release.
- All focused tests, owner governance, release cascade, and release preflight pass on current main.
- v0.7.0 is committed, merged, tagged with an annotated tag, pushed, and published as a GitHub release.
- GitHub #280 and all completed intake issues are closed with evidence; no claims, worktrees, or divergent branches remain.

## Verification

- `python scripts/release_version_cascade.py --check`
- `python scripts/owner_governance_gate.py`
- `python -m pytest -q`
- `python scripts/work.py status`
- `git cat-file -t v0.7.0`
- `git rev-parse v0.7.0~0`
