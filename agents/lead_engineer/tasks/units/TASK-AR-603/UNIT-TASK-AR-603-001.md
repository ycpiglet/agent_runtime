---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-603-001
work_uid: 050f21bb-5cf0-4115-a48c-257412aa8cc6
kind: unit
parent_id: TASK-AR-603
unit_id: UNIT-TASK-AR-603-001
task_id: TASK-AR-603
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
initiative_id: INIT-AR-OPERATOR-ATTENTION-GRAPH
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: interface-designer
created_at: 2026-06-19T09:08:00+09:00
updated_at: 2026-06-19T09:08:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-ui-refactor-continuous-cycle
created_by: codex-planner
summary: Add relation-aware UI assets and first workflow wiring
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: TASK-AR-601 accepted operator_attention_graph. The implementation must create a relationship-aware path from taskset attention to claim evidence, wiki/graph context, and safe command readiness while preserving the existing light-first operator console.
inputs:
  - reviews/RFC-2026-06-19-ui-ux-design-direction.md
  - docs/design/agent-runtime/DESIGN.md
  - docs/design/agent-runtime/DESIGN-SYSTEM.md
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
target_files:
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_design_assets.py
  - tests/test_ui_console.py
  - reviews/VERIFY-2026-06-19-operator-attention-graph-implementation.json
  - reviews/INDEX.md
scope: Implement relation assets and one workflow slice only. Do not add unrelated console redesign, new routing architecture, or broad visual refresh.
acceptance:
  - New relation UI states include default, active, stale, blocked, missing, and keyboard-focus paths where applicable.
  - The implementation contains visible text labels for relation state and evidence freshness.
  - Reduced-motion behavior is represented by tokens or CSS media handling where motion is introduced.
  - No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
  - The workflow remains usable when graph context is empty or evidence is stale.
verification:
  - python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q
  - python scripts/design_system_gate.py --check --all-ui
  - python scripts/ui_ux_cycle.py --root . assess --json
  - python scripts/evidence_index_generator.py --check
handoff: Report changed helpers, assetization classification, first wired workflow, focused tests, design-system gate result, and residual one-off or extraction debt.
stop_condition: Stop after one relation-aware workflow slice is implemented, tested, and ready for independent verification.
---

# UNIT-TASK-AR-603-001 - Add relation-aware UI assets and first workflow wiring

## Context

TASK-AR-601 accepted operator_attention_graph. The implementation must create a relationship-aware path from taskset attention to claim evidence, wiki/graph context, and safe command readiness while preserving the existing light-first operator console.

## Inputs

- reviews/RFC-2026-06-19-ui-ux-design-direction.md
- docs/design/agent-runtime/DESIGN.md
- docs/design/agent-runtime/DESIGN-SYSTEM.md
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py

## Target Files

- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_design_assets.py
- tests/test_ui_console.py
- reviews/VERIFY-2026-06-19-operator-attention-graph-implementation.json
- reviews/INDEX.md

## Scope

Implement relation assets and one workflow slice only. Do not add unrelated console redesign, new routing architecture, or broad visual refresh.

## Steps

1. Read the RFC assetization table and existing ui_design_assets helpers.
2. Add or reuse semantic tokens for relation traces, relation spacing, focus, and reduced-motion behavior.
3. Add reusable helpers for relation chips and evidence preview rows, using local naming conventions if different from the RFC candidate names.
4. Add a domain pattern for the attention relation panel and narrow-viewport graph context stack.
5. Wire one existing console renderer to the new pattern without moving unrelated views.
6. Add focused tests for asset output, required states, non-color-only labels, and existing console API behavior.
7. Run W4a verification commands and record evidence.

## Acceptance Criteria

- New relation UI states include default, active, stale, blocked, missing, and keyboard-focus paths where applicable.
- The implementation contains visible text labels for relation state and evidence freshness.
- Reduced-motion behavior is represented by tokens or CSS media handling where motion is introduced.
- No raw color, spacing, radius, shadow, or type literal is introduced outside token definitions.
- The workflow remains usable when graph context is empty or evidence is stale.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q`
- `python scripts/design_system_gate.py --check --all-ui`
- `python scripts/ui_ux_cycle.py --root . assess --json`
- `python scripts/evidence_index_generator.py --check`

## Handoff

Report changed helpers, assetization classification, first wired workflow, focused tests, design-system gate result, and residual one-off or extraction debt.

## Stop Boundary

Stop after one relation-aware workflow slice is implemented, tested, and ready for independent verification.
