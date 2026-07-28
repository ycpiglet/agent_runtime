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
status: in_progress
verification_status: passed
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T02:21:42+09:00
started_at: 2026-07-29T01:25:32+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Replace platform-specific hook shims with verified Python entrypoints
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: The focused suite passes while shipped Codex hooks still invoke Windows-only or machine-specific commands, omit commandWindows and compact lifecycle events, and never wire the generic continuity entrypoint. Current official Codex and Claude hook contracts support SessionStart, PreCompact, and PostCompact.
inputs:
  - reviews/REVIEW-2026-07-29-task-ar-644-w0-t3-replan.md
  - .codex/hooks.json
  - src/agent_runtime/templates/project/.codex/hooks.json
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/install_hooks.py
target_files:
  - agents/lead_engineer/tasks/units/TASK-AR-644/UNIT-TASK-AR-644-001.md
  - .codex/hooks.json
  - scripts/bootstrap_dev_env.py
  - scripts/verify_wheel_dotfiles.py
  - scripts/session_start_hook.py
  - scripts/session_compact_hook.py
  - scripts/session_resume_check.py
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - agents/runtime/session_checkpoints/.gitignore
  - pyproject.toml
  - src/agent_runtime/hook_runtime.py
  - src/agent_runtime/doctor.py
  - src/agent_runtime/templates/project/.codex/hooks.json
  - src/agent_runtime/templates/project/agents/runtime/session_checkpoints/.gitignore
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/session_compact_hook.py
  - src/agent_runtime/templates/project/scripts/session_resume_check.py
  - src/agent_runtime/templates/project/scripts/install_hooks.py
  - src/agent_runtime/templates/project/scripts/test_install_hooks.py
  - src/agent_runtime/templates/project/AGENTS.md
  - src/agent_runtime/templates/project/CLAUDE.md
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - tests/test_session_continuity_hooks.py
  - tests/test_bootstrap_dev_env.py
  - tests/test_session_resume_check.py
  - tests/test_interrupted_run_detector.py
  - tests/test_doctor.py
  - tests/test_template_smoke.py
  - tests/test_session_dashboard.py
  - tests/test_stop_hook_owner_governance.py
  - tests/test_update_notify.py
  - tests/fixtures/host/agent_runtime.lock.json
  - agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.json
  - agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.log.md
  - agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.handoff.md
  - reviews/W4A-2026-07-29-unit-task-ar-644-001.md
  - reviews/W4B-2026-07-29-unit-task-ar-644-001.md
  - reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142.json
  - reviews/INDEX.md
scope: Use one allowlisted Python dispatcher with POSIX and commandWindows commands, add bounded derived compact checkpoints and SessionStart reinjection, retain explicit owner-run Claude installation, and verify tracked hook health. Do not mutate consumer repositories or real per-user settings, persist prompt/transcript content, redesign compound/scribe, commit checkpoint state, or perform a release.
acceptance:
  - No POSIX path depends on a .cmd file.
  - Linux and Windows command variants resolve through the packaged dispatcher in a clean host.
  - SessionStart reports host context, active work, minimal compound lookup, resume/pointer state, and compact checkpoint state with bounded output.
  - PreCompact atomically saves derived non-conversational state and PostCompact marks rebootstrap without blocking or committing.
  - Missing, malformed, stale, incomplete, or machine-specific hooks are visible in doctor; valid Codex hooks retain an explicit trust-review reminder.
  - Claude hook installation changes only an explicit settings path and includes SessionStart, PreCompact, PostCompact, and UserPromptSubmit.
verification:
  - python -m pytest tests/test_session_continuity_hooks.py tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_interrupted_run_detector.py tests/test_doctor.py tests/test_template_smoke.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/verify_wheel_dotfiles.py --check
  - python -m pytest -q
handoff: Provide the client/OS hook matrix, simulated manual/automatic compact and restart logs, doctor failure fixtures, bounded checkpoint proof, and exact implementation head for independent W4b.
stop_condition: Stop before editing per-user agent settings without explicit Owner action.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.json
verified_at: 2026-07-29T02:21:42+09:00
verified_by: codex-root-v080-w4a
evidence_refs:
  - reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142.json
---

# UNIT-TASK-AR-644-001 - Replace platform-specific hook shims with verified Python entrypoints

## Context

