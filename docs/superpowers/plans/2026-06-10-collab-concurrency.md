# Collaboration Concurrency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the real-time collaboration research and implement a first-pass conflict-control layer for multi-pane work.

**Architecture:** Workers use per-task worktrees and append-only pane events. The root checkout remains the orchestrator and only direct SSoT writer. UI and board surfaces read derived state from task files, claims, and pane events.

**Tech Stack:** Python scripts, JSONL event logs, markdown task records, existing owner governance gates.

---

### Task 1: Record research and task set

- [x] Create the owner brief and research review.
- [x] Register `TASKSET-AR-COLLAB-CONCURRENCY`.
- [x] Add `TASK-AR-251` through `TASK-AR-256`.

### Task 2: Add append-only pane events

- [x] Add `scripts/pane_event_log.py`.
- [x] Add tests for monotonic append and task-set summary.

### Task 3: Add concurrency gate

- [x] Add `scripts/collaboration_concurrency_gate.py`.
- [x] Block non-orchestrator SSoT write attempts.
- [x] Wire the gate into owner governance.

### Task 4: Automate worktree-first taskset start

- [x] Make `taskset_dispatcher start` create a missing task worktree before claim creation.
- [x] Keep preflight checks after worktree creation.

### Task 5: Surface collaboration state

- [x] Add pane event loading to `agent_runtime.ui_state`.
- [x] Add `collaboration` resource summary for UI/API consumers.
