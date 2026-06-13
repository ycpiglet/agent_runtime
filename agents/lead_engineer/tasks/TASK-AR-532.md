---
id: TASK-AR-532
display_id: TASK-AR-532
task_uid: cb6168bf-1b68-40ce-82a4-4531a8433509
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
updated_at: 2026-06-14T02:08:50+09:00
status: planned
priority: P2
difficulty: M
est_hours: 5
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - bug
  - triage
  - candidate
---

# TASK-AR-532 - Open BUG triage routing + fixes

## Goal

- Route the standing open bug issues through the same intake/triage pipeline (category = 결함) and resolve them, proving the pipeline consumes defect-class feedback, not only design/process feedback. (GH #19, #20, #21)

## Scope

- **#21 [High] BUG-002** — `sync --diff` fails on Windows cp949 console with `UnicodeEncodeError`. Make console output encoding-safe on legacy code pages.
- **#20 [Medium] BUG-001** — `build_sync_plan` accepts a stale config argument and fails with `AttributeError`. Validate/refresh the config contract.
- **#19 [Low] BUG-004** — project template role docs link to files that are not shipped. Fix links or ship the targets (overlaps TASK-AR-531 wheel/dotfile packaging — coordinate).

## Acceptance Criteria — candidate

- Triage classification + fix order is decided by the TASK-AR-527 deliberation (severity = priority signal); this file pre-registers the three bugs so they are tracked in the taskset.

## Acceptance Criteria

- Each bug has a reproduction, a fix, and a regression test where feasible.
- #19 fix is coordinated with TASK-AR-531 so the dotfile/doc-shipping fix is not duplicated.

## Evidence Targets

- Fixes + tests in `scripts/` / `src/agent_runtime/`.
- Reply-back on each bug issue per TASK-AR-528.
- Source: GH ycpiglet/agent_runtime#21, #20, #19.
