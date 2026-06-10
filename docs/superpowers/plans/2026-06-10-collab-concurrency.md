# Collaboration Concurrency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the real-time collaboration research and implement a first-pass conflict-control layer for multi-pane work.

**Architecture:** Workers use per-task worktrees and append-only pane events. The root checkout remains the orchestrator and only direct SSoT writer. UI and board surfaces read derived state from task files, claims, and pane events.

**Tech Stack:** Python scripts, JSONL event logs, markdown task records, existing owner governance gates.

---

## Sync Audit

- [x] 2026-06-11 audit result: this is the canonical plan for the multi-pane collision and realtime collaboration issue raised in the session.
- [x] The canonical task set is `TASKSET-AR-COLLAB-CONCURRENCY`.
- [x] The canonical tasks are `TASK-AR-251`, `TASK-AR-252`, `TASK-AR-253`, `TASK-AR-254`, `TASK-AR-255`, and `TASK-AR-256`.
- [x] The task set appears in `BACKLOG-BOARD.md` under `Archived Task Sets` because all six tasks are completed.
- [x] The task set is summarized in `BACKLOG.md`, `STATUS.md`, `AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF.md`, and `agents/project/NEXT-SESSION-POINTER.yml`.
- [x] No duplicate task set should be created for the same multi-pane scope.

## File Structure

- Owner brief: `AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF.md`
- Research record: `reviews/RESEARCH-2026-06-10-realtime-collab-conflict-patterns.md`
- Implementation plan: `docs/superpowers/plans/2026-06-10-collab-concurrency.md`
- Task files: `agents/lead_engineer/tasks/TASK-AR-251.md` through `agents/lead_engineer/tasks/TASK-AR-256.md`
- Event log CLI: `scripts/pane_event_log.py`
- Event log tests: `tests/test_pane_event_log.py`
- SSoT concurrency gate: `scripts/collaboration_concurrency_gate.py`
- SSoT concurrency tests: `tests/test_collaboration_concurrency_gate.py`
- Task-set dispatcher: `scripts/taskset_dispatcher.py`
- Task-set dispatcher tests: `tests/test_taskset_dispatcher.py`
- UI state adapter: `src/agent_runtime/ui_state.py`
- UI state tests: `tests/test_ui_state.py`
- Owner gate integration: `scripts/owner_governance_gate.py`
- Template owner gate integration: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`

### Task 1: Record research and task set

**Files:**
- Create: `AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF.md`
- Create: `reviews/RESEARCH-2026-06-10-realtime-collab-conflict-patterns.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-251.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-252.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-253.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-254.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-255.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-256.md`
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `BACKLOG-BOARD.md`

- [x] Record the platform research synthesis for Google Docs/Slides, Figma, Notion, Firestore, ActivityPub, and AT Protocol.
- [x] Translate the research into local design decisions: append-only pane events, single-writer SSoT ownership, and worktree-first worker execution.
- [x] Register `TASKSET-AR-COLLAB-CONCURRENCY` with exactly six canonical tasks.
- [x] Update the Owner-facing backlog/status surfaces so the task set can be found after archive.

### Task 2: Add append-only pane events

**Files:**
- Create: `scripts/pane_event_log.py`
- Create: `tests/test_pane_event_log.py`

- [x] Implement `record` support that writes JSONL pane events under `agents/runtime/pane_events/`.
- [x] Include event fields for timestamp, actor, pane, task, task set, claim, event type, and metadata.
- [x] Keep event records append-only so workers report state instead of editing shared truth files.
- [x] Test monotonic sequence behavior and replay summary grouping by task set.

### Task 3: Add concurrency gate

**Files:**
- Create: `scripts/collaboration_concurrency_gate.py`
- Create: `tests/test_collaboration_concurrency_gate.py`
- Modify: `scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`

- [x] Implement a gate that scans pane events for shared SSoT write attempts.
- [x] Treat non-orchestrator writes to `BACKLOG.md`, `STATUS.md`, `BACKLOG-BOARD.md`, `owner-docs.yml`, and `agents/project/NEXT-SESSION-POINTER.yml` as blocking findings.
- [x] Allow orchestrator-owned SSoT write events.
- [x] Wire the gate into the root and template owner governance gate.

### Task 4: Automate worktree-first taskset start

**Files:**
- Modify: `scripts/taskset_dispatcher.py`
- Modify: `tests/test_taskset_dispatcher.py`

- [x] Make `taskset_dispatcher start` create the missing per-task worktree before claim creation.
- [x] Keep worktree validation after creation so claims cannot falsely assert isolation.
- [x] Preserve duplicate-claim protection and task-set preflight behavior.
- [x] Use `AGENT_RUNTIME_GIT` in tests so the worktree create path is tested without mutating real git state.

### Task 5: Surface collaboration state

- [x] Add pane event loading to `agent_runtime.ui_state`.
- [x] Add `collaboration` resource summary for UI/API consumers.

**Files:**
- Modify: `src/agent_runtime/ui_state.py`
- Modify: `tests/test_ui_state.py`
- Modify: `docs/UI_STATE_API_EXAMPLES.md`

- [x] Read pane events into the UI state adapter.
- [x] Expose a `collaboration` summary grouped by active task set and pane.
- [x] Include `pane_events` in the UI state source list.
- [x] Test event summary exposure using fixed sample pane events.

### Task 6: Keep the sync surfaces discoverable

**Files:**
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `BACKLOG-BOARD.md`
- Modify: `agents/project/NEXT-SESSION-POINTER.yml`
- Modify: `owner-docs.yml`

- [x] Keep `TASKSET-AR-COLLAB-CONCURRENCY` visible in archived task-set reporting after completion.
- [x] Keep completed task files visible in the archived task file table with `task_uid` and lifecycle metadata.
- [x] List `AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF.md` in `owner-docs.yml`.
- [x] Keep next-session rules explicit: 5+ pane work uses isolated worktrees, append-only pane events, and orchestrator-owned SSoT writes.

## Verification Commands

- [x] Run focused pane event tests: `pytest tests/test_pane_event_log.py -q`
- [x] Run focused concurrency gate tests: `pytest tests/test_collaboration_concurrency_gate.py -q`
- [x] Run focused dispatcher tests: `pytest tests/test_taskset_dispatcher.py -q`
- [x] Run focused UI state tests: `pytest tests/test_ui_state.py -q`
- [x] Run task-set gate: `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-COLLAB-CONCURRENCY --require-complete --check`
- [x] Run owner governance gate: `python scripts/owner_governance_gate.py`
