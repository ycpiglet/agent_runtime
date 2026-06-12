---
title: Work Schema SSoT Gate Closeout
date: 2026-06-12
signal: pass
score: 95
tags: [work-schema, metadata, task-ar-372, work-item, governance]
---

# Work Schema SSoT Gate Closeout

## Bottom Line

`UNIT-TASK-AR-372-001` is complete: the repository now has a deterministic
`WORK-SCHEMA.yml` field dictionary and an executable gate wired into Owner
governance.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Field dictionary | pass | `agents/project/WORK-SCHEMA.yml` covers work kinds, core fields, provenance, closure, measurement, relationship, governance, search, and attribution fields |
| Gate behavior | pass | `scripts/work_schema_gate.py --check` returns findings=0 |
| Regression tests | pass | `pytest tests/test_work_schema_gate.py tests/test_task_unit_readiness_gate.py -q` returns 6 passed |
| Governance | pass | `python scripts/owner_governance_gate.py` runs `work_schema_gate.py --check` and exits 0 |
| Full suite | pass | `pytest tests -q` returns 435 passed |

## Decision

Keep the schema as a field dictionary SSoT before implementing the broader
registration CLI/API. New metadata fields should be registered in
`WORK-SCHEMA.yml` with producer and consumer intent before a generator, gate, UI,
or stats command depends on them.

## Action Board

| Item | Status | Owner | Next Evidence |
| --- | --- | --- | --- |
| `UNIT-TASK-AR-372-001` | done | lead-engineer | schema gate and tests |
| `TASK-AR-372` registration CLI/API | open | planning-office | next unit for structured input and `work new` behavior |
| AI planner tools `split/criteria/assign` | deferred | planner | separate B-mode proposal-gated task/unit |

## Risks / Blockers

- The schema gate validates the catalog contract, not real frontmatter
  enforcement yet.
- `TASK-AR-372` remains open because full structured registration CLI/API
  behavior is still out of scope for this unit.
- Agent identity spawn records and attribution gates are still future work.

## Next

- Add the next `TASK-AR-372` unit for the deterministic `work new` or structured
  registration input path.
- Make that command consume `WORK-SCHEMA.yml` instead of hard-coding field names
  in multiple tools.
- Keep AI-generated `split`, `criteria`, and `assign` behavior behind B-mode
  proposal approval.
