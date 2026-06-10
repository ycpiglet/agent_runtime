---
type: review
id: REVIEW-2026-06-10-agent-runtime-taskset-dispatcher
task: TASK-AR-250
audience: owner
status: pass
signal: pass
score: 96
priority: High
tags: [task-set, parallel-panes, hook, skill, governance-gate, owner-brief]
---

# Task Set Dispatcher Review

## Bottom Line

- Summary: `taskset-* 진행` requests now have a concrete dispatcher, prompt hook, skill, and gate path.
- Result: agents can plan and claim a task set before editing, with human-readable display names and machine-stable IDs.
- Boundary: the dispatcher creates claims and worktree commands; it does not silently mutate git worktrees unless a future command explicitly adds that behavior.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Task-set alias planning | pass | `tests/test_taskset_dispatcher.py` |
| Task-set claim metadata | pass | `tests/test_task_claim_dispatcher.py` |
| Duplicate task-set claim block | pass | `tests/test_parallel_worktree_gate.py` |
| Prompt trigger context | pass | `tests/test_taskset_prompt_hook.py` |
| Backlog routing gate | pass | `tests/test_taskset_work_gate.py` |
| Governance integration | pass | `scripts/owner_governance_gate.py` |

## Action Board

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add `taskset_dispatcher.py` | lead-engineer | codex | `scripts/taskset_dispatcher.py` |
| Done | Add `taskset_work_gate.py` | lead-engineer | codex | `scripts/taskset_work_gate.py` |
| Done | Add `taskset_prompt_hook.py` and Codex hook entry | lead-engineer | codex | `.codex/hooks.json` |
| Done | Add task-set skill guidance | lead-engineer | codex | `skills/taskset-dispatch/SKILL.md` |
| Done | Mirror scripts and rules into project template | doc-steward | codex | `src/agent_runtime/templates/project/` |

## Risks / Blockers

- Risk: actual git worktree creation is still an explicit returned command, not an automatic side effect.
- Risk: UI progress rendering is planned in `TASK-AR-248`; this task only creates the backend workflow and gates.
- Blocker: none for task-set dispatch and governance enforcement.

## Insight

- The useful unit of parallelism is the task set claim, not the visible terminal container.
- Human display names such as `Quality Sentinel` and `Progress Scout` make the board readable while stable fields remain machine IDs.
- The prevention layer has to be executable: prompt trigger, dispatcher, claim metadata, and gate are all needed.

## Decision

- Decision: one active claim per `task_set_id` is the default safety rule.
- Decision: task-set prompts should route through `scripts/taskset_dispatcher.py` before file edits.
- Decision: generated host projects inherit the same scripts, hooks, and concise skill doc.

## Next Steps

1. Use `taskset-progress-scout 진행해줘` style prompts from new panes to exercise the workflow.
2. Continue `TASK-AR-248` for UI display of the progress fields already enforced here.
3. Continue `TASK-AR-249` for richer claim progress updates if needed after UI integration.
