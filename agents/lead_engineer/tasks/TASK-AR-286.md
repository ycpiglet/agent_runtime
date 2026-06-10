---
id: TASK-AR-286
display_id: TASK-AR-286
task_uid: e1b6076f-bb18-4a75-a019-6ec0cc1fbfef
registered_at: 2026-06-11T01:45:00+09:00
created_at: 2026-06-11T01:45:00+09:00
started_at: ""
updated_at: 2026-06-11T01:45:00+09:00
completed_at: ""
title: Audit multi-pane process compliance
status: planned
priority: P0
difficulty: M
est_hours: 3
est_tokens: 1200
owner: lead_engineer
task_set_id: TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE
tags:
  - multi-pane
  - process
  - audit
  - governance
---

# TASK-AR-286 - Audit multi-pane process compliance

## Goal

- Verify whether plan, review, compound, retro, meeting, seminar, Ralph, scribe, and doc-steward process steps actually occurred for multi-pane work.

## Scope

- Define process evidence requirements per task set and per pane role.
- Distinguish required, optional, waived, and out-of-scope process steps.
- Count evidence artifacts for `PLAN`, `REVIEW`, `COMPOUND`, `RETRO`, `MEETING`, `SEMINAR`, Ralph, scribe, and doc-steward.
- Report low-frequency or excluded agents without fabricating participation.

## Acceptance Criteria

- Audit output shows pass, watch, waived, and block counts for each process step.
- Missing scribe/Ralph/retro/doc-steward evidence is visible as watch or block according to policy.
- The audit can explain whether every active task set has a plan and review path.
- The audit does not treat a generated document name as proof unless it maps to a task, claim, or event.

## Evidence Targets

- `scripts/multipane_process_audit.py`
- `agents/project/MULTIPANE-PROCESS-POLICY.yml`
- `tests/test_multipane_process_audit.py`

