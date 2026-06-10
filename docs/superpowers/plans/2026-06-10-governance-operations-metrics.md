# Governance Operations Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Turn the remaining collaboration-governance, waiver burn-down, lifecycle cleanup, usage metrics, realtime sync, and test hygiene work into registered tasks with executable measurement and enforcement.

**Architecture:** Add a new `TASKSET-AR-GOVERNANCE-OPS` task set and register seven canonical task files. Promote template-only runtime capabilities into root where safe, add an asset registry for skill/hook/trigger/gate/script lifecycle tracking, and enforce it with a deterministic `runtime_asset_usage` gate wired into Owner governance.

**Tech Stack:** Python 3.10 standard library, JSON registry files, markdown task files, existing Owner governance gate pattern, pytest focused tests.

---

## File Structure

- `agents/lead_engineer/tasks/TASK-AR-257.md`: taskset planning and registration record.
- `agents/lead_engineer/tasks/TASK-AR-258.md`: waiver burn-down and root runtime capability promotion.
- `agents/lead_engineer/tasks/TASK-AR-259.md`: lifecycle drift cleanup and claim normalization.
- `agents/lead_engineer/tasks/TASK-AR-260.md`: skill/hook/trigger/gate/script usage and reuse measurement.
- `agents/lead_engineer/tasks/TASK-AR-261.md`: realtime backlog/status/pointer sync enforcement.
- `agents/lead_engineer/tasks/TASK-AR-262.md`: pytest collection hygiene and verification tier split.
- `agents/lead_engineer/tasks/TASK-AR-263.md`: governance operations report and deprecation decision loop.
- `AGENT_RUNTIME_GOVERNANCE_OPS_BRIEF.md`: Owner-facing BRIEF for this taskset.
- `agents/project/RUNTIME-ASSET-REGISTRY.json`: root asset lifecycle and usage registry.
- `src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json`: template copy of the registry.
- `scripts/runtime_asset_usage.py`: root executable usage/reuse lifecycle gate.
- `src/agent_runtime/templates/project/scripts/runtime_asset_usage.py`: template executable usage/reuse lifecycle gate.
- `tests/test_runtime_asset_usage.py`: focused tests for registry validation and lifecycle findings.
- `scripts/owner_governance_gate.py`: add `runtime_asset_usage.py --check`.
- `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`: mirror Owner gate wiring.
- `scripts/backlog_board.py`: add `TASKSET-AR-GOVERNANCE-OPS` to the Owner board.
- `src/agent_runtime/templates/project/scripts/backlog_board.py`: mirror taskset definition.
- `BACKLOG.md`: append operating-cycle registration note.
- `STATUS.md`: append current state note.
- `agents/project/NEXT-SESSION-POINTER.yml`: set the active governance-ops pointer.

## Task 1: Register Governance Ops Taskset

**Files:**
- Create: `AGENT_RUNTIME_GOVERNANCE_OPS_BRIEF.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-257.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-258.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-259.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-260.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-261.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-262.md`
- Create: `agents/lead_engineer/tasks/TASK-AR-263.md`
- Modify: `scripts/backlog_board.py`
- Modify: `src/agent_runtime/templates/project/scripts/backlog_board.py`
- Modify: `BACKLOG.md`
- Modify: `STATUS.md`
- Modify: `agents/project/NEXT-SESSION-POINTER.yml`

- [x] **Step 1: Create Owner BRIEF**

Create a BRIEF with `Bottom Line`, `Signal`, `Insight`, `Decision`, `Action Board`, and `Next`, listing all seven tasks and their completion criteria.

- [x] **Step 2: Create task files**

Create `TASK-AR-257` through `TASK-AR-263` with `task_set_id: TASKSET-AR-GOVERNANCE-OPS`, explicit owners, tags, audit logs, and completion criteria.

- [x] **Step 3: Add board taskset definition**

Add `TASKSET-AR-GOVERNANCE-OPS` to root and template `backlog_board.py` so generated Owner boards can route these tasks as one workflow.

- [x] **Step 4: Update state docs**

Add an operating-cycle entry to `BACKLOG.md`, add the current status to `STATUS.md`, and point `NEXT-SESSION-POINTER.yml` at `TASKSET-AR-GOVERNANCE-OPS`.

- [x] **Step 5: Regenerate board**

Run:

```powershell
python scripts/backlog_board.py --write
```

Expected: `BACKLOG-BOARD.md` includes `TASKSET-AR-GOVERNANCE-OPS` with open task rows.

## Task 2: Burn Down Collaboration Waivers

**Files:**
- Create: `scripts/agent_loop.py`
- Create: `scripts/agent_retro.py`
- Create: `scripts/promote_retro_forward.py`
- Create: `scripts/scribe_due.py`
- Create: `scripts/doc_steward_due.py`
- Create: `reviews/RETRO-2026-06-10-agent-runtime-governance-ops.md`
- Modify: `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json`

- [x] **Step 1: Promote safe template capabilities**

Copy the existing template implementations for agent loop, retro, retro-forward promotion, scribe due check, and doc-steward due check into root `scripts/`.

- [x] **Step 2: Record retro evidence**

Create a `RETRO-*` artifact under `reviews/` documenting the governance-ops feed-forward items.

- [x] **Step 3: Reduce waiver subjects**

Remove subjects that now have direct evidence: root Ralph/retro/scribe/doc-steward capabilities and `artifact:RETRO`. Keep only genuinely unresolved role-usage gaps such as `role-usage:scribe`.

- [x] **Step 4: Verify collaboration gate**

Run:

```powershell
$env:PYTHONPATH='src'; python scripts/collaboration_governance_gate.py --root . --check
```

Expected: pass with fewer waived findings than the previous `waived=6` baseline.

