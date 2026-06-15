# Agent Org Delegation — Unit 1: Role/Team Registry + Owner Normalization Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the repo a structured role/team/tier registry (`ORG-MODEL.yml`) that absorbs the current free-text `owner` drift via aliases, plus a watch-level gate that resolves every work item's `owner`/`team` to a registered role — the foundation the Director→Lead→Worker+Reviewer org hangs on.

**Architecture:** One YAML SSOT (`agents/project/ORG-MODEL.yml`) lists tiers, teams, and roles; each role carries `aliases` so existing values (`lead_engineer`, `lead-engineer`, …) resolve to one canonical role without rewriting 189 task files. A standalone gate (`scripts/org_model_gate.py --check`) builds the alias→role map and reports unresolved owners; it is watch-level (exit 0) until `--enforce`, mirroring the schema's `unknown_field_policy: watch`. No skill_file dependency (the repo has none yet) and no mass file migration in this unit.

**Tech Stack:** Python 3.10+, PyYAML (already a dep), pytest. Spec: `docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md` (Section A + build step 1). Research: `reviews/RESEARCH-2026-06-14-agent-org-design-references.md`.

---

## File Structure

- Create `agents/project/ORG-MODEL.yml` — role/team/tier registry SSOT (the only canonical data).
- Create `scripts/org_model_gate.py` — loader + `resolve_owner()`/`resolve_team()` + `--check` CLI. One responsibility: validate owner/team against the registry.
- Create `tests/test_org_model_gate.py` — registry parse, alias resolution, unresolved detection, exit codes.
- Modify `scripts/owner_governance_gate.py` — chain `org_model_gate.py --check` at watch level (one line in the gate sequence).

---

### Task 1: ORG-MODEL.yml registry (absorbs current owner drift)

**Files:**
- Create: `agents/project/ORG-MODEL.yml`
- Test: `tests/test_org_model_gate.py` (first test only)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_org_model_gate.py
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "scripts" / "org_model_gate.py"

def _load():
    spec = importlib.util.spec_from_file_location("org_model_gate", SPEC)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def test_registry_loads_and_covers_existing_owners():
    mod = _load()
    reg = mod.load_registry()
    # every owner value currently in the repo must resolve to a canonical role
    for value in ["lead_engineer", "lead-engineer", "qa", "research-agent",
                  "managing-partner", "release-integrity"]:
        assert mod.resolve_owner(value, reg) is not None, f"{value} unresolved"
    # canonical ids are kebab-case and unique
    ids = [r["id"] for r in reg["roles"]]
    assert len(ids) == len(set(ids))
    assert all("_" not in i for i in ids)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_org_model_gate.py::test_registry_loads_and_covers_existing_owners -v`
Expected: FAIL (`org_model_gate.py` not found / `load_registry` missing).

- [ ] **Step 3: Create the registry**

```yaml
# agents/project/ORG-MODEL.yml — Role/Team/Tier registry (SSOT).
# Director -> Lead -> Worker + Reviewer, organized into functional teams.
# `aliases` absorb historical free-text owner values so no mass file rewrite is
# needed; the org_model_gate resolves any alias to the canonical kebab-case id.
schema: agent-runtime-org-model/v1
updated_at: 2026-06-15T00:00:00+09:00

# Tiers map to the work-schema *_model_tier fields (planner/worker/reviewer).
tiers: [director, planner, worker, reviewer]

teams:
  - id: org           # org-wide (no single discipline)
    display_name: Org
  - id: engineering
    display_name: Engineering
  - id: ui-ux
    display_name: UI/UX
  - id: research
    display_name: Research
  - id: quality
    display_name: Quality & Eval
  - id: risk-release
    display_name: Risk & Release

