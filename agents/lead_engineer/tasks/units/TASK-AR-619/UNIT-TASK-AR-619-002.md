---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-619-002
work_uid: 63166ae5-07a4-4f6a-b967-b68a10e98c10
kind: unit
parent_id: TASK-AR-619
unit_id: UNIT-TASK-AR-619-002
task_id: TASK-AR-619
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
initiative_id: INIT-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: interface-designer
created_at: 2026-06-20T01:08:00+09:00
updated_at: 2026-06-20T01:08:00+09:00
origin_type: ui_ux_rfc
origin_ref: reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
created_by: codex-interface-designer-ar-618
summary: Render evidence queue assets and split-loading UI states
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: After the read-only schema exists, the Taskset Board needs reusable components and patterns for group filters, cap disclosure, queue rows, latency badges, selected detail, retry/defer controls, and inactive containment.
inputs:
  - reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
  - reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-implementation.json
  - reviews/INDEX.md
scope: Render only the accepted evidence review queue inside Taskset Board. Keep page/server assembly focused on layout and data wiring. Do not redesign unrelated views or introduce decorative effects.
acceptance:
  - The Taskset Board first viewport can show evidence group counts and hidden counts before full detail is inspected.
  - Every dynamic field in queue rendering is escaped.
  - Retry/defer controls are labelled, keyboard reachable, and proposal-only unless a later claimed task registers command behavior.
  - Reduced-motion mode keeps all meaning in text labels and focus state.
  - No card or button text overflows its fixed-format control at desktop or 390x844 according to tests and beta plan requirements.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
  - git diff --check
handoff: Report rendered components, CSS anchors, accessibility states, token/component/pattern/one-off classification, tests, and beta risks.
stop_condition: Stop after source mutation is tested, self-verified, and ready for independent W4b verification.
---

# UNIT-TASK-AR-619-002 - Render evidence queue assets and split-loading UI states

## Context

After the read-only schema exists, the Taskset Board needs reusable components and patterns for group filters, cap disclosure, queue rows, latency badges, selected detail, retry/defer controls, and inactive containment.

## Inputs

- reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py
- reviews/VERIFY-2026-06-20-taskset-board-evidence-review-queue-implementation.json
- reviews/INDEX.md

## Scope

Render only the accepted evidence review queue inside Taskset Board. Keep page/server assembly focused on layout and data wiring. Do not redesign unrelated views or introduce decorative effects.

## Steps

1. Add reusable JS helpers in `ui_design_assets.py` for filter, cap, badge, row, and pattern rendering with `escapeHtml` on every dynamic field.
2. Add CSS classes for stable desktop/mobile dimensions, focus, hover, selected, loading, retryable, and reduced-motion-safe states.
3. Wire `ui_console_assets.py` to render the evidence review queue from `attention_workspace.evidence_review_queue` without duplicating row markup.
4. Add tests for helper names, CSS anchors, escaping, focusable controls, reduced-motion labels, mobile stacking, and active/inactive containment.
5. Record W4a verification evidence.

## Acceptance Criteria

- The Taskset Board first viewport can show evidence group counts and hidden counts before full detail is inspected.
- Every dynamic field in queue rendering is escaped.
- Retry/defer controls are labelled, keyboard reachable, and proposal-only unless a later claimed task registers command behavior.
- Reduced-motion mode keeps all meaning in text labels and focus state.
- No card or button text overflows its fixed-format control at desktop or 390x844 according to tests and beta plan requirements.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`
- `git diff --check`

## Handoff

Report rendered components, CSS anchors, accessibility states, token/component/pattern/one-off classification, tests, and beta risks.

## Stop Boundary

Stop after source mutation is tested, self-verified, and ready for independent W4b verification.
