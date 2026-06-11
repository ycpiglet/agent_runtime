# RSI Operating System Taskset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register and then implement `TASKSET-AR-RSI-OPERATING-SYSTEM`, an Evidence-to-Proposal OS that turns trace, eval, grader, A2A, correction, review, retro, failure, compound, and Owner conversation evidence into bounded proposals.

**Architecture:** Build on the completed `TASKSET-AR-RSI-PLANNING` B-mode substrate without reopening it. Add registries first, then proposal quality metrics, council review, A2A lifecycle verification, bounded apply gates, and a small skill layer.

**Tech Stack:** Markdown task files, `BACKLOG.md`, `BACKLOG-BOARD.md`, `STATUS.md`, `owner-docs.yml`, `agents/project/evidence/`, `agents/project/casebooks/`, Python standard-library gates, existing `scripts/planning_loop.py`, and existing Owner governance gates.

---

## File Structure

- Create: `agents/project/evidence/README.md`
- Create: `agents/project/evidence/inbox/README.md`
- Create: `agents/project/evidence/evaluations/README.md`
- Create: `agents/project/evidence/verification/README.md`
- Create: `agents/project/casebooks/README.md`
- Create: `agents/project/casebooks/failure-and-compound-casebook.md`
- Create: `AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF.md`
- Create: `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md`
- Create: `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-297.md` through `TASK-AR-305.md`
- Modify: `scripts/backlog_board.py`
- Modify: `tests/test_backlog_board_tasksets.py`
- Modify: `BACKLOG.md`, `STATUS.md`, `owner-docs.yml`, `agents/project/NEXT-SESSION-POINTER.yml`

## Task Set

Canonical task set: `TASKSET-AR-RSI-OPERATING-SYSTEM`

Registered tasks:

- `TASK-AR-297` - Register evidence inbox and conversation capture contract
- `TASK-AR-298` - Create evaluation and verification record registry
- `TASK-AR-299` - Build failure and compound casebook registry
- `TASK-AR-300` - Define evidence-to-proposal engine contract
- `TASK-AR-301` - Add council review and quantitative proposal metrics
- `TASK-AR-302` - Verify A2A message lifecycle as planning evidence
- `TASK-AR-303` - Preserve latent C-mode and bounded apply gate roadmap
- `TASK-AR-304` - Package RSI operating-system skill layer
- `TASK-AR-305` - Add RSI operating-system verification and Owner handoff

### Task 1: Registration

**Files:**
- Create: `agents/lead_engineer/tasks/TASK-AR-297.md` through `TASK-AR-305.md`
- Modify: `scripts/backlog_board.py`
- Modify: `tests/test_backlog_board_tasksets.py`

- [ ] **Step 1: Add taskset definition**

Add `TASKSET-AR-RSI-OPERATING-SYSTEM` to `TASK_SET_DEFINITIONS` with display name `Evidence-to-Proposal Operator` and order `61`.

- [ ] **Step 2: Add task files**

Create planned task records for `TASK-AR-297` through `TASK-AR-305`; each record must include `task_uid`, lifecycle timestamps, `status: planned`, and `task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM`.

- [ ] **Step 3: Update backlog-board test**

Update `test_real_backlog_tasks_are_classified_into_fifteen_task_sets` to expect the new taskset and rename it to `sixteen`.

- [ ] **Step 4: Regenerate board**

Run: `python scripts/backlog_board.py --write`

Expected: `BACKLOG-BOARD.md` includes `Evidence-to-Proposal Operator`.

### Task 2: Evidence And Casebook Registration

**Files:**
- Create: `agents/project/evidence/README.md`
- Create: `agents/project/evidence/inbox/README.md`
- Create: `agents/project/evidence/evaluations/README.md`
- Create: `agents/project/evidence/verification/README.md`
- Create: `agents/project/casebooks/README.md`
- Create: `agents/project/casebooks/failure-and-compound-casebook.md`

- [ ] **Step 1: Add registry docs**

Each registry document must define purpose, fields, routing rules, and local-vs-provider-live boundaries.

- [ ] **Step 2: Add seed cases**

Seed the casebook with BRIEF drift, continuity pointer gap, taskset completion inference, and RSI evidence scatter.

- [ ] **Step 3: Verify docs are discoverable**

Run: `rg -n "rsi-evidence-scattered|proposal_precision|TASKSET-AR-RSI-OPERATING-SYSTEM" agents/project`

Expected: all three terms are found.

### Task 3: Owner-Facing Registration

**Files:**
- Create: `AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF.md`
- Create: `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md`
- Create: `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md`
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `owner-docs.yml`
- Modify: `agents/project/NEXT-SESSION-POINTER.yml`

- [ ] **Step 1: Add Owner brief**

The brief must use `Bottom Line`, `Signal`, `Insight`, `Decision`, `Action Board`, `Risks / Blockers`, and `Next Steps`.

- [ ] **Step 2: Record the conversation**

The meeting record must capture the Owner's request to record this dialogue, manage eval/verification records, add failure/compound casebooks, preserve C as latent, and register A.

- [ ] **Step 3: Add registration review**

The review must state registration only, not implementation completion.

- [ ] **Step 4: Sync pointers**

Update backlog, status, owner-doc manifest, and next-session pointer so the taskset is resumable.

### Task 4: Verification

**Files:**
- Modify: generated `BACKLOG-BOARD.md`

- [ ] **Step 1: Run focused tests**

Run: `pytest tests/test_backlog_board_tasksets.py tests/test_task_identity.py -q`

Expected: pass.

- [ ] **Step 2: Run gates**

Run:

```powershell
python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-RSI-OPERATING-SYSTEM --check
python scripts/owner_doc_format_gate.py --manifest owner-docs.yml
python scripts/task_identity.py check --check
```

Expected: all commands pass.

## Self-Review

- Spec coverage: covers A안 registration, conversation record, eval/verification directories, failure/compound casebook, C latent option, and resumability pointers.
- Placeholder scan: no task is registered without a concrete scope and evidence target.
- Type consistency: taskset ID, task IDs, directory names, and review names are consistent across task files, plan, backlog, status, and owner-doc pointers.