roles:
  - id: managing-partner
    tier: director
    team: org
    aliases: [mp, partner, director, ceo, managing_partner, managing-partner]
  - id: lead-engineer
    tier: planner
    team: engineering
    aliases: [lead, lead_engineer, lead-engineer, engineering, worktree-dispatcher]
  - id: worker-engineer
    tier: worker
    team: engineering
    aliases: [worker, engineer, agent-runtime, rsi-lab]
  - id: uiux
    tier: planner
    team: ui-ux
    aliases: [ui, ux, uiux, frontend, uiux-designer]
  - id: research-agent
    tier: planner
    team: research
    aliases: [research, researcher, research-agent, research_agent]
  - id: qa
    tier: reviewer
    team: quality
    aliases: [qa, quality, test, evaluation-office, evaluation_office]
  - id: independent-auditor
    tier: reviewer
    team: quality
    aliases: [audit, auditor, independent-auditor, independent_auditor]
  - id: risk-controller
    tier: reviewer
    team: risk-release
    aliases: [risk, risk-controller, risk_controller, risk-and-safety, risk_and_safety]
  - id: release-integrity
    tier: reviewer
    team: risk-release
    aliases: [release, release-integrity, release_integrity, ci-cd, cicd]
```

- [ ] **Step 4: (defer) — test needs the gate module; proceed to Task 2 then re-run.**

Note: this test depends on `org_model_gate.py` (Task 2). Run it at the end of Task 2.

---

### Task 2: org_model_gate.py (loader + resolver + --check)

**Files:**
- Create: `scripts/org_model_gate.py`
- Test: `tests/test_org_model_gate.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_org_model_gate.py
def test_resolve_owner_aliases_and_unknown():
    mod = _load(); reg = mod.load_registry()
    assert mod.resolve_owner("lead_engineer", reg)["id"] == "lead-engineer"
    assert mod.resolve_owner("lead-engineer", reg)["id"] == "lead-engineer"
    assert mod.resolve_owner("ci-cd", reg)["id"] == "release-integrity"
    assert mod.resolve_owner("totally-unknown-role", reg) is None

def test_check_reports_unresolved_but_is_watch_level(tmp_path, capsys):
    mod = _load()
    # a fake work item with an unknown owner
    f = tmp_path / "TASK-X.md"
    f.write_text("---\nowner: nope-not-a-role\nkind: task\n---\n", encoding="utf-8")
    rc = mod.cmd_check([str(f)], enforce=False)
    out = capsys.readouterr().out
    assert "nope-not-a-role" in out
    assert rc == 0          # watch-level: never blocks

def test_check_enforce_blocks_on_unresolved(tmp_path):
    mod = _load()
    f = tmp_path / "TASK-Y.md"
    f.write_text("---\nowner: nope\nkind: task\n---\n", encoding="utf-8")
    assert mod.cmd_check([str(f)], enforce=True) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_org_model_gate.py -v`
Expected: FAIL (module/functions missing).

- [ ] **Step 3: Implement the gate**

```python
# scripts/org_model_gate.py
"""Org model gate: resolve work-item owner/team against agents/project/ORG-MODEL.yml.

Watch-level by default (exit 0); `--enforce` exits 1 on any unresolved owner/team.
Aliases absorb historical free-text owner drift (lead_engineer vs lead-engineer).
Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (Sec A).
"""
from __future__ import annotations
import argparse, glob, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "agents" / "project" / "ORG-MODEL.yml"
DEFAULT_GLOB = "agents/lead_engineer/tasks/TASK-*.md"


def load_registry(path: Path = REGISTRY) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _alias_map(reg: dict) -> dict[str, dict]:
    m: dict[str, dict] = {}
    for role in reg["roles"]:
        for key in [role["id"], *role.get("aliases", [])]:
            m[key.strip().lower()] = role
    return m


def resolve_owner(value: str | None, reg: dict) -> dict | None:
    if not value:
        return None
    return _alias_map(reg).get(value.strip().lower())


def resolve_team(team_id: str | None, reg: dict) -> dict | None:
    if not team_id:
        return None
    for t in reg.get("teams", []):
        if t["id"] == team_id.strip().lower():
            return t
    return None


