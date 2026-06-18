---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-597-001
work_uid: c11ebe79-c6ad-4d08-bde8-25912bd251a6
kind: unit
parent_id: TASK-AR-597
unit_id: UNIT-TASK-AR-597-001
task_id: TASK-AR-597
task_set_id: TASKSET-AR-UI-UX-CYCLE-AUTOMATION
initiative_id: INIT-AR-UI-UX-CONTINUOUS-IMPROVEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-06-19T00:00:00+09:00
updated_at: 2026-06-19T00:00:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Add UI/UX cycle conductor
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The Owner wants UI refactoring to continue, then repeatedly use seminar, meeting, beta tester, and related agent functions to derive the next step, implement, verify, and evaluate. Direct UI asset edits are temporarily blocked by an active overlapping TASK-AR-593 claim, so this unit builds the non-overlapping cycle conductor first.
inputs:
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/design_system_gate.py
  - scripts/meeting_room.py
  - scripts/self_improvement_cycle.py
  - BACKLOG-BOARD.md
  - agents/project/ORG-MODEL.yml
target_files:
  - scripts/ui_ux_cycle.py
  - tests/test_ui_ux_cycle.py
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - agents/lead_engineer/tasks/TASK-AR-583.md
  - agents/lead_engineer/tasks/TASK-AR-584.md
scope: Create read-only assessment/report plumbing and documentation. Do not perform the semantic-token or JS-renderer refactors in this unit.
acceptance:
  - The cycle names TASK-AR-583 as the next UI refactor when no conflicting active claim owns its target files, and marks it blocked/deferred when a conflict exists.
  - The cycle checklist includes typography, size, color, motion, effects, schema, assets, accessibility, responsiveness, and interaction evidence.
  - Report dry-run returns planned artifact paths without writing them.
  - The command output is stable enough for future automation to consume.
verification:
  - python -m pytest tests/test_ui_ux_cycle.py -q
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/ui_ux_cycle.py --root . report --dry-run --json
handoff: Report cycle status, next UI refactor recommendation, review/beta-tester requirements, and commands used.
stop_condition: Stop after the UI/UX cycle conductor, tests, docs, and verification evidence are complete and ready for independent review.
---

# UNIT-TASK-AR-597-001 - Add UI/UX cycle conductor

## Context

The Owner wants UI refactoring to continue, then repeatedly use seminar, meeting, beta tester, and related agent functions to derive the next step, implement, verify, and evaluate. Direct UI asset edits are temporarily blocked by an active overlapping TASK-AR-593 claim, so this unit builds the non-overlapping cycle conductor first.

## Inputs

- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/design_system_gate.py
- scripts/meeting_room.py
- scripts/self_improvement_cycle.py
- BACKLOG-BOARD.md
- agents/project/ORG-MODEL.yml

## Target Files

- scripts/ui_ux_cycle.py
- tests/test_ui_ux_cycle.py
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- agents/lead_engineer/tasks/TASK-AR-583.md
- agents/lead_engineer/tasks/TASK-AR-584.md

## Scope

Create read-only assessment/report plumbing and documentation. Do not perform the semantic-token or JS-renderer refactors in this unit.

## Steps

1. Implement a deterministic UI/UX cycle assessment that composes current design-system gate status, UI backlog candidates, recent review artifacts, and beta-tester evidence requirements.
2. Expose CLI subcommands for JSON assess output and dry-run report planning.
3. Document how the cycle selects the next UI refactor, meeting/seminar/beta-tester review, and verification handoff.
4. Add focused tests with fixture repos covering candidate selection, checklist dimensions, dry-run reporting, and no assess-mode writes.
5. Run verification commands and record handoff evidence.

## Acceptance Criteria

- The cycle names TASK-AR-583 as the next UI refactor when no conflicting active claim owns its target files, and marks it blocked/deferred when a conflict exists.
- The cycle checklist includes typography, size, color, motion, effects, schema, assets, accessibility, responsiveness, and interaction evidence.
- Report dry-run returns planned artifact paths without writing them.
- The command output is stable enough for future automation to consume.

## Verification

- `python -m pytest tests/test_ui_ux_cycle.py -q`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/ui_ux_cycle.py --root . report --dry-run --json`

## Handoff

Report cycle status, next UI refactor recommendation, review/beta-tester requirements, and commands used.

## Stop Boundary

Stop after the UI/UX cycle conductor, tests, docs, and verification evidence are complete and ready for independent review.
