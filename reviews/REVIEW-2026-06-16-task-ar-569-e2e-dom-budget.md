# TASK-AR-569 W4a Review - E2E + DOM Budget Regression

## Bottom Line

TASK-AR-569 is ready for independent W4b verification.

## Scope

- Added a server-backed E2E regression for the decision-first home budget.
- Counted initial served HTML elements and enforced the `<= 1500` DOM budget.
- Counted the decision shell before the work surface and enforced a compact `<= 320` element budget as the CI-safe guard for the 1-2 screen cockpit.
- Asserted progressive disclosure through exactly one active view plus CSS-hidden inactive views.
- Re-asserted maturity behavior preservation in the same E2E path: responsive CSS, accessibility landmarks/ARIA, SSE, KO/EN i18n, and validation signals.

## Verification

- `PYTHONPATH=src python -m pytest tests/test_ui_console_e2e.py -q` -> 13 passed.
- `PYTHONPATH=src python -m pytest tests/test_ui_console.py -q` -> 152 passed.

## Risk

- The 1-2 screen assertion is a CI-safe DOM/shell-size proxy, not a browser pixel-height measurement.
- Browser-level viewport measurement can be added later with Playwright if the suite gains that dependency.