def _front_owner(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    fm = yaml.safe_load(text[3:end]) if end != -1 else {}
    return (fm or {}).get("owner")


def cmd_check(paths: list[str], *, enforce: bool) -> int:
    reg = load_registry()
    files: list[Path] = []
    for p in paths:
        files.extend(Path(x) for x in glob.glob(p)) if any(c in p for c in "*?") else files.append(Path(p))
    unresolved = []
    for f in files:
        if not f.exists():
            continue
        owner = _front_owner(f)
        if owner is not None and resolve_owner(owner, reg) is None:
            unresolved.append((f, owner))
    for f, owner in unresolved:
        print(f"org-model: unresolved owner '{owner}' in {f}")
    level = "block" if enforce else "watch"
    print(f"org-model: {level} unresolved={len(unresolved)} checked={len(files)}")
    return 1 if (enforce and unresolved) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--enforce", action="store_true")
    ap.add_argument("paths", nargs="*", default=[DEFAULT_GLOB])
    a = ap.parse_args(argv)
    paths = a.paths or [DEFAULT_GLOB]
    return cmd_check(paths, enforce=a.enforce)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run all Task 1+2 tests to verify pass**

Run: `python -m pytest tests/test_org_model_gate.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Run the gate against the real repo (manual smoke)**

Run: `python scripts/org_model_gate.py --check`
Expected: prints `org-model: watch unresolved=0 checked=<N>` (all current owners resolve via aliases; if any unresolved appears, add its alias to ORG-MODEL.yml and re-run).

- [ ] **Step 6: Commit**

```bash
git add agents/project/ORG-MODEL.yml scripts/org_model_gate.py tests/test_org_model_gate.py
git commit -m "feat(org): role/team/tier registry + watch-level owner-resolution gate (org-delegation Unit 1)"
```

---

### Task 3: Chain the gate into owner_governance_gate at watch level

**Files:**
- Modify: `scripts/owner_governance_gate.py` (add one entry to the gate sequence)
- Test: `tests/test_org_model_gate.py` (wiring assertion)

- [ ] **Step 1: Write the failing test**

```python
def test_governance_gate_invokes_org_model():
    text = (ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    assert "org_model_gate.py" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_org_model_gate.py::test_governance_gate_invokes_org_model -v`
Expected: FAIL.

- [ ] **Step 3: Add the gate to the sequence**

Locate the list/sequence of `--check` subprocess invocations in `scripts/owner_governance_gate.py` (search for an existing entry like `evidence_index_generator.py`). Add an entry that runs `python scripts/org_model_gate.py --check` **without** `--enforce` (watch-level: its exit 0 never blocks). Match the file's existing invocation pattern exactly (same helper/result-print convention).

- [ ] **Step 4: Run the wiring test + full governance gate**

Run: `python -m pytest tests/test_org_model_gate.py -v` → PASS (5 tests).
Run: `python scripts/owner_governance_gate.py` → exit 0; output includes an `org-model: watch unresolved=0 …` line.

- [ ] **Step 5: Commit**

```bash
git add scripts/owner_governance_gate.py tests/test_org_model_gate.py
git commit -m "feat(org): chain org_model_gate at watch level in governance gate (Unit 1)"
```

---

## Self-Review

- **Spec coverage:** implements Section A "role/team registry … ending the lead_engineer/lead-engineer drift" + build step 1 (registry + normalization gate). Owner-value rewrite is intentionally deferred (aliases absorb drift; optional `--fix` is a later unit) — noted, not a gap.
- **Placeholder scan:** none — ORG-MODEL.yml, gate, and tests are complete code. Task 3 Step 3 references the existing file's pattern rather than guessing its exact lines (the implementer matches the surrounding convention); the wiring is verified by `test_governance_gate_invokes_org_model` + a full gate run.
- **Type consistency:** `load_registry`/`resolve_owner`/`resolve_team`/`cmd_check` signatures are consistent across tasks; canonical ids are kebab-case throughout.

## Out of scope (subsequent units, each its own plan)

Unit 2 decomposition tool (Taskset→Units); Unit 3 seam+risk dispatch gate; Unit 4 orchestrator + WorkerBackend/SubagentBackend; Unit 5 deliberation/persona layer; Unit 6 org/state read-API. Optional owner-value `--fix` migration.