The focused suite passes while shipped Codex hooks still invoke Windows-only
or machine-specific commands, omit `commandWindows` and compact lifecycle
events, and never wire the generic continuity entrypoint. Current official
Codex and Claude hook contracts support `SessionStart`, `PreCompact`, and
`PostCompact`.

## Inputs

- reviews/REVIEW-2026-07-29-task-ar-644-w0-t3-replan.md
- .codex/hooks.json
- src/agent_runtime/templates/project/.codex/hooks.json
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/install_hooks.py

## Target Files

- agents/lead_engineer/tasks/units/TASK-AR-644/UNIT-TASK-AR-644-001.md
- .codex/hooks.json
- scripts/bootstrap_dev_env.py
- scripts/verify_wheel_dotfiles.py
- scripts/session_start_hook.py
- scripts/session_compact_hook.py
- scripts/session_resume_check.py
- agents/project/RUNTIME-ASSET-REGISTRY.json
- agents/runtime/session_checkpoints/.gitignore
- pyproject.toml
- src/agent_runtime/hook_runtime.py
- src/agent_runtime/doctor.py
- src/agent_runtime/templates/project/.codex/hooks.json
- src/agent_runtime/templates/project/agents/runtime/session_checkpoints/.gitignore
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/session_compact_hook.py
- src/agent_runtime/templates/project/scripts/session_resume_check.py
- src/agent_runtime/templates/project/scripts/install_hooks.py
- src/agent_runtime/templates/project/scripts/test_install_hooks.py
- src/agent_runtime/templates/project/AGENTS.md
- src/agent_runtime/templates/project/CLAUDE.md
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- tests/test_session_continuity_hooks.py
- tests/test_bootstrap_dev_env.py
- tests/test_session_resume_check.py
- tests/test_interrupted_run_detector.py
- tests/test_doctor.py
- tests/test_template_smoke.py
- tests/test_session_dashboard.py
- tests/test_stop_hook_owner_governance.py
- tests/test_update_notify.py
- tests/fixtures/host/agent_runtime.lock.json
- agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.json
- agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.log.md
- agents/runtime/task_claims/CLAIM-20260729-012532-task-ar-644-644001.handoff.md
- reviews/W4A-2026-07-29-unit-task-ar-644-001.md
- reviews/W4B-2026-07-29-unit-task-ar-644-001.md
- reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142.json
- reviews/INDEX.md

## Scope

Use one allowlisted Python dispatcher with POSIX and `commandWindows`
commands, add bounded derived compact checkpoints and `SessionStart`
reinjection, retain explicit owner-run Claude installation, and verify tracked
hook health. Do not mutate consumer repositories or real per-user settings,
persist prompt/transcript content, redesign compound/scribe, commit checkpoint
state, or perform a release.

## Steps

1. Add the packaged allowlisted hook dispatcher and portable command matrix.
2. Replace the project-specific start hook with bounded generic host/work,
   resume, compound-read, and compact-checkpoint context.
3. Add atomic pre-compact checkpoint and post-compact rebootstrap handling.
4. Wire tracked Codex hooks and explicit owner-run Claude installation.
5. Teach doctor and bootstrap checks to reject incomplete, stale, or
   machine-specific hook contracts.
6. Prove clean-host packaging, root/template mirrors, compact/restart
   continuity, and fail-open advisory behavior.

## Acceptance Criteria

- No POSIX path depends on a `.cmd` file.
- Linux and Windows command variants resolve through the packaged dispatcher
  in a clean host.
- `SessionStart` reports host context, active work, minimal compound lookup,
  resume/pointer state, and compact checkpoint state with bounded output.
- `PreCompact` atomically saves derived non-conversational state and
  `PostCompact` marks rebootstrap without blocking or committing.
- Missing, malformed, stale, incomplete, or machine-specific hooks are visible
  in doctor; valid Codex hooks retain an explicit trust-review reminder.
- Claude hook installation changes only an explicit settings path and includes
  `SessionStart`, `PreCompact`, `PostCompact`, and `UserPromptSubmit`.

## Verification

- `python -m pytest tests/test_session_continuity_hooks.py tests/test_bootstrap_dev_env.py tests/test_session_resume_check.py tests/test_interrupted_run_detector.py tests/test_doctor.py tests/test_template_smoke.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python -m pytest -q`

## Handoff

Provide the client/OS hook matrix, simulated manual/automatic compact and
restart logs, doctor failure fixtures, bounded checkpoint proof, and exact
implementation head for independent W4b.

## Stop Boundary

Stop before editing per-user agent settings without explicit Owner action.
