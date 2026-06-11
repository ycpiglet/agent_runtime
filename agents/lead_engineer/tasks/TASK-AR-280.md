---
id: TASK-AR-280
display_id: TASK-AR-280
task_uid: d9f3edb5-70e5-43c5-a6ed-b85c5f1c3280
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11T08:42:47+09:00
completed_at: 2026-06-11T09:05:05+09:00
updated_at: 2026-06-11T09:05:05+09:00
title: Apply design treatment to agent and command panes
status: completed
priority: P1
difficulty: M
est_hours: 3
est_tokens: 1100
owner: lead_engineer
task_set_id: TASKSET-AR-UI-DESIGN-IMPLEMENTATION
updated: 2026-06-11
tags: [ui-design, agents, commands, ui-console]
---

# TASK-AR-280 - Apply design treatment to agent and command panes

## Goal

Make active agent state, claims, progress, and command safety boundaries visible in the console design language.

## Acceptance Criteria

- Agent cards emphasize role, status, score, task claim, and progress metadata.
- Command controls keep type, target, payload, and result clearly visible.
- Unsupported or high-risk runtime controls remain explicit rather than visually hidden.

## Completion Evidence

- Implemented agent and command card hierarchy in `src/agent_runtime/ui_console.py`.
- Added agent `score` and `score_label` exposure in `src/agent_runtime/ui_state.py`.
- Added focused UI/state tests covering the new operational hierarchy.
- Focused verification passed with `python -m pytest tests/test_ui_console.py tests/test_ui_state.py tests/test_ui_commands.py -q` (`42 passed`).
- Full pytest passed with `346 passed`.
- Owner review recorded in `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-280-agent-command-panes.md`.
