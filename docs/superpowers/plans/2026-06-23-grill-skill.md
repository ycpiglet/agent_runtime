# `/grill` Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conversational `/grill` skill that interviews the Owner about a program/asset they are building and drafts `BLUEPRINT.md` + `VISION-DIRECTION.md` mapped to the lane playbooks.

**Architecture:** One live-only skill (`skills/grill/SKILL.md`) runs three phases — grill (six-part discovery interview, one question at a time) → blueprint synthesis → vision/direction/methodology synthesis. Outputs are draft markdown under `agents/project/blueprints/<slug>/`. A structural pytest guards the skill's completeness and safety wiring. No new scripts/hooks; the interview is conversational.

**Tech Stack:** Markdown skill (`SKILL.md` with `name/version/description/triggers/dependencies` frontmatter), Python `pytest` (repo config: `pythonpath = [".", "src"]`, `testpaths = ["tests"]`).

## Global Constraints

- Live-only skill: do NOT mirror to `src/agent_runtime/templates/` (matches `rsi-planning-loop`/`failure-to-regression`); no host-lock regeneration.
- Draft-only, zero external effects: no external writes, no contacting customers/leads/partners, no price/contract mutation, no scraping/spam/manipulation, no auto-registering tasksets.
- Anything the Owner does not state is recorded literally as `OWNER-DECIDES`; never fabricate business facts.
- Interview asks ONE question at a time (do not batch).
- Outputs go under `agents/project/blueprints/<slug>/` (`<slug>` = kebab asset name + date).
- Delivery is collision-safe: isolated worktree off latest `main` (already created at `.worktrees/grill-skill`, branch `claude/grill-skill`), single PR, CI auto-merges on green.

---

### Task 1: Blueprints output convention + README

