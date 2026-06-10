# Pane Progress Task Sets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make pane, task-set, phase, step, and rough progress visible and testable so parallel workers can resume like a game-style live status board.

**Architecture:** Add the test contract first, then project the contract through claim records and `ui_state`, then render it in the local console. Enforcement stays repo-local: claim JSON is the active runtime source, `NEXT-SESSION-POINTER.yml` is the human handoff pointer, and backlog tasks define independent work packets.

**Tech Stack:** Python stdlib, pytest, JSON/JSONL, Markdown frontmatter, existing `agent_runtime.ui_state`, `agent_runtime.ui_console`, and `scripts/task_claim_dispatcher.py`.

---

## File Structure

- Create `agents/project/evals/pane-progress-v1.jsonl`: fixed golden set for progress phases, step labels, rough percent bounds, and task-set aggregation.
- Modify `agents/project/DATASET-CATALOG.yml`: register the pane progress goldset so it is discoverable by eval tooling.
- Create `tests/test_pane_progress_contract.py`: validates the committed goldset independently of implementation code.
- Modify `scripts/task_claim_dispatcher.py`: accepts and writes `step_index`, `step_total`, `status_text`, `task_set_id`, and `updated_at`.
- Modify `src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`: keeps generated host templates aligned with the root script.
- Modify `src/agent_runtime/ui_state.py`: exposes per-pane progress and aggregated `task_sets`.
- Modify `src/agent_runtime/ui_console.py`: renders progress bars, phase labels, step counters, and status text in the Agents view and task-set summary.
- Modify `tests/test_task_claim_dispatcher.py`, `tests/test_ui_state.py`, and `tests/test_ui_console.py`: cover the new contract at each layer.
- Modify `docs/UI_STATE_API_EXAMPLES.md` and `docs/UI_CONSOLE_MVP.md`: document the JSON/API shape and UI behavior.
- Modify `scripts/continuity_contract_gate.py` and template copy only if progress fields are not enforced by existing checks.

## Task 1: TASK-AR-247 Testset Contract

**Files:**
- Create: `agents/project/evals/pane-progress-v1.jsonl`
- Modify: `agents/project/DATASET-CATALOG.yml`
- Create: `tests/test_pane_progress_contract.py`

- [ ] **Step 1: Write the failing goldset presence test**

```python
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "agents" / "project" / "evals" / "pane-progress-v1.jsonl"


def _rows() -> list[dict[str, object]]:
    return [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_pane_progress_goldset_exists_and_has_required_case_types():
    rows = _rows()
    case_types = {row["case_type"] for row in rows}
    assert {"typical", "edge", "adversarial", "ambiguous", "access-controlled"}.issubset(case_types)
    assert len(rows) >= 6
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_pane_progress_contract.py::test_pane_progress_goldset_exists_and_has_required_case_types -q`

Expected: FAIL because `agents/project/evals/pane-progress-v1.jsonl` does not exist.

- [ ] **Step 3: Add the committed golden set**

Create `agents/project/evals/pane-progress-v1.jsonl` with these records:

