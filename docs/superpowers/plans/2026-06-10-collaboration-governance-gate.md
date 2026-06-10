# Collaboration Governance Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make multi-agent collaboration, role usage, waivers, and lifecycle hygiene measurable and gateable in `agent_runtime`.

**Architecture:** Add a repository-local collaboration policy file, explicit waiver records, and a deterministic gate that reads task claims, review artifacts, root runtime tools, and lifecycle metadata. Wire the gate into Owner governance and mirror the policy/gate into the reusable project template.

**Tech Stack:** Python 3.10 standard library, JSON policy files, pytest, existing `scripts/*_gate.py` pattern.

---

### Task 1: Policy And Waiver Contract

**Files:**
- Create: `agents/project/COLLABORATION-GOVERNANCE.json`
- Create: `src/agent_runtime/templates/project/agents/project/COLLABORATION-GOVERNANCE.json`
- Create: `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json`

- [x] **Step 1: Add policy JSON**

Add a policy with schema `agent-runtime-collaboration-governance/v1`, minimum claim roles, required artifact prefixes, root capability paths, monitored roles, and lifecycle thresholds.

- [x] **Step 2: Add root waiver JSON**

Record temporary waivers for root-level Ralph, retro, scribe, and doc-steward runtime tools plus missing `RETRO-*` artifact evidence. Each waiver must include `subjects`, `reason`, `approved_by`, `created_at`, `expires_at`, and `mitigation`.

### Task 2: Collaboration Governance Gate

**Files:**
- Create: `scripts/collaboration_governance_gate.py`
- Create: `src/agent_runtime/templates/project/scripts/collaboration_governance_gate.py`
- Test: `tests/test_collaboration_governance_gate.py`

- [x] **Step 1: Write failing tests**

Cover missing policy, missing required role/artifact/capability without waiver, waiver conversion from block to waived, and Owner gate wiring.

- [x] **Step 2: Implement gate**

Read JSON policy and waiver files. Count claim roles, review artifact prefixes, active claims, future heartbeat drift, released-claim phase/progress drift, and root capability paths. Return non-zero only for unwaived block findings.

- [x] **Step 3: Mirror gate into template**

Copy the same script into `src/agent_runtime/templates/project/scripts/`.

### Task 3: Owner Governance Wiring And Evidence

**Files:**
- Modify: `scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- Create: `reviews/REVIEW-2026-06-10-agent-runtime-collaboration-governance-redesign.md`

- [x] **Step 1: Wire new gate**

Add `["scripts/collaboration_governance_gate.py", "--check"]` after continuity/taskset gates.

- [x] **Step 2: Record audit review**

Record the meaning of waiver vs runtime promotion, the enforced checks, and current known gaps.

### Task 4: Verification

**Files:**
- No new files.

- [x] **Step 1: Run focused tests**

Run:

```powershell
$env:PYTHONPATH='src'; pytest tests/test_collaboration_governance_gate.py tests/test_continuity_contract_gate.py tests/test_response_contract_gate.py
```

Expected: all selected tests pass.

Observed on 2026-06-10:

```text
12 passed in 9.17s
```

- [x] **Step 2: Run focused gate**

Run:

```powershell
$env:PYTHONPATH='src'; python scripts/collaboration_governance_gate.py --root . --check
```

Expected: `collaboration-governance-gate: pass`, with waived findings shown for explicitly waived subjects.

Observed on 2026-06-10:

```text
collaboration-governance-gate: pass
block=0
watch=10
waived=6
```

### Additional Verification Notes

Owner governance gate was also run after wiring:

```text
status=pass
```

Broad pytest was attempted but is not a valid green completion signal yet:

```text
$env:PYTHONPATH='src'; pytest
collection failed with 7 import errors

$env:PYTHONPATH='.;src'; pytest
collection failed with 4 template-project import errors

$env:PYTHONPATH='.;src;src/agent_runtime/templates/project'; pytest
timed out after 180s with multiple template-project failures in progress

$env:PYTHONPATH='.;src'; pytest tests
timed out after 180s after collecting 321 root tests
```

This plan is closed for the collaboration governance gate implementation. Broad-suite cleanup remains separate repo health work.
