# `/enable` Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `/enable` skill that reads a `/grill` blueprint and drafts a tailored `ENABLEMENT.md` mapping the blueprint's methodology to concrete agent_runtime assets (skills/scripts/docs) with references and next actions.

**Architecture:** One live-only skill (`skills/enable/SKILL.md`). It takes a blueprint slug, reads `agents/project/blueprints/<slug>/{VISION-DIRECTION,BLUEPRINT}.md`, reads the live asset surfaces (so recommendations don't go stale), and writes `agents/project/blueprints/<slug>/ENABLEMENT.md`. A structural pytest guards completeness and safety wiring. No new scripts/hooks; synthesis is conversational.

**Tech Stack:** Markdown skill (`SKILL.md` with `name/version/description/triggers/dependencies` frontmatter), Python `pytest` (repo config: `pythonpath = [".", "src"]`, `testpaths = ["tests"]`).

## Global Constraints

- Live-only skill: do NOT mirror to `src/agent_runtime/templates/` (matches `/grill`, `rsi-planning-loop`); no host-lock regeneration.
- Draft-only, zero external effects, **zero auto-execution**: recommends assets and drafts a manual; never runs a recommended command/script or auto-registers a taskset.
- Recommend only assets that actually exist (read the live surfaces); unresolved choices are `OWNER-DECIDES`.
- Output goes to the existing `agents/project/blueprints/<slug>/` folder as `ENABLEMENT.md`.
- Delivery is collision-safe: isolated worktree off latest `main` (already created at `.worktrees/enable-skill`, branch `claude/enable-skill`), single PR, CI auto-merges on green.

---

### Task 1: `/enable` skill

**Files:**
- Create: `skills/enable/SKILL.md`
- Test: `tests/test_enable_skill.py`

**Interfaces:**
- Consumes: the `/grill` output convention `agents/project/blueprints/<slug>/{BLUEPRINT,VISION-DIRECTION}.md` (already in `main`).
- Produces: the `/enable` skill (terminal capability; nothing depends on it in this slice).

- [ ] **Step 1: Write the failing test**

Create `tests/test_enable_skill.py`:

```python
"""Structural guards for the /enable skill (per-blueprint enablement pack).

The synthesis is conversational and not unit-tested; these tests assert the skill
file stays complete (blueprint input, live asset surfaces, ENABLEMENT sections) and
safe (boundary + OWNER-DECIDES + no auto-execution).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "enable" / "SKILL.md"

ASSET_SURFACES = [
    "skills/",
    "scripts/",
    "RUNTIME-ASSET-REGISTRY.json",
    "WORK-LANE-PLAYBOOKS.md",
    "BUSINESS-OPERATING-SYSTEM.md",
]
SECTIONS = [
    "Getting started",
    "Methodology → Asset map",
    "Tailored asset index",
    "Open choices",
]


def test_skill_exists_with_frontmatter_name():
    assert SKILL.exists()
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: enable" in text


def test_skill_declares_blueprint_input():
    text = SKILL.read_text(encoding="utf-8")
    assert "blueprints/" in text
    assert "VISION-DIRECTION.md" in text


def test_skill_reads_live_asset_surfaces():
    text = SKILL.read_text(encoding="utf-8")
    for surface in ASSET_SURFACES:
        assert surface in text, f"missing asset surface: {surface}"


def test_enablement_template_has_sections():
    text = SKILL.read_text(encoding="utf-8")
    assert "ENABLEMENT.md" in text
    for section in SECTIONS:
        assert section in text, f"missing section: {section}"


def test_safety_and_no_execute():
    text = SKILL.read_text(encoding="utf-8")
    assert "OWNER-DECIDES" in text
    assert "boundary" in text.lower()
    assert "not execute" in text.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_enable_skill.py -q`
Expected: FAIL (skill file does not exist).

- [ ] **Step 3: Write the skill**

Create `skills/enable/SKILL.md`:

````markdown
---
name: enable
version: 1.0.0
description: Use when the Owner wants the enablement pack for a program they planned with /grill — reads a blueprint and drafts ENABLEMENT.md mapping the methodology to concrete agent_runtime assets (skills/scripts/docs) with references and next actions. Planning-strategy lane, slice D.
triggers:
  - enable
  - enablement
  - how to apply
  - asset pack
  - operator manual
dependencies:
  - agents/project/blueprints/README.md
  - agents/project/WORK-LANE-PLAYBOOKS.md
  - agents/project/BUSINESS-OPERATING-SYSTEM.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
---

# Enable — per-blueprint enablement pack

Turn a `/grill` blueprint into a tailored "how to apply your program" manual:
`ENABLEMENT.md`, mapping the blueprint's methodology to concrete agent_runtime
assets (skills, scripts, docs) with references and next actions. Slice D of the
Business Operating System; runs after `/grill`, or on any existing blueprint.

## Safety boundary (read first)

This skill RECOMMENDS assets and DRAFTS a manual. It does NOT execute any
recommended command, run any script, or auto-register a taskset — the Owner does
that. It recommends only assets that actually exist (see "Read live assets").
Unresolved choices are recorded as `OWNER-DECIDES`. Inherit the
`agents/project/BUSINESS-OPERATING-SYSTEM.md` safe-effect boundary verbatim: no
external writes; no contacting customers/leads/partners; no price/contract/invoice
mutation; no scraping, spam, fake engagement, or platform manipulation. Outputs are
**drafts in this repo**.

## Input

Take a blueprint slug. Read `agents/project/blueprints/<slug>/VISION-DIRECTION.md`
(its **Methodology** section) and `BLUEPRINT.md` for context. If the slug or those
files are missing, say so and stop — never fabricate a blueprint (run `/grill`
first to create one).

## Read live assets (no hardcoding)

Before mapping, read the live asset surfaces so recommendations never go stale, and
recommend ONLY assets found there:
- `skills/` — available skills.
- key `scripts/` — for example `scripts/work.py` (register work) and
  `scripts/taskset_dispatcher.py` (plan/start tasksets).
- `agents/project/WORK-LANE-PLAYBOOKS.md` and
  `agents/project/BUSINESS-OPERATING-SYSTEM.md` — lane procedure + cycle contract.
- `agents/project/RUNTIME-ASSET-REGISTRY.json` — the asset registry.

## Output — ENABLEMENT.md

Write `agents/project/blueprints/<slug>/ENABLEMENT.md` using the template below. For
each methodology step/lane in `VISION-DIRECTION.md`, recommend the concrete asset(s)
to use, the reference to read, and the next action. Finish by pointing the Owner at
the Getting-started sequence. Do NOT run any recommended command.

### ENABLEMENT.md template

```
# Enablement — <asset>

## Getting started
1. ...
2. ...

## Methodology → Asset map
| Step / lane | Platform asset(s) | Reference | Next action |
| --- | --- | --- | --- |
| ... | skill/script/doc | path | command or step (do not run it) |

## Tailored asset index
- `<asset>` — when to use it for this program.

## Open choices
- OWNER-DECIDES: ...
```
````

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_enable_skill.py -q`
Expected: PASS (all 5 tests).

- [ ] **Step 5: Commit**

```bash
git add skills/enable/SKILL.md tests/test_enable_skill.py
git commit -m "feat(enable): add /enable per-blueprint enablement pack skill"
```

---

### Task 2: Finalize & deliver

**Files:** none (verification + delivery only).

- [ ] **Step 1: Run the skill test module**

Run: `python -m pytest tests/test_enable_skill.py -q`
Expected: PASS (5 passed).

- [ ] **Step 2: Push the branch**

```bash
git push -u origin claude/enable-skill
```

- [ ] **Step 3: Open the PR**

```bash
gh pr create --base main --head claude/enable-skill \
  --title "feat(enable): /enable per-blueprint enablement pack (slice D)" \
  --body "Slice D of the Business Operating System: an /enable skill that reads a /grill blueprint and drafts ENABLEMENT.md mapping the methodology to concrete agent_runtime assets (skills/scripts/docs) with references and next actions. Live-only skill, draft-only, zero external effects, zero auto-execution. Spec: docs/superpowers/specs/2026-06-24-enable-skill-design.md"
```

- [ ] **Step 4: Watch CI to green (auto-merge)**

Run: `gh pr checks <PR#> --watch --interval 30`
Expected: all `test (3.10/3.11/3.12)` pass; PR auto-merges.
