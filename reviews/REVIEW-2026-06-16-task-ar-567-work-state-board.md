# TASK-AR-567 W4a Review - Work State Board

## Bottom Line

TASK-AR-567 is ready for independent W4b verification.

## Scope

- Added a `work_state` UI state resource backed by `scripts/org_read_api.py::work_state`.
- Added `/api/work_state` and `/api/work-state` console API routes.
- Added the Home `Work state` secondary hero with compact taskset counts and per-card unit drill-down.
- Added route, UI contract, and live-console smoke tests.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 151 passed.
- `PYTHONPATH=src python -m pytest tests/test_org_read_api.py -q` -> 3 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 11 passed.

## Risk

- The resource intentionally reuses `scripts/org_read_api.py::work_state`; changes to that script's bucket vocabulary will be reflected in this board.
- The Home hero shows up to six tasksets and each card shows up to twelve units to preserve progressive disclosure and DOM budget headroom.
