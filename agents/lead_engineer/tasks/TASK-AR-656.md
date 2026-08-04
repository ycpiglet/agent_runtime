---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-656
display_id: TASK-AR-656
task_uid: 52d253fd-865e-47b6-8ddd-6229d7b1f3ab
work_id: TASK-AR-656
work_uid: 52d253fd-865e-47b6-8ddd-6229d7b1f3ab
kind: task
parent_id: TASKSET-AR-V080-OPERABILITY-HARDENING
registered_at: 2026-07-30T11:25:00+09:00
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
title: Make lifecycle hooks composable and deduplicated
status: planned
priority: P1
difficulty: M
est_hours: 10
est_tokens: 19000
owner: lead-engineer
team: agent-runtime-core
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-656/UNIT-TASK-AR-656-001.md
reservation_id: RES-20260730-112500-842c7890-05
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Let Runtime own its canonical lifecycle while hosts add authority hooks without permanent duplicate commands or seed_once forks.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
acceptance:
  - Runtime lifecycle commands remain managed and host extensions remain host-owned.
  - Equivalent legacy commands are removed after successful migration.
  - Host Owner-authority hooks retain declared ordering and timeout limits.
  - Repeated sync and install produce byte-identical hook state.
  - Doctor reports semantic duplicates and missing Windows parity consistently.
verification:
  - python -m pytest tests/test_doctor.py tests/test_hook_runtime.py tests/test_install_hooks.py tests/test_inventory_sync_sanitize.py -q
  - python scripts/template_mirror_gate.py --check
---

# TASK-AR-656 - Make lifecycle hooks composable and deduplicated

## Goal

- Let Runtime own its canonical lifecycle while hosts add authority hooks without permanent duplicate commands or seed_once forks.

## Scope

- Define a host hook extension registry, deterministic merge/order semantics, semantic duplicate removal, and POSIX/Windows parity checks.

## Acceptance Criteria

- Runtime lifecycle commands remain managed and host extensions remain host-owned.
- Equivalent legacy commands are removed after successful migration.
- Host Owner-authority hooks retain declared ordering and timeout limits.
- Repeated sync and install produce byte-identical hook state.
- Doctor reports semantic duplicates and missing Windows parity consistently.

## Verification

- `python -m pytest tests/test_doctor.py tests/test_hook_runtime.py tests/test_install_hooks.py tests/test_inventory_sync_sanitize.py -q`
- `python scripts/template_mirror_gate.py --check`
