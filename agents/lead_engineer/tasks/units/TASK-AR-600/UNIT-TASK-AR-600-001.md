---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-600-001
work_uid: dd488414-29e1-4405-8b9b-2a547734a768
kind: unit
parent_id: TASK-AR-600
unit_id: UNIT-TASK-AR-600-001
task_id: TASK-AR-600
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
initiative_id: INIT-AR-UI-UX-DESIGN-DIRECTION-CYCLE
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead-designer
created_at: 2026-06-19T08:18:00+09:00
updated_at: 2026-06-19T08:30:57+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Run lead-designer UI direction seminar
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The previous design-system work made tokens, roles, gates, and UI/UX cycle proposals usable. The next cycle must create a real design-direction decision before implementation, so new UI work does not simply repeat the existing visual language.
inputs:
  - reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
  - reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
  - docs/design/agent-runtime/DESIGN.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - scripts/ui_ux_cycle.py
target_files:
  - reviews/SEMINAR-2026-06-19-ui-ux-design-direction.md
  - reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
  - reviews/INDEX.md
scope: Write the seminar decision artifact and refresh the evidence index only. Do not edit docs/design or UI source files in this unit.
acceptance:
  - The seminar artifact is specific enough for a planner to write the RFC task without chat context.
  - Every UI quality dimension has evidence expectations and a likely assetization class.
  - The chosen direction has an explicit implementation boundary and beta-tester follow-up path.
verification:
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/evidence_index_generator.py --check
handoff: Report the selected design-direction candidate, rejected alternatives, assetization implications, and next RFC target files.
stop_condition: Stop after seminar evidence is complete and ready for RFC registration or claim.
verified_at: 2026-06-19T08:23:49+09:00
verified_by: codex-independent-verifier-ui-seminar-600
evidence_refs:
  - reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082323.json
  - reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082349.json
resolution: done
completed_at: 2026-06-19T08:30:57+09:00
closed_by: codex-lead-designer-ui-seminar-600
actual_hours: 1.0
actual_tokens: 6000
---

# UNIT-TASK-AR-600-001 - Run lead-designer UI direction seminar

## Context

The previous design-system work made tokens, roles, gates, and UI/UX cycle proposals usable. The next cycle must create a real design-direction decision before implementation, so new UI work does not simply repeat the existing visual language.

## Inputs

- reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
- reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md
- docs/design/agent-runtime/DESIGN.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- scripts/ui_ux_cycle.py

## Target Files

- reviews/SEMINAR-2026-06-19-ui-ux-design-direction.md
- reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md
- reviews/INDEX.md

## Scope

Write the seminar decision artifact and refresh the evidence index only. Do not edit docs/design or UI source files in this unit.

## Steps

1. Read the current UI/UX proposal and design-system diagnostic.
2. Record lead-designer, design-system-steward, interface-designer, and ux-evaluator positions.
3. Compare at least two design-direction options and choose one RFC candidate.
4. Map the chosen direction to token, UI component, pattern component, and one-off implications.
5. Refresh evidence index and run the recorded verification commands.

## Acceptance Criteria

- The seminar artifact is specific enough for a planner to write the RFC task without chat context.
- Every UI quality dimension has evidence expectations and a likely assetization class.
- The chosen direction has an explicit implementation boundary and beta-tester follow-up path.

## Verification

- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report the selected design-direction candidate, rejected alternatives, assetization implications, and next RFC target files.

## Stop Boundary

Stop after seminar evidence is complete and ready for RFC registration or claim.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-06-19T08:30:57+09:00`
- Resolution: `done`
- Actual hours: `1.0`
- Actual tokens: `6000`
- Closed by: `codex-lead-designer-ui-seminar-600`
- Evidence:
  - `reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082323.json`
  - `reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082349.json`
<!-- work-close:end -->
