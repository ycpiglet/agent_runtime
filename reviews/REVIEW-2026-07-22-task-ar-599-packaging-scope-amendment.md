---
title: TASK-AR-599 Packaging Scope Amendment
date: 2026-07-22
signal: pass
score: 96
tags: [task-ar-599, packaging, scope-amendment]
---

# TASK-AR-599 packaging scope amendment

## Bottom Line

Add `pyproject.toml` to the declared TASK-AR-599 footprint so the new template
`.env.example` is actually included in built wheels.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Template source | pass | `.env.example` exists in the claimed worktree |
| Wheel contents | block before amendment | dot-file verifier listed five files and omitted `.env.example` |
| Required repair | scoped | one explicit package-data entry in `pyproject.toml` |

## Decision

Amend the unit and active claim target lists to include `pyproject.toml`. This
is a packaging completion requirement for the already-approved template
configuration surface, not a new product capability.

## Action Board

| Action | Owner | Status |
| --- | --- | --- |
| Amend unit and claim footprint | lead-engineer | approved |
| Add explicit package-data entry | worker | pending |
| Rebuild wheel and assert `.env.example` | worker | pending |

## Risks / Blockers

- Without the amendment, generated source contains the example but installed
  hosts cannot receive it, making the documented blank-default contract false.
- No other packaging or dependency changes are authorized.

## Next

- Apply the single package-data entry in the claimed worktree.
- Rerun focused tests, wheel inspection, lock regeneration, and W4 verification.