```jsonl
{"id":"pane-progress-001","domain":"runtime-progress","case_type":"typical","question":"lead_engineer@design-01 is implementing TASK-AR-248 in step 3 of 6. How should the UI summarize it?","difficulty":"standard","label":"show implementation phase, 3/6, rough percent, and readable status text","expected_outcome":{"phase":"implement","step_index":3,"step_total":6,"progress_pct_min":35,"progress_pct_max":60,"status_text_required":true},"source_refs":["agents/project/NEXT-SESSION-POINTER.yml","scripts/task_claim_dispatcher.py"],"query_contract":{"resource":"agents","requires":["pane_id","phase","step_index","step_total","progress_pct","status_text"]}}
{"id":"pane-progress-002","domain":"runtime-progress","case_type":"edge","question":"A claim has progress_pct 104. What should validation do?","difficulty":"edge","label":"reject progress outside 0..100","expected_outcome":{"valid":false,"finding":"progress_pct:out-of-range"},"source_refs":["scripts/task_claim_dispatcher.py"],"query_contract":{"resource":"claims","requires":["progress_pct"]}}
{"id":"pane-progress-003","domain":"runtime-progress","case_type":"adversarial","question":"A worker marks phase done while step_index is 2 of 6. What should the state contract report?","difficulty":"adversarial","label":"block inconsistent done phase before final step","expected_outcome":{"valid":false,"finding":"phase-step:inconsistent"},"source_refs":["agents/project/STATE-MACHINES.yml","scripts/continuity_contract_gate.py"],"query_contract":{"resource":"claims","requires":["phase","step_index","step_total"]}}
{"id":"pane-progress-004","domain":"runtime-progress","case_type":"ambiguous","question":"A worker has phase test and no progress_pct. How should the UI estimate progress?","difficulty":"ambiguous","label":"derive rough percent from phase and step counter, mark it approximate","expected_outcome":{"derived_progress":true,"progress_pct_min":60,"progress_pct_max":75,"approximate":true},"source_refs":["src/agent_runtime/ui_state.py"],"query_contract":{"resource":"agents","requires":["phase","step_index","step_total"]}}
{"id":"pane-progress-005","domain":"runtime-progress","case_type":"access-controlled","question":"A different pane wants to update another active pane claim. What should happen?","difficulty":"high","label":"require matching claim ownership or explicit dispatcher command","expected_outcome":{"valid":false,"finding":"claim-owner:mismatch"},"source_refs":["docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md","scripts/task_claim_dispatcher.py"],"query_contract":{"resource":"claims","requires":["claim_id","agent_instance_id","pane_id"]}}
{"id":"pane-progress-006","domain":"runtime-progress","case_type":"typical","question":"TASKSET-AR-PROGRESS has three tasks: one done, one implement 3/6 at 48%, one blocked at 20%. What should the task-set card show?","difficulty":"standard","label":"aggregate by task_set_id with done, active, blocked, and rough percent","expected_outcome":{"task_set_id":"TASKSET-AR-PROGRESS","done":1,"active":1,"blocked":1,"progress_pct_min":45,"progress_pct_max":65},"source_refs":["src/agent_runtime/ui_state.py"],"query_contract":{"resource":"task_sets","requires":["task_set_id","status","progress_pct"]}}
```

- [ ] **Step 4: Register the dataset**

Append this dataset under `datasets:` in `agents/project/DATASET-CATALOG.yml`:

```yaml
  - id: pane-progress-gold
    purpose: pane/task-set 진행률, 단계, 상태 문구, rough percent 표시 계약 검증
    owner: lead_engineer
    source_tier: lineage
    location: agents/project/evals/pane-progress-v1.jsonl
    label_type: human_gold
    minimum_score: 0.90
    metrics:
      - progress_contract
      - phase_step_consistency
      - task_set_aggregation
      - status_text_presence
    tags:
      - pane
      - progress
      - task-set
```

- [ ] **Step 5: Add the field contract test**

Add to `tests/test_pane_progress_contract.py`:

```python
def test_pane_progress_goldset_rows_have_contract_metadata():
    for row in _rows():
        assert row["id"].startswith("pane-progress-")
        assert row["domain"] == "runtime-progress"
        assert row["source_refs"]
        contract = row["query_contract"]
        assert contract["resource"] in {"agents", "claims", "task_sets"}
        assert contract["requires"]
        assert row["expected_outcome"]
```

- [ ] **Step 6: Run the contract tests**

Run: `PYTHONPATH=src pytest tests/test_pane_progress_contract.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add agents/project/DATASET-CATALOG.yml agents/project/evals/pane-progress-v1.jsonl tests/test_pane_progress_contract.py
git commit -m "test: add pane progress goldset"
```

## Task 2: TASK-AR-248 UI State And Console Progress

**Files:**
- Modify: `src/agent_runtime/ui_state.py`
- Modify: `src/agent_runtime/ui_console.py`
- Modify: `docs/UI_STATE_API_EXAMPLES.md`
- Modify: `docs/UI_CONSOLE_MVP.md`
- Modify: `tests/test_ui_state.py`
- Modify: `tests/test_ui_console.py`

- [ ] **Step 1: Write the failing UI state test**

Add to `tests/test_ui_state.py`:

```python
def test_ui_state_exposes_task_set_progress_and_status_text(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-progress.json",
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-progress",
                "task_id": "TASK-AR-248",
                "task_set_id": "TASKSET-AR-PROGRESS",
                "agent_role": "lead-engineer",
                "team_id": "agent-runtime-core",
                "agent_instance_id": "le-1",
                "display_name": "lead_engineer@ui-01",
                "callsite_id": "terminal:wt-task-ar-248:tab-01",
                "pane_id": "terminal:wt-task-ar-248:tab-01",
                "status": "working",
                "phase": "implement",
                "step_index": 3,
                "step_total": 6,
                "progress_pct": 48,
                "status_text": "Rendering task-set progress cards",
                "worktree_path": ".worktrees/TASK-AR-248",
                "branch": "codex/task-ar-248-ui-01",
                "claimed_at": "2026-06-10T18:00:00+09:00",
                "last_heartbeat": "2026-06-10T18:05:00+09:00",
            }
        ),
    )

    state = ui_state.build_state(tmp_path, now="2026-06-10T18:06:00+09:00")

    assert state["agents"][0]["step_index"] == 3
    assert state["agents"][0]["step_total"] == 6
    assert state["agents"][0]["status_text"] == "Rendering task-set progress cards"
    assert state["task_sets"][0]["id"] == "TASKSET-AR-PROGRESS"
    assert state["task_sets"][0]["progress_pct"] == 48
    assert state["task_sets"][0]["active"] == 1
```

- [ ] **Step 2: Run the state test to verify it fails**

Run: `PYTHONPATH=src pytest tests/test_ui_state.py::test_ui_state_exposes_task_set_progress_and_status_text -q`

Expected: FAIL because `step_index`, `step_total`, `status_text`, and `task_sets` are not exposed yet.

- [ ] **Step 3: Implement minimal state projection**

In `src/agent_runtime/ui_state.py`, extend the active claim projection with:

```python
"task_set_id": claim.get("task_set_id"),
"step_index": claim.get("step_index"),
"step_total": claim.get("step_total"),
"status_text": claim.get("status_text"),
```

Add a `build_task_sets(agents: list[dict[str, object]]) -> list[dict[str, object]]` helper that groups agents by `task_set_id`, counts `active`, `blocked`, and `done`, and averages valid numeric `progress_pct` values.

- [ ] **Step 4: Expose `task_sets` in the state object and resource API**

Add `task_sets` beside existing `agents`, `tasks`, and `messages` in `build_state`, and allow `build_resource(root, "task_sets")`.

- [ ] **Step 5: Write the failing console rendering test**

Add to `tests/test_ui_console.py`:

```python
def test_ui_console_agents_view_contains_progress_fields(tmp_path):
    _write(
        tmp_path / "agents" / "runtime" / "task_claims" / "CLAIM-progress.json",
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-progress",
                "task_id": "TASK-AR-248",
                "task_set_id": "TASKSET-AR-PROGRESS",
                "agent_role": "lead-engineer",
                "team_id": "agent-runtime-core",
                "agent_instance_id": "le-1",
                "display_name": "lead_engineer@ui-01",
                "callsite_id": "terminal:wt-task-ar-248:tab-01",
                "pane_id": "terminal:wt-task-ar-248:tab-01",
                "status": "working",
                "phase": "implement",
                "step_index": 3,
                "step_total": 6,
                "progress_pct": 48,
                "status_text": "Rendering task-set progress cards",
                "worktree_path": ".worktrees/TASK-AR-248",
                "branch": "codex/task-ar-248-ui-01",
                "claimed_at": "2026-06-10T18:00:00+09:00",
                "last_heartbeat": "2026-06-10T18:05:00+09:00",
            }
        ),
    )

    html = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    assert "status_text" in html
    assert "step_index" in html
    assert "progress_pct" in html
```

- [ ] **Step 6: Render progress in `ui_console.JS` and `ui_console.CSS`**

Add a small progress element to agent cards:

```javascript
const step = agent.step_index && agent.step_total ? `${agent.step_index}/${agent.step_total}` : "step ?";
const pct = Number.isFinite(Number(agent.progress_pct)) ? `${agent.progress_pct}%` : "~";
const statusText = agent.status_text || agent.phase || "working";
```

Render: `phase`, `step`, `pct`, `statusText`, `pane_id`, and `task_set_id`.

- [ ] **Step 7: Run focused UI tests**

Run: `PYTHONPATH=src pytest tests/test_ui_state.py tests/test_ui_console.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/agent_runtime/ui_state.py src/agent_runtime/ui_console.py tests/test_ui_state.py tests/test_ui_console.py docs/UI_STATE_API_EXAMPLES.md docs/UI_CONSOLE_MVP.md
git commit -m "feat: show pane task-set progress in ui"
```

## Task 3: TASK-AR-249 Claim Progress Enforcement

**Files:**
- Modify: `scripts/task_claim_dispatcher.py`
- Modify: `src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`
- Modify: `scripts/continuity_contract_gate.py`
- Modify: `src/agent_runtime/templates/project/scripts/continuity_contract_gate.py`
- Modify: `tests/test_task_claim_dispatcher.py`
- Modify: `tests/test_continuity_contract_gate.py`
- Modify: `agents/project/NEXT-SESSION-POINTER.yml`

