---
id: TASK-AR-288
display_id: TASK-AR-288
task_uid: 3de2947c-1b61-4c41-882c-ef7f1a99edd1
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: 2026-06-11T11:53:49+09:00
updated_at: 2026-06-11T11:53:49+09:00
completed_at: 2026-06-11T11:53:49+09:00
title: Enforce role coverage and waiver lifecycle
status: completed
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - role-coverage
  - waiver
---

# TASK-AR-288 - Enforce role coverage and waiver lifecycle

## Goal

- Track excluded, underused, waived, and lifecycle-stale agents across multi-pane collaboration.

## Scope

- Extend collaboration governance to report role coverage per audit window.
- Keep `role-usage:scribe` visible until real claim or log evidence exists.
- Track low-frequency roles such as council, progress-scout, release-steward, reviewer, and skeptic.
- Add expiry and owner fields to any waiver that allows missing role evidence.

## Acceptance Criteria

- Role coverage output includes required, observed, missing, waived, and monitored roles.
- Waivers without owner, reason, expiry, mitigation, and evidence target fail the gate.
- Low-frequency roles remain visible as watch items until policy is changed or evidence is added.
- No role is counted as used from prose mentions alone.

## Evidence Targets

- `scripts/collaboration_governance_gate.py`
- `agents/project/waivers/`
- `reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md`
- `tests/test_collaboration_governance_gate.py`
