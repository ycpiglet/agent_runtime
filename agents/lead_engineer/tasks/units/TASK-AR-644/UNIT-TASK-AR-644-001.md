---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-644-001
work_uid: c0c1060c-915c-4189-9371-7c8af2d5deef
kind: unit
parent_id: TASK-AR-644
unit_id: UNIT-TASK-AR-644-001
task_id: TASK-AR-644
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Replace platform-specific hook shims with verified Python entrypoints
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The shipped Codex hooks invoke .cmd files for update, prompt, governance, and Allimbot actions. The existing session_start_hook is not wired into those hooks, reproducing the Tag Manual dogfooding bypass.
inputs:
  - src/agent_runtime/templates/project/.codex/hooks.json
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/install_hooks.py
target_files:
  - .codex/hooks.json
  - src/agent_runtime/templates/project/.codex/hooks.json
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/install_hooks.py
  - src/agent_runtime/doctor.py
  - tests/test_bootstrap_dev_env.py
  - tests/test_session_resume_check.py
  - tests/test_doctor.py
  - tests/test_template_smoke.py
scope: Use portable Python commands and client-supported platform overrides, add compact checkpoint/rebootstrap, and verify hook presence. Do not assume unsupported hook events without capability detection.
acceptance:
  - No POSIX path depends on a .cmd file.
  - Hook commands resolve in a clean host.
  - Compaction capability degrades explicitly when unsupported.
  - Session resume finds active or recovered work.
verification:
  - python -m pytest tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_doctor.py tests/test_template_smoke.py -q
handoff: Provide the client/OS hook matrix and simulated compact/restart logs.
stop_condition: Stop before editing per-user agent settings without explicit Owner action.
---

# UNIT-TASK-AR-644-001 - Replace platform-specific hook shims with verified Python entrypoints

## Context

The shipped Codex hooks invoke .cmd files for update, prompt, governance, and Allimbot actions. The existing session_start_hook is not wired into those hooks, reproducing the Tag Manual dogfooding bypass.

## Inputs

- src/agent_runtime/templates/project/.codex/hooks.json
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/install_hooks.py

## Target Files

- .codex/hooks.json
- src/agent_runtime/templates/project/.codex/hooks.json
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/install_hooks.py
- src/agent_runtime/doctor.py
- tests/test_bootstrap_dev_env.py
- tests/test_session_resume_check.py
- tests/test_doctor.py
- tests/test_template_smoke.py

## Scope

Use portable Python commands and client-supported platform overrides, add compact checkpoint/rebootstrap, and verify hook presence. Do not assume unsupported hook events without capability detection.

## Steps

1. Define portable hook entrypoints.
2. Wire SessionStart and supported compact events.
3. Add commandWindows only where necessary.
4. Teach doctor to validate effective hooks and dependencies.

## Acceptance Criteria

- No POSIX path depends on a .cmd file.
- Hook commands resolve in a clean host.
- Compaction capability degrades explicitly when unsupported.
- Session resume finds active or recovered work.

## Verification

- `python -m pytest tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_doctor.py tests/test_template_smoke.py -q`

## Handoff

Provide the client/OS hook matrix and simulated compact/restart logs.

## Stop Boundary

Stop before editing per-user agent settings without explicit Owner action.
