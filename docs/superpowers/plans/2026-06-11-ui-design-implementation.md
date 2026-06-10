# UI Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the accepted Agent Runtime design system across the live runtime console panes while keeping operational evidence and command safety visible.

**Architecture:** Keep `TASKSET-AR-UI-DESIGN-SYSTEM` as completed research/design evidence. Track implementation as a separate active task set, `TASKSET-AR-UI-DESIGN-IMPLEMENTATION`, so backlog views show real remaining design work instead of hiding it in the archive.

**Tech Stack:** Python standard library web server, inline HTML/CSS/JavaScript in `src/agent_runtime/ui_console.py`, markdown task records, generated `BACKLOG-BOARD.md`.

---

## File Structure

- `src/agent_runtime/ui_console.py`: runtime console HTML/CSS/JS implementation target.
- `tests/test_ui_console.py`: token and shell contract tests for the visual system.
- `docs/design/agent-runtime/DESIGN.md`: accepted design decision and token guide.
- `agents/lead_engineer/tasks/TASK-AR-278.md` through `TASK-AR-284.md`: active implementation backlog.
- `BACKLOG.md`, `STATUS.md`, `BACKLOG-BOARD.md`: Owner-facing backlog/status surfaces.

### Task 1: Console Shell Design Implementation

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Modify: `tests/test_ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-278.md`

- [ ] **Step 1: Lock shell tokens**

Ensure the CSS served by `/app.css` includes `--canvas`, `--primary`, and the accepted Linear canvas `#010102`.

- [ ] **Step 2: Apply shell layout**

Use `docs/design/agent-runtime/DESIGN.md` as the visual source of truth for the topbar, hero, metrics, cards, tabs, and sticky detail panel.

- [ ] **Step 3: Validate focused shell behavior**

Run: `python -m pytest tests/test_ui_console.py`

Expected: all UI console tests pass.

### Task 2: Backlog Pane Visual Hierarchy

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-279.md`

- [ ] **Step 1: Emphasize lanes**

Style backlog lanes so status, task id, priority, owner, and evidence are scannable without relying on color alone.

- [ ] **Step 2: Preserve task mutation controls**

Keep existing task create/update/archive/reorder route behavior unchanged.

### Task 3: Agent and Command Pane Treatment

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-280.md`

- [ ] **Step 1: Surface active agents**

Style agent cards around role, status, score, current task, and claim/progress metadata.

- [ ] **Step 2: Surface command safety**

Keep command forms explicit about type, target, payload, outcome, and unsupported runtime controls.

### Task 4: Evidence and Event Pane Treatment

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-281.md`

- [ ] **Step 1: Elevate audit evidence**

Give evidence, replay, event, and error cards clear pass/warn/fail severity treatment while preserving labels.

- [ ] **Step 2: Preserve filtering**

Keep event filters and evidence lists route-compatible with the existing state adapter.

### Task 5: Map, Planner, Source, and Write Pane Treatment

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-282.md`

- [ ] **Step 1: Make maps operational**

Use the same design system for graph, state-machine, roadmap, source, and write surfaces.

- [ ] **Step 2: Keep read/write boundaries visible**

Do not make derived map/source surfaces look like direct mutation controls.

### Task 6: Responsive and Accessibility Polish

**Files:**
- Modify: `src/agent_runtime/ui_console.py`
- Modify: `tests/test_ui_console.py`
- Task: `agents/lead_engineer/tasks/TASK-AR-283.md`

- [ ] **Step 1: Preserve mobile breakpoints**

Keep desktop density while ensuring single-column mobile panes remain readable.

- [ ] **Step 2: Preserve non-color state**

Every color-coded state must retain visible text labels.

### Task 7: Visual QA and Owner Handoff

**Files:**
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `BACKLOG-BOARD.md`
- Task: `agents/lead_engineer/tasks/TASK-AR-284.md`

- [ ] **Step 1: Run focused checks**

Run: `python -m pytest tests/test_ui_console.py tests/test_backlog_board_tasksets.py`

Expected: all focused tests pass.

- [ ] **Step 2: Run Owner gate**

Run: `python scripts/owner_governance_gate.py`

Expected: all blocking gates pass.

- [ ] **Step 3: Publish handoff**

Record what panes were visually completed, what remains, and whether screenshots/browser review were performed.