**Files:**
- Create: `agents/project/blueprints/README.md`
- Test: `tests/test_grill_skill.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the `agents/project/blueprints/` directory convention that `skills/grill/SKILL.md` (Task 2) writes into; the test module `tests/test_grill_skill.py` that Task 2 extends.

- [ ] **Step 1: Write the failing test**

Create `tests/test_grill_skill.py`:

```python
"""Structural guards for the /grill skill (discovery -> blueprint -> vision).

The interview itself is conversational and not unit-tested; these tests assert the
skill file stays complete (six-part frame, three phases), safe (boundary +
OWNER-DECIDES), wired to the lane playbooks, and that its output convention exists.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "grill" / "SKILL.md"
BLUEPRINTS_README = ROOT / "agents" / "project" / "blueprints" / "README.md"


def test_blueprints_dir_has_readme():
    assert BLUEPRINTS_README.exists()
    text = BLUEPRINTS_README.read_text(encoding="utf-8").lower()
    assert "draft" in text and "owner" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grill_skill.py::test_blueprints_dir_has_readme -q`
Expected: FAIL (README does not exist).

- [ ] **Step 3: Create the README**

Create `agents/project/blueprints/README.md`:

```markdown
# Blueprints

Per-situation **draft** outputs of the `/grill` skill (planning-strategy lane).

Each run creates `<slug>/` (kebab asset name + date) holding:
- `INTAKE.md` — the Owner's grilled answers,
- `BLUEPRINT.md` — a lean-canvas business plan draft,
- `VISION-DIRECTION.md` — fit vision + direction options + methodology.

These are **Owner drafts**, not commitments. Values the Owner has not decided are
marked `OWNER-DECIDES`. Nothing here triggers an external effect; the Owner approves
any direction or external action.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_grill_skill.py::test_blueprints_dir_has_readme -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_grill_skill.py agents/project/blueprints/README.md
git commit -m "feat(grill): add blueprints output convention + README"
```

---

### Task 2: `/grill` skill

**Files:**
- Create: `skills/grill/SKILL.md`
- Modify: `tests/test_grill_skill.py` (append skill structural tests)

**Interfaces:**
- Consumes: the `agents/project/blueprints/` convention from Task 1.
- Produces: the `/grill` skill (terminal capability; nothing depends on it in this slice).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grill_skill.py`:

```python
FRAME = [
    "Asset",
    "Problem & who",
    "Value & differentiation",
    "Constraints",
    "Goals",
    "Monetization hypothesis",
]
PHASES = ["Phase A", "Phase B", "Phase C"]


def test_skill_exists_with_frontmatter_name():
    assert SKILL.exists()
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: grill" in text


def test_skill_covers_six_part_frame():
    text = SKILL.read_text(encoding="utf-8")
    for item in FRAME:
        assert item in text, f"missing frame item: {item}"


def test_skill_has_three_phases():
    text = SKILL.read_text(encoding="utf-8")
    for phase in PHASES:
        assert phase in text, f"missing {phase}"


def test_skill_states_safety_and_owner_decides():
    text = SKILL.read_text(encoding="utf-8")
    assert "OWNER-DECIDES" in text
    assert "boundary" in text.lower()
    assert "draft" in text.lower()


def test_skill_links_playbooks_and_packet():
    text = SKILL.read_text(encoding="utf-8")
    assert "WORK-LANE-PLAYBOOKS.md" in text
    assert "BUSINESS-OPERATING-SYSTEM.md" in text


def test_skill_includes_artifact_templates():
    text = SKILL.read_text(encoding="utf-8")
    assert "BLUEPRINT.md" in text and "VISION-DIRECTION.md" in text
    assert "Revenue hypothesis" in text  # blueprint field
    assert "Methodology" in text  # vision-direction section
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_grill_skill.py -q`
Expected: FAIL (skill file does not exist; `test_blueprints_dir_has_readme` still passes).

- [ ] **Step 3: Write the skill**

Create `skills/grill/SKILL.md`:

````markdown
---
name: grill
version: 1.0.0
description: Use when the Owner wants to turn a program/asset they are building with agent_runtime into a tailored plan — an intensive discovery interview ("grill") that drafts a blueprint and a fit vision/direction/methodology. Planning-strategy lane entry point.
triggers:
  - grill
  - blueprint
  - business plan
  - vision
  - discovery interview
dependencies:
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
---

# Grill — Discovery → Blueprint → Vision

Interview the Owner about a program/asset they are building with agent_runtime,
then draft a blueprint and a fit vision/direction/methodology. This is the
planning-strategy lane's entry point of the Business Operating System.

## Safety boundary (read first)

This skill ELICITS the Owner's own answers and decisions; it does NOT invent
business facts. Anything the Owner does not state is recorded literally as
`OWNER-DECIDES`. All outputs are **drafts in this repo**. Inherit the
`agents/project/BUSINESS-OPERATING-SYSTEM.md` safe-effect boundary verbatim: no
external writes; no contacting customers/leads/partners; no price/contract/invoice
mutation; no scraping, spam, fake engagement, or platform manipulation. The skill
never sends, publishes, charges, or auto-registers anything — it drafts only.

## Output location

Create `agents/project/blueprints/<slug>/` where `<slug>` is the kebab-cased asset
name plus the date (for example `my-cli-tool-2026-06-23`). Write `INTAKE.md`,
`BLUEPRINT.md`, and `VISION-DIRECTION.md` there.

## Phase A — Grill (discovery)

Ask ONE question at a time (never batch). Cover this six-part frame and record each
answer to `INTAKE.md` as you go. If the Owner declines or does not know, write
`OWNER-DECIDES` for that item and move on.

1. **Asset** — What program/asset are you building with agent_runtime? What does it
   do, and what is its current state?
2. **Problem & who** — What problem does it solve, and who has that problem (target
   user/segment)?
3. **Value & differentiation** — Why is it better or different? What proof do you
   already have?
4. **Constraints** — Time, money, skills, risk tolerance: what will you and won't
   you do?
5. **Goals** — What does success look like (revenue / users / learning), and over
   what timeframe?
6. **Monetization hypothesis** — How could this make money? (your hypothesis)

When the frame is covered, write `INTAKE.md` using the template below.

## Phase B — Blueprint

Synthesize the intake into `BLUEPRINT.md` using the template below. Fill each field
from the grill; mark gaps `OWNER-DECIDES`. Do not fabricate.

## Phase C — Vision · Direction · Methodology

Write `VISION-DIRECTION.md` using the template below:
- **Vision** — one paragraph derived from the blueprint; confirm it with the Owner.
- **Direction** — 3–5 roadmap themes / next bets, presented as options for the
  Owner to choose.
- **Methodology** — map the work to lanes/cycles: reference
  `agents/project/WORK-LANE-PLAYBOOKS.md` for the per-lane procedure and
  `agents/project/BUSINESS-OPERATING-SYSTEM.md` for the cycle contract. Suggest a
  first taskset to register (suggest only; do not auto-create).

Finish by pointing the Owner to the relevant lane playbooks and the suggested first
taskset.

## Templates

### INTAKE.md

```
# Intake — <asset>

- Asset: ...
- Problem & who: ...
- Value & differentiation: ...
- Constraints: ...
- Goals: ...
- Monetization hypothesis: ...
```

### BLUEPRINT.md

```
# Blueprint — <asset>

| Field | Notes |
| --- | --- |
| Problem | ... |
| Customer | ... |
| Value proposition | ... |
| The asset | ... |
| Channels | ... |
| Revenue hypothesis | ... |
| Cost notes | ... |
| Key risks | ... |
| Open questions | OWNER-DECIDES: ... |
```

### VISION-DIRECTION.md

```
# Vision · Direction · Methodology — <asset>

## Vision
<one paragraph>

## Direction (options — Owner picks)
1. ...
2. ...
3. ...

## Methodology (lanes & cycles)
- Lane: <lane> — <what to draft> (see agents/project/WORK-LANE-PLAYBOOKS.md)
- Cycle contract: see agents/project/BUSINESS-OPERATING-SYSTEM.md
- Suggested first taskset: <name> (suggested; register via `scripts/work.py new` when the Owner approves)
```
````

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_grill_skill.py -q`
Expected: PASS (all 7 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/grill/SKILL.md tests/test_grill_skill.py
git commit -m "feat(grill): add /grill discovery->blueprint->vision skill"
```

---

### Task 3: Finalize & deliver

**Files:** none (verification + delivery only).

- [ ] **Step 1: Run the full skill test module + a sanity slice**

Run: `python -m pytest tests/test_grill_skill.py -q`
Expected: PASS (7 passed).

- [ ] **Step 2: Push the branch**

```bash
git push -u origin claude/grill-skill
```

- [ ] **Step 3: Open the PR**

```bash
gh pr create --base main --head claude/grill-skill \
  --title "feat(grill): add /grill discovery->blueprint->vision skill" \
  --body "Thin end-to-end slice of the planning-strategy lane: a conversational /grill skill that interviews the Owner and drafts BLUEPRINT.md + VISION-DIRECTION.md mapped to the lane playbooks. Live-only skill, draft-only outputs, zero external effects. Spec: docs/superpowers/specs/2026-06-23-grill-blueprint-vision-skill-design.md"
```

- [ ] **Step 4: Watch CI to green (auto-merge)**

Run: `gh pr checks <PR#> --watch --interval 30`
Expected: all `test (3.10/3.11/3.12)` pass; PR auto-merges.
