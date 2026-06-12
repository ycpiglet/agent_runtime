---
unit_id: UNIT-TASK-AR-372-004
task_id: TASK-AR-372
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: completed
completed_at: 2026-06-12T12:58:47+09:00
verification_status: passed
horizon: unit
model_tier: worker_standard
escalation_triggers: [data_integrity, cross_cutting]
context: "Restore the root canonical timestamp generator referenced by host-project docs and expose it through the deterministic work CLI."
inputs:
  - src/agent_runtime/templates/project/scripts/now.py
  - src/agent_runtime/templates/project/AGENTS.md
  - src/agent_runtime/templates/project/CLAUDE.md
  - scripts/work.py
target_files:
  - scripts/now.py
  - scripts/work.py
  - tests/test_now.py
  - agents/lead_engineer/tasks/TASK-AR-372.md
  - reviews/REVIEW-2026-06-12-work-now-timestamp-source.md
scope: "Restore scripts/now.py and add work.py now only; do not refactor every existing timestamp caller in the repository."
acceptance:
  - "scripts/now.py exists at the root and prints local ISO, UTC Z, date-only, and epoch outputs."
  - "scripts/work.py now exposes the same output modes through the work CLI."
  - "work.py registration uses the canonical now utility for generated timestamps when no explicit --now/input now is provided."
  - "Focused tests validate timestamp formats and existing work new behavior."
verification:
  - "python -m py_compile scripts\\now.py scripts\\work.py"
  - "pytest tests/test_now.py tests/test_work_registration.py -q"
  - "python scripts/now.py --utc"
  - "python scripts/work.py now --utc"
handoff: "Report canonical timestamp command syntax and that broader timestamp caller migration remains out of scope."
stop_condition: "Stop after restoring the canonical time source and work now; do not implement work close or repo-wide timestamp refactors in this unit."
---

# UNIT-TASK-AR-372-004 - Canonical Timestamp Source And Work Now

## Context

The host-project template already references `python scripts/now.py`, and the
Claude conversation identified the missing root script as a metadata reliability
gap. Work registration and closeout tools need one deterministic timestamp
source rather than shell-specific date commands.

## Inputs

- `src/agent_runtime/templates/project/scripts/now.py`
- `src/agent_runtime/templates/project/AGENTS.md`
- `src/agent_runtime/templates/project/CLAUDE.md`
- `scripts/work.py`
- `tests/test_work_registration.py`

## Target Files

- `scripts/now.py`
- `scripts/work.py`
- `tests/test_now.py`
- `agents/lead_engineer/tasks/TASK-AR-372.md`
- `reviews/REVIEW-2026-06-12-work-now-timestamp-source.md`
- `owner-docs.yml`
- `BACKLOG-BOARD.md`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.json`
- `agents/project/work-items/WORK-ITEM-CLASSIFICATION.md`
- `reviews/INDEX.md`

## Scope

In scope: root canonical timestamp script, `work.py now` command, `work.py`
registration fallback timestamps using the canonical utility, and focused tests
for CLI output formats.

Out of scope: replacing every existing direct `datetime.now()` call, adding
closeout actuals, or implementing `work verify`.

## Steps

1. Add root `scripts/now.py` with local, UTC, date, and epoch output modes.
2. Import that module in `scripts/work.py` for generated registration
   timestamps.
3. Add `work.py now` with matching output modes.
4. Add tests that run both CLIs and validate output shapes.
5. Run existing work registration tests to prove `work new` still passes.

## Acceptance Criteria

- `python scripts/now.py` emits a local ISO timestamp with timezone offset.
- `python scripts/now.py --utc` emits a UTC timestamp with `Z`.
- `python scripts/now.py --date` emits `YYYY-MM-DD`.
- `python scripts/now.py --epoch` emits Unix epoch seconds.
- `python scripts/work.py now` supports the same output modes.
- `pytest tests/test_now.py tests/test_work_registration.py -q` passes.

## Verification

```powershell
python -m py_compile scripts\now.py scripts\work.py
pytest tests/test_now.py tests/test_work_registration.py -q
python scripts/now.py --utc
python scripts/work.py now --utc
```

## Handoff

Use `python scripts/now.py` for direct timestamp capture and
`python scripts/work.py now` when staying inside the work CLI surface. Existing
timestamp producers can migrate gradually when touched.

## Completion Evidence

- `python -m py_compile scripts\now.py scripts\work.py`
- `pytest tests/test_now.py tests/test_work_registration.py -q`
- `python scripts/now.py --utc`
- `python scripts/work.py now --utc`

## Stop Boundary

Stop after restoring the canonical timestamp source and `work now`. Continue
into `work close`, `work verify`, or repo-wide timestamp refactors only under
separate units.