## Task 3: Add Runtime Asset Usage And Reuse Measurement

**Files:**
- Create: `agents/project/RUNTIME-ASSET-REGISTRY.json`
- Create: `src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json`
- Create: `scripts/runtime_asset_usage.py`
- Create: `src/agent_runtime/templates/project/scripts/runtime_asset_usage.py`
- Create: `tests/test_runtime_asset_usage.py`
- Modify: `scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`

- [x] **Step 1: Write focused tests**

Test missing registry, missing asset path, configured usage evidence, and invalid deprecation decisions.

- [x] **Step 2: Add registry**

Register active skills, hooks, triggers, gates, and runtime scripts with path, lifecycle decision, evidence paths, and minimum usage expectations.

- [x] **Step 3: Implement gate**

Read the registry, verify paths, count evidence references, classify unused/low-reuse assets as `watch`, and fail only on missing required assets or invalid deprecation decisions.

- [x] **Step 4: Wire Owner gate**

Add `["scripts/runtime_asset_usage.py", "--check"]` to root and template Owner governance gates.

- [x] **Step 5: Verify**

Run:

```powershell
$env:PYTHONPATH='.;src'; pytest tests/test_runtime_asset_usage.py tests/test_collaboration_governance_gate.py
$env:PYTHONPATH='src'; python scripts/runtime_asset_usage.py --check
```

Expected: tests pass; gate reports `block=0` with `watch` items for low-use or review-needed assets.

## Task 4: Clean Lifecycle Drift

**Files:**
- Modify: `agents/runtime/task_claims/*.json`
- Modify: corresponding `*.handoff.md`
- Modify: corresponding `*.log.md`
- Create: `reviews/REVIEW-2026-06-10-agent-runtime-lifecycle-drift-cleanup.md`

- [x] **Step 1: Normalize released claim metadata**

Set completed/released claims to `phase: taskset-completed` and `progress_pct: 100` only when the referenced task is actually complete.

- [x] **Step 2: Resolve future heartbeat drift**

Replace future heartbeat values with an actual observed timestamp and document why the drift occurred.

- [x] **Step 3: Resolve missing worktree references**

For active claims whose worktree is missing, either release the claim with evidence or recreate the dispatcher-managed worktree.

- [x] **Step 4: Verify lifecycle watch count**

Run:

```powershell
$env:PYTHONPATH='src'; python scripts/collaboration_governance_gate.py --root . --check
```

Expected: lifecycle watch findings are reduced and no unwaived blocks appear.

## Task 5: Enforce Realtime State Sync

**Files:**
- Create: `scripts/state_sync_gate.py`
- Create: `src/agent_runtime/templates/project/scripts/state_sync_gate.py`
- Create: `tests/test_state_sync_gate.py`
- Modify: `scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`

- [x] **Step 1: Define stale pointer invariants**

Compare task frontmatter, active claims, `BACKLOG-BOARD.md`, `STATUS.md`, and `NEXT-SESSION-POINTER.yml` for the active taskset.

- [x] **Step 2: Implement gate**

Block when the active taskset pointer contradicts task files or active claims. Watch when generated board timestamps lag behind task updates.

- [x] **Step 3: Wire Owner gate**

Add `state_sync_gate.py --check` after taskset and collaboration gates.

- [x] **Step 4: Verify**

Run:

```powershell
$env:PYTHONPATH='.;src'; pytest tests/test_state_sync_gate.py
$env:PYTHONPATH='src'; python scripts/state_sync_gate.py --check
```

Expected: test and gate pass.

## Task 6: Split Broad Test Collection Hygiene

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_pytest_collection_contract.py`
- Create: `reviews/REVIEW-2026-06-10-agent-runtime-pytest-hygiene.md`

- [x] **Step 1: Define root vs template test scopes**

Root tests should not collect generated-project template tests unless the template root is intentionally selected.

- [x] **Step 2: Add pytest config or markers**

Configure collection so `pytest tests` is the root fast suite and template tests run through an explicit template-suite command.

- [x] **Step 3: Verify focused scopes**

Run:

```powershell
$env:PYTHONPATH='.;src'; pytest tests/test_runtime_asset_usage.py tests/test_collaboration_governance_gate.py
```

Expected: focused tests pass without collecting template-project tests.

## Task 7: Publish Governance Operations Report

**Files:**
- Create: `scripts/governance_ops_report.py`
- Create: `tests/test_governance_ops_report.py`
- Create: `reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md`

- [x] **Step 1: Aggregate gate outputs**

Aggregate collaboration governance, runtime asset usage, taskset gate, state sync, and Owner document gate into one Owner-facing report.

- [x] **Step 2: Add deprecation decision table**

For each asset with low usage, include `keep`, `modify`, `deprecate`, or `remove` and the evidence path used for that decision.

- [x] **Step 3: Verify report generation**

Run:

```powershell
$env:PYTHONPATH='.;src'; pytest tests/test_governance_ops_report.py
$env:PYTHONPATH='src'; python scripts/governance_ops_report.py --out reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md --check
```

Expected: report exists, follows Owner BRIEF frame, and contains waiver/watch/block/action tables.

## Self-Review

- Spec coverage: covers detailed planning, task registration, execution start, role/usage/frequency/reuse/lifecycle measurement, skill/hook/trigger usage tracking, deprecation decisions, realtime state sync, and test hygiene.
- Placeholder scan: no task uses unspecified paths or vague "later" work; each task has exact files and commands.
- Type consistency: taskset id is consistently `TASKSET-AR-GOVERNANCE-OPS`; asset registry schema is `agent-runtime-asset-registry/v1`; usage gate command is `scripts/runtime_asset_usage.py --check`.

