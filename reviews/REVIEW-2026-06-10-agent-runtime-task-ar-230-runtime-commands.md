---
type: review
id: REVIEW-2026-06-10-agent-runtime-task-ar-230-runtime-commands
task: TASK-AR-230
audience: owner
status: pass
signal: pass
score: 91
priority: High
tags: [ui-console, runtime-commands, command-outbox, safety-boundary]
---

# TASK-AR-230 Runtime Command Controls Review

## Bottom Line

- Summary: `TASK-AR-230` is complete for command submission and auditability.
- Result: the UI can submit agent prompts through `/api/commands` without terminal embedding.
- Boundary: lifecycle commands are recorded as `pending_runtime_support`; execution is not claimed.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Command schema | pass | `runtime.call_agent`, `runtime.assign_task`, `runtime.request_review`, `runtime.request_meeting`, `runtime.goal.*` |
| Safe prompt bridge | pass | `runtime.call_agent` writes queued `runtime-command` message markdown |
| High-risk boundary | pass | commit/push/PR/install/deletion/external/long-running requests become `approval_required` |
| Unsupported lifecycle | pass | goal lifecycle requests become `pending_runtime_support` |
| UI route | pass | `POST /api/commands` and runtime command form |
| Tests | pass | `tests/test_ui_commands.py` 11 passed; `tests/test_ui_console.py` 9 passed |
| Smoke | pass | temporary-root route smoke produced one queued command and message |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add runtime command types | lead-engineer | codex | `src/agent_runtime/ui_commands.py` |
| Done | Add command route and form | lead-engineer | codex | `src/agent_runtime/ui_console.py` |
| Done | Record safety boundary | lead-engineer | codex | `docs/UI_RUNTIME_COMMANDS.md` |
| Next | Improve live logs and evidence views | lead-engineer | codex | `TASK-AR-231` |

## Risks / Blockers

- Risk: lifecycle commands are submitted but not executed until a runtime executor consumes them.
- Risk: keyword-based approval detection is conservative and should later move to a shared policy module.
- Blocker: none for UI command submission.

## Insight

- The useful boundary is command submission, not terminal control.
- `.ui_outbox` is now the shared audit trail for task writes, runtime prompts, approval holds, and unsupported lifecycle requests.

## Decision

- Decision: keep browser writes routed through local server validation and `.ui_outbox`.
- Decision: do not add PTY/WebSocket terminal embedding for lifecycle control.
- Decision: continue to `TASK-AR-231` for freshness, logs, evidence, and replay visibility.

## Next Steps

1. Add event timeline filtering and freshness assertions.
2. Surface recent errors and evidence links in dashboard/detail panels.
3. Keep command execution status distinct from command submission status.