- [ ] **Step 1: Write the failing dispatcher test**

Add to `tests/test_task_claim_dispatcher.py`:

```python
def test_create_claim_accepts_step_status_and_task_set(tmp_path: Path):
    (tmp_path / "STATUS.md").write_text("## Handoff Checklist\n- continue here\n", encoding="utf-8")
    result = _run_dispatcher(
        tmp_path,
        "create",
        "--task-id",
        "TASK-AR-249",
        "--agent-role",
        "lead-engineer",
        "--mode",
        "implementation",
        "--task-set-id",
        "TASKSET-AR-PROGRESS",
        "--step-index",
        "3",
        "--step-total",
        "6",
        "--status-text",
        "Updating claim progress enforcement",
        "--progress-pct",
        "48",
        "--now",
        "2026-06-10T18:20:00+09:00",
        "--suffix",
        "c9d1",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    claim = json.loads(result.stdout)["claim"]
    assert claim["task_set_id"] == "TASKSET-AR-PROGRESS"
    assert claim["step_index"] == 3
    assert claim["step_total"] == 6
    assert claim["status_text"] == "Updating claim progress enforcement"
    assert claim["updated_at"] == "2026-06-10T18:20:00+09:00"
```

- [ ] **Step 2: Run the dispatcher test to verify it fails**

Run: `PYTHONPATH=.;src pytest tests/test_task_claim_dispatcher.py::test_create_claim_accepts_step_status_and_task_set -q`

Expected: FAIL because the CLI options are not accepted yet.

- [ ] **Step 3: Add CLI options and validation**

Add arguments:

```python
create.add_argument("--task-set-id")
create.add_argument("--step-index", type=int, default=1)
create.add_argument("--step-total", type=int, default=6)
create.add_argument("--status-text", default="Claim created")
```

Validate:

```python
if args.step_index < 1 or args.step_total < 1 or args.step_index > args.step_total:
    raise SystemExit("step_index must be between 1 and step_total")
if args.progress_pct < 0 or args.progress_pct > 100:
    raise SystemExit("progress_pct must be between 0 and 100")
```

Write `task_set_id`, `step_index`, `step_total`, `status_text`, and `updated_at` into the claim JSON.

- [ ] **Step 4: Mirror the dispatcher changes into the template copy**

Apply the same option and JSON changes to `src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`.

- [ ] **Step 5: Strengthen continuity gate if needed**

If `scripts/continuity_contract_gate.py --check` does not already require live phase/progress documentation, add a finding that requires `step_index`, `step_total`, or `status_text` in the pointer or protocol docs.

- [ ] **Step 6: Run focused enforcement tests**

Run: `PYTHONPATH=.;src pytest tests/test_task_claim_dispatcher.py tests/test_continuity_contract_gate.py -q`

Expected: PASS.

- [ ] **Step 7: Run integration gates**

Run:

```bash
PYTHONPATH=.;src python scripts/continuity_contract_gate.py --check
PYTHONPATH=.;src python scripts/owner_governance_gate.py
PYTHONPATH=src pytest tests/test_pane_progress_contract.py tests/test_task_claim_dispatcher.py tests/test_ui_state.py tests/test_ui_console.py -q
```

Expected: all commands return 0.

- [ ] **Step 8: Commit**

```bash
git add scripts/task_claim_dispatcher.py src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py scripts/continuity_contract_gate.py src/agent_runtime/templates/project/scripts/continuity_contract_gate.py tests/test_task_claim_dispatcher.py tests/test_continuity_contract_gate.py agents/project/NEXT-SESSION-POINTER.yml
git commit -m "feat: enforce pane progress claims"
```

## Self-Review

- Spec coverage: The plan covers pane identity, task-set aggregation, phase/status text, rough percent, step counters, UI visibility, golden set, and enforcement.
- Placeholder scan: The plan contains no TBD, TODO, or "implement later" steps.
- Type consistency: `task_set_id`, `step_index`, `step_total`, `status_text`, `progress_pct`, `phase`, `pane_id`, and `display_name` are used consistently across tests, claim JSON, UI state, and console rendering.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-pane-progress-tasksets.md`.

Recommended execution order:

1. `TASK-AR-247`: testset contract.
2. `TASK-AR-248`: UI state and console rendering.
3. `TASK-AR-249`: claim progress enforcement and gates.
