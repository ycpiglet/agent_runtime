# Measured Improvement Continuity Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make loop engineering, bilingual README, live work pointer continuity, repeated-request API promotion, and Compound recurrence capture enforceable.

**Architecture:** Add a narrow continuity contract gate that checks normative docs and the template live work pointer. Wire it into Owner governance, publish, and doctor checks. Keep README concise and bilingual, while detailed operational rules live in AGENTS/CLAUDE, task claims, and pointer files.

**Tech Stack:** Python gate scripts, pytest, Markdown/YAML docs, existing `agent_runtime` publish and governance gates.

---

### Task 1: Continuity Gate

**Files:**
- Create: `scripts/continuity_contract_gate.py`
- Create: `src/agent_runtime/templates/project/scripts/continuity_contract_gate.py`
- Test: `tests/test_continuity_contract_gate.py`

- [x] **Step 1: Write failing tests**

Run: `PYTHONPATH=.;src pytest tests/test_continuity_contract_gate.py -q`
Expected: FAIL because the gate and governance wiring do not exist.

- [ ] **Step 2: Implement gate**

The gate checks:
- `README.md` has Korean and English sections.
- Template `AGENTS.md` and `CLAUDE.md` mention session continuity.
- Template `NEXT-SESSION-POINTER.yml` exists.
- Repeated requests must be promoted to a function, script, API, hook, or gate.
- Repeated criticism must be reflected into Compound automatically or as a mandatory closure step.

- [ ] **Step 3: Verify gate**

Run: `PYTHONPATH=.;src pytest tests/test_continuity_contract_gate.py -q`
Expected: PASS.

### Task 2: Normative Docs

**Files:**
- Modify: `README.md`
- Modify: `src/agent_runtime/templates/project/AGENTS.md`
- Modify: `src/agent_runtime/templates/project/CLAUDE.md`
- Create: `src/agent_runtime/templates/project/agents/project/NEXT-SESSION-POINTER.yml`

- [ ] **Step 1: README**

Make `README.md` human-friendly and bilingual. Keep quick install and direct pointers to detailed docs.

- [ ] **Step 2: AGENTS/CLAUDE**

Add rules for:
- live work pointer updates;
- README/AGENTS/CLAUDE continuous improvement;
- measured improvement loops;
- repeated prompt/API promotion;
- Compound recurrence capture;
- Owner-owned evaluation criteria and merge decisions.

- [ ] **Step 3: Pointer**

Create `NEXT-SESSION-POINTER.yml` with current state, active_work, resume command hints, roles, active task pointers, and required update rules.

### Task 3: Gate Integration

**Files:**
- Modify: `scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- Modify: `src/agent_runtime/doctor.py`
- Modify: `src/agent_runtime/publish_bundle.py`
- Modify: `src/agent_runtime/publish_check.py`
- Modify: `tests/test_inventory_sync_sanitize.py`
- Modify: `tests/fixtures/host/agent_runtime.lock.json`

- [ ] **Step 1: Wire governance**

Run `continuity_contract_gate.py --check` from Owner governance before parallel worktree checks.

- [ ] **Step 2: Ship and publish**

Include root and template gate scripts in doctor, publish check, and public bundle.

- [ ] **Step 3: Refresh lock**

Run: `PYTHONPATH=src python -m agent_runtime.cli lock --root tests\fixtures\host --write`
Expected: `findings=0`.

### Task 4: Verification

**Files:**
- All touched files.

- [ ] **Step 1: Focused tests**

Run: `PYTHONPATH=.;src pytest tests/test_continuity_contract_gate.py tests/test_inventory_sync_sanitize.py -q`
Expected: PASS.

- [ ] **Step 2: Governance checks**

Run:
- `PYTHONPATH=src python scripts/continuity_contract_gate.py --check`
- `PYTHONPATH=src python scripts/owner_governance_gate.py --allow-empty-owner-docs`
- `PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check`

Expected: all `findings=0`.

- [ ] **Step 3: Full tests**

Run: `PYTHONPATH=.;src pytest tests -q`
Expected: PASS.
